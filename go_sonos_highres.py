"""
This file is for use with the Pimoroni HyperPixel 4.0 Square (Non Touch) High Res display
it integrates with your local Sonos sytem to display what is currently playing
"""
import asyncio
import logging
import os
import re
import signal
import subprocess
import sys
import time
from io import BytesIO

from aiohttp import ClientError, ClientSession
from PIL import Image, ImageFile

import async_demaster
from display_controller import DisplayController, SonosDisplaySetupError
from sonos_user_data import SonosData
from webhook_handler import SonosWebhook

_LOGGER = logging.getLogger(__name__)

try:
    import sonos_settings
except ImportError:
    _LOGGER.error("ERROR: Config file not found. Copy 'sonos_settings.py.example' to 'sonos_settings.py' before you edit. You can do this with the command: cp sonos_settings.py.example sonos_settings.py")
    sys.exit(1)

show_spotify_code = getattr(sonos_settings, "show_spotify_code", None)
show_spotify_albumart = getattr(sonos_settings, "show_spotify_albumart", None)

if show_spotify_code or show_spotify_albumart:
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        spotify_import_success = True
    except ImportError:
        _LOGGER.error("ERROR: spotipy not found. Install spotipy with the command: pip install spotipy")
        sys.exit(1)

###############################################################################
# Global variables and setup
POLLING_INTERVAL = 1
WEBHOOK_INTERVAL = 60

ImageFile.LOAD_TRUNCATED_IMAGES = True

###############################################################################
# Functions

async def get_image_data(session, url):
    """Return image data from a URL if available."""
    if not url:
        return None

    try:
        async with session.get(url) as response:
            content_type = response.headers.get('content-type')
            if content_type and not content_type.startswith('image/'):
                _LOGGER.warning(
                    "Not a valid image type (%s): %s", content_type, url)
                return None
            return await response.read()
    except ClientError as err:
        _LOGGER.warning("Problem connecting to %s [%s]", url, err)
    except Exception as err:
        _LOGGER.warning("Image failed to load: %s [%s]", url, err)
    return None


async def redraw(session, sonos_data, display):
    """Redraw the screen with current data."""
    if sonos_data.status == "API error":
        return

    pil_image = None
    code_image = None
    spotify_code_uri = None
    spotify_albumart_uri = None
    spotify_client_id = None
    spotify_client_secret = None
    spotify_auth_success = False 

    def should_sleep():
        """Determine if screen should be sleeping."""
        if sonos_data.type == "line_in":
            return getattr(sonos_settings, "sleep_on_linein", False)
        if sonos_data.type == "TV":
            return getattr(sonos_settings, "sleep_on_tv", False)
        if sonos_data.type == "Bluetooth":
            return getattr(sonos_settings, "sleep_on_bluetooth", False)

    if should_sleep():
        if display.is_showing:
            _LOGGER.debug("Input source is %s, sleeping", sonos_data.type)
            display.hide_album()
        return

    # see if something is playing
    if sonos_data.status == "PLAYING":
        new_track_info = sonos_data.is_track_new()
        force_update = False

        if not new_track_info:
            # Ensure the album frame is displayed in case the current track was paused, seeked, etc
            if not display.is_showing:
                _LOGGER.debug("Waking up display...")
                force_update = True
                display.show_album()

        # slim down the album and track names
        if sonos_settings.demaster and sonos_data.type not in ("line_in", "TV", "Bluetooth"):
            offline = not getattr(
                sonos_settings, "demaster_query_cloud", False)
            sonos_data.trackname = await async_demaster.strip_name(sonos_data.trackname, session, offline)
            sonos_data.album = await async_demaster.strip_name(sonos_data.album, session, offline)

        if new_track_info or force_update:
            _LOGGER.debug("The new_track_info state is %s and force_update state is %s, resetting display with new information", new_track_info, force_update)

            if sonos_data.artist != "" and sonos_data.trackname !="":
                if show_spotify_code or show_spotify_albumart:
                    spotify_client_id = getattr(sonos_settings, "spotify_client_id", None)
                    spotify_client_secret = getattr(sonos_settings, "spotify_client_secret", None)

                    if spotify_client_id and spotify_client_secret:
                        client_credentials_manager = SpotifyClientCredentials(spotify_client_id, spotify_client_secret)
                        try:
                            spotify_auth_success = True
                            spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
                            _LOGGER.debug("Authorising Spotify developer account successful")
                        except:
                            spotify_auth_success = False
                            _LOGGER.warning("Problem authorising Spotify developer account, please check your credentials in sonos_settings.py are correct")
                    else:
                        spotify_auth_success = False

                if spotify_client_id and spotify_client_secret:
                    if show_spotify_code or show_spotify_albumart and spotify_auth_success:
                        spotify_code_path = "https://scannables.scdn.co/uri/plain/png/368A7D/white/320/"

                        try:
                            results = spotify.search(q="artist:" + re.sub("´|`|'|’", "", sonos_data.artist) + " track:" + re.sub("´|`|'|’", "", sonos_data.trackname), type="track", limit=1, market=sonos_settings.spotify_market)

                            if results['tracks']['total'] != 0:
                                results = results['tracks']['items'][0]  # Find top result
                                uri = results['uri']
                                spotify_albumart_uri = results['album']['images'][0]['url']
                                _LOGGER.debug("Spotify album art URI successfully obtained: %s", spotify_albumart_uri)
                                if sonos_data.uri.startswith('x-sonos-spotify:'):
                                    spotify_code_uri = sonos_data.uri.replace('x-sonos-spotify:', '')
                                else:                            
                                    spotify_code_uri = uri
                                _LOGGER.debug("Spotify Code URI successfully obtained: %s", spotify_code_uri)
                            else:
                                spotify_code_uri = None
                                spotify_albumart_uri = None
                        except:
                            spotify_code_uri = None
                            spotify_albumart_uri = None
                            _LOGGER.warning("Problem searching Spotify, defaulting to Sonos system")

                        if spotify_code_uri != None:
                            spotify_code_url = "".join(filter(None, [spotify_code_path, spotify_code_uri]))
                        else:
                            spotify_code_url = None

                        if spotify_code_url != None:
                            code_data = await get_image_data(session, spotify_code_url)
                            if code_data:
                                code_image = Image.open(BytesIO(code_data))
                            else:
                                code_image = None
                        else:
                            code_image = None

                        if code_image == None:
                                _LOGGER.info("Spotify Code not available")
                        if spotify_albumart_uri == None:
                                _LOGGER.info("Spotify album art not available")
                    else:
                        code_image = None
                else:
                    if show_spotify_code or show_spotify_albumart:
                        _LOGGER.warning("No Spotify API client ID or Secret in settings file, cannot search the Spotify API")
            else:
                _LOGGER.debug("Either artist and/or trackname was blank, skipped searching Spotify")

            if show_spotify_albumart and spotify_auth_success and spotify_albumart_uri != None:
                image_data = await get_image_data(session, spotify_albumart_uri)
            else:
                image_data = await get_image_data(session, sonos_data.image_uri)
            
            if image_data:
                pil_image = Image.open(BytesIO(image_data))
            elif sonos_data.type == "line_in":
                pil_image = Image.open(sys.path[0] + "/line_in.png")
            elif sonos_data.type == "TV":
                pil_image = Image.open(sys.path[0] + "/tv.png")
            elif sonos_data.type == "Bluetooth":
                pil_image = Image.open(sys.path[0] + "/bluetooth.png")

            if pil_image is None:
                if show_spotify_code or show_spotify_albumart:
                    pil_image = Image.open(sys.path[0] + "/spotify_sonos.png")
                else:
                    pil_image = Image.open(sys.path[0] + "/sonos.png")
                _LOGGER.warning("Image not available, using default")

            display.update(code_image, pil_image, sonos_data)
        else:
            _LOGGER.debug("The new_track_info state is %s, no action taken", new_track_info)
    else:
        display.hide_album()


def log_git_hash():
    """Log the current git hash for troubleshooting purposes."""
    try:
        git_hash = subprocess.check_output(
            ["git", "describe"], cwd=sys.path[0], text=True).strip()
    except (OSError, subprocess.CalledProcessError) as err:
        _LOGGER.debug("Error getting current version: %s", err)
    else:
        _LOGGER.info("Current script version: %s", git_hash)


def setup_logging():
    """Set up logging facilities for the script."""
    log_level = getattr(sonos_settings, "log_level", logging.INFO)
    log_file = getattr(sonos_settings, "log_file", None)
    if log_file:
        log_path = os.path.expanduser(log_file)
    else:
        log_path = None

    fmt = "%(asctime)s %(levelname)7s - %(message)s"
    logging.basicConfig(format=fmt, level=log_level)

    # Suppress overly verbose logs from libraries that aren't helpful
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

    if log_path is None:
        return

    log_path_exists = os.path.isfile(log_path)
    log_dir = os.path.dirname(log_path)

    if (log_path_exists and os.access(log_path, os.W_OK)) or (
        not log_path_exists and os.access(log_dir, os.W_OK)
    ):
        _LOGGER.info("Writing to log file: %s", log_path)
        logfile_handler = logging.FileHandler(log_path, mode="a")

        logfile_handler.setLevel(log_level)
        logfile_handler.setFormatter(logging.Formatter(fmt))

        logger = logging.getLogger("")
        logger.addHandler(logfile_handler)
    else:
        _LOGGER.error(
            "Cannot write to %s, check permissions and ensure directory exists", log_path)


async def main(loop):
    """Main process for script."""
    setup_logging()
    log_git_hash()
    show_details_timeout = getattr(
        sonos_settings, "show_details_timeout", None)
    overlay_text = getattr(sonos_settings, "overlay_text", None)
    show_play_state = getattr(sonos_settings, "show_play_state", None)
    

    try:
        display = DisplayController(loop, sonos_settings.show_details, sonos_settings.show_artist_and_album,
                                    show_details_timeout, overlay_text, show_play_state, show_spotify_code)
    except SonosDisplaySetupError:
        loop.stop()
        return

    if sonos_settings.room_name_for_highres == "":
        print("No room name found in sonos_settings.py")
        print("You can specify a room name manually below")
        print("Note: manual entry works for testing purposes, but if you want this to run automatically on startup then you should specify a room name in sonos_settings.py")
        print("You can edit the file with the command: nano sonos_settings.py")
        print("")
        sonos_room = input("Enter a Sonos room name for testing purposes>>>  ")
    else:
        sonos_room = sonos_settings.room_name_for_highres
        _LOGGER.info("Monitoring room: %s", sonos_room)

    session = ClientSession()
    sonos_data = SonosData(
        sonos_settings.sonos_http_api_address,
        sonos_settings.sonos_http_api_port,
        sonos_room,
        session,
    )

    async def webhook_callback():
        """Callback to trigger after webhook is processed."""
        await redraw(session, sonos_data, display)

    webhook = SonosWebhook(display, sonos_data, webhook_callback)
    await webhook.listen()

    for signame in ('SIGINT', 'SIGTERM', 'SIGQUIT'):
        loop.add_signal_handler(getattr(signal, signame), lambda: asyncio.ensure_future(
            cleanup(loop, session, webhook, display)))

    while True:
        if sonos_data.webhook_active:
            update_interval = WEBHOOK_INTERVAL
        else:
            update_interval = POLLING_INTERVAL

        if time.time() - sonos_data.last_update > update_interval:
            await sonos_data.refresh()
            await redraw(session, sonos_data, display)
        await asyncio.sleep(1)


async def cleanup(loop, session, webhook, display):
    """Cleanup tasks on shutdown."""
    _LOGGER.debug("Shutting down")
    display.cleanup()
    await session.close()
    await webhook.stop()

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(main(loop))
        loop.run_forever()
    finally:
        loop.close()

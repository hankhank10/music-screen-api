"""
This file is for use with the Pimoroni HyperPixel 4.0 Square (Non Touch) High Res display
it integrates with your local Sonos sytem to display what is currently playing
"""
import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from io import BytesIO

from aiohttp import ClientError, ClientSession
from PIL import Image, ImageFile

import demaster
import scrap
from display_controller import DisplayController
from sonos_user_data import SonosData
from webhook_handler import SonosWebhook

_LOGGER = logging.getLogger(__name__)

try:
    import sonos_settings
except ImportError:
    _LOGGER.error("ERROR: Config file not found. Copy 'sonos_settings.py.example' to 'sonos_settings.py' before you edit. You can do this with the command: cp sonos_settings.py.example sonos_settings.py")
    sys.exit(1)


## Remote debug mode - only activate if you are experiencing issues and want the developer to help
remote_debug_key = ""
if remote_debug_key != "":
    print ("Remote debugging being set up - waiting 10 seconds for wifi to get working")
    time.sleep(10)
    scrap.setup (remote_debug_key)
    scrap.auto_scrap_on_print()
    scrap.auto_scrap_on_error()
    scrap.new_section()
    scrap.write ("App start")

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
                _LOGGER.warning("Not a valid image type (%s): %s", content_type, url)
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
        if remote_debug_key != "": print ("API error reported fyi")
        return

    pil_image = None

    def should_sleep():
        """Determine if screen should be sleeping."""
        if sonos_data.type == "line_in":
            return getattr(sonos_settings, "sleep_on_linein", False)
        if sonos_data.type == "TV":
            return getattr(sonos_settings, "sleep_on_tv", False)

    if should_sleep():
        if display.is_showing:
            _LOGGER.debug("Input source is %s, sleeping", sonos_data.type)
            display.hide_album()
        return

    # see if something is playing
    if sonos_data.status == "PLAYING":
        if remote_debug_key != "": print ("Music playing")

        if not sonos_data.is_track_new():
            # Ensure the album frame is displayed in case the current track was paused, seeked, etc
            if not display.is_showing:
                display.show_album()
            return

        # slim down the trackname
        if sonos_settings.demaster and sonos_data.type not in ["line_in", "TV"]:
            offline = not getattr(sonos_settings, "demaster_query_cloud", False)
            sonos_data.trackname = demaster.strip_name(sonos_data.trackname, offline)
            if remote_debug_key != "": print ("Demastered to " + sonos_data.trackname)
            _LOGGER.debug("Demastered to %s", sonos_data.trackname)

        image_data = await get_image_data(session, sonos_data.image_uri)
        if image_data:
            pil_image = Image.open(BytesIO(image_data))
        elif sonos_data.type == "line_in":
            pil_image = Image.open(sys.path[0] + "/line_in.png")
        elif sonos_data.type == "TV":
            pil_image = Image.open(sys.path[0] + "/tv.png")

        if pil_image is None:
            pil_image = Image.open(sys.path[0] + "/sonos.png")
            _LOGGER.warning("Image not available, using default")

        display.update(pil_image, sonos_data)
    else:
        display.hide_album()
        if remote_debug_key != "": print ("Track not playing - doing nothing")

def log_git_hash():
    """Log the current git hash for troubleshooting purposes."""
    try:
        git_hash = subprocess.check_output(["git", "describe"], text=True).strip()
    except OSError as err:
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
        _LOGGER.error("Cannot write to %s, check permissions and ensure directory exists", log_path)

async def main(loop):
    """Main process for script."""
    setup_logging()
    log_git_hash()
    show_details_timeout = getattr(sonos_settings, "show_details_timeout", None)
    display = DisplayController(loop, sonos_settings.show_details, sonos_settings.show_artist_and_album, show_details_timeout)

    if sonos_settings.room_name_for_highres == "":
        print ("No room name found in sonos_settings.py")
        print ("You can specify a room name manually below")
        print ("Note: manual entry works for testing purposes, but if you want this to run automatically on startup then you should specify a room name in sonos_settings.py")
        print ("You can edit the file with the command: nano sonos_settings.py")
        print ("")
        sonos_room = input ("Enter a Sonos room name for testing purposes>>>  ")
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
        loop.add_signal_handler(getattr(signal, signame), lambda: asyncio.ensure_future(cleanup(loop, session, webhook, display)))

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

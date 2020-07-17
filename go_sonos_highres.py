"""
This file is for use with the Pimoroni HyperPixel 4.0 Square (Non Touch) High Res display
it integrates with your local Sonos sytem to display what is currently playing
"""

import asyncio
import logging
import os
import signal
import sys
import time
import tkinter as tk
from io import BytesIO
from tkinter import font as tkFont

from aiohttp import ClientSession
from PIL import Image, ImageFile, ImageTk

import demaster
import scrap
from sonos_user_data import SonosData
from webhook_handler import SonosWebhook

_LOGGER = logging.getLogger(__name__)

try:
    import sonos_settings
except ImportError:
    _LOGGER.error("ERROR: Config file not found. Copy 'sonos_config.py.example' to 'sonos_config.py' and edit.")
    sys.exit(1)

try:
    from rpi_backlight import Backlight
except ImportError:
    backlight = None
else:
    backlight = Backlight()


class TkData():

    def __init__(self, root, album_frame, curtain_frame, detail_text, label_albumart, track_name):
        """Initialize the object."""
        self.root = root
        self.album_frame = album_frame
        self.curtain_frame = curtain_frame
        self.detail_text = detail_text
        self.label_albumart = label_albumart
        self.track_name = track_name
        self.is_showing = False

    def show_album(self, should_show):
        """Control if album art should be displayed or hidden."""
        if should_show != self.is_showing:
            if should_show:
                self.album_frame.tkraise()
            else:
                self.curtain_frame.tkraise()
            self.is_showing = should_show
        set_backlight_power(should_show)


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
# Parameters and global variables

# set user variables
thumbsize = 600,600   # pixel size of thumbnail if you're displaying detail
screensize = 720,720  # pixel size of HyperPixel 4.0
fullscreen = True
thumbwidth = thumbsize[1]
screenwidth = screensize[1]

POLLING_INTERVAL = 1
WEBHOOK_INTERVAL = 60

ImageFile.LOAD_TRUNCATED_IMAGES = True

###############################################################################
# Functions

def set_backlight_power(new_state):
    """Control the backlight power of the HyperPixel display."""
    global backlight
    if backlight:
        if new_state is False and backlight.power:
            _LOGGER.debug("Going idle, turning backlight off")
            if remote_debug_key != "": print("Going idle, turning backlight off")
        try:
            backlight.power = new_state
        except PermissionError:
            _LOGGER.error("Backlight control failed, ensure permissions are correct: https://github.com/linusg/rpi-backlight#installation")
            backlight = None

async def redraw(session, sonos_data, tk_data):
    """Redraw the screen with current data."""
    if sonos_data.status == "API error":
        if remote_debug_key != "": print ("API error reported fyi")
        return

    current_artist = sonos_data.artist
    current_album = sonos_data.album
    current_duration = sonos_data.duration
    current_image_url = sonos_data.image
    current_trackname = sonos_data.trackname

    # see if something is playing
    if sonos_data.status == "PLAYING":
        if remote_debug_key != "": print ("Music playing")

        if not sonos_data.is_track_new():
            # Ensure the album frame is displayed in case the current track was paused, seeked, etc
            tk_data.show_album(True)
            return

        # slim down the trackname
        if sonos_settings.demaster:
            current_trackname = demaster.strip_name (current_trackname)
            if remote_debug_key != "": print ("Demastered to " + current_trackname)
            _LOGGER.debug("Demastered to %s", current_trackname)

        if current_image_url:
            try:
                async with session.get(current_image_url) as response:
                    image_url_response = await response.read()
                pil_image = Image.open(BytesIO(image_url_response))
            except:
                pil_image = Image.open (sys.path[0] + "/sonos.png")
                target_image_width = 500
                _LOGGER.warning("Image failed to load: %s", current_image_url)
        else:
            pil_image = Image.open(sys.path[0] + "/sonos.png")
            target_image_width = 500
            _LOGGER.warning("Image URL not available, using default")

        # set the image size and text based on whether we are showing track details as well
        if sonos_settings.show_details == True:
            target_image_width = thumbwidth
            tk_data.track_name.set(current_trackname)
            detail_text = f"{current_artist} • {current_album}"
            tk_data.detail_text.set(detail_text)
        else:
            target_image_width = screenwidth

        # resize the image
        wpercent = (target_image_width/float(pil_image.size[0]))
        hsize = int((float(pil_image.size[1])*float(wpercent)))
        pil_image = pil_image.resize((target_image_width,hsize), Image.ANTIALIAS)

        tk_image = ImageTk.PhotoImage(pil_image)
        tk_data.label_albumart.configure (image = tk_image)
        tk_data.show_album(True)
    else:
        tk_data.show_album(False)
        if remote_debug_key != "": print ("Track not playing - doing nothing")

    tk_data.root.update()


# Create the main window
root = tk.Tk()
root.geometry("720x720")
root.title("Music Display")

album_frame = tk.Frame(root, bg='black', width=720, height=720)
curtain_frame = tk.Frame(root, bg='black', width=720, height=720)

album_frame.grid(row=0, column=0, sticky="news")
curtain_frame.grid(row=0, column=0, sticky="news")

# Set variables
track_name = tk.StringVar()
detail_text = tk.StringVar()
if sonos_settings.show_artist_and_album:
    track_font = tkFont.Font(family='Helvetica', size=30)
else:
    track_font = tkFont.Font(family='Helvetica', size=40)
image_font = tkFont.Font(size=25)
detail_font = tkFont.Font(family='Helvetica', size=15)

# Create widgets
label_albumart = tk.Label(album_frame,
                        image=None,
                        font=image_font,
                        borderwidth=0,
                        highlightthickness=0,
                        fg='white',
                        bg='black')
label_track = tk.Label(album_frame,
                        textvariable=track_name,
                        font=track_font,
                        fg='white',
                        bg='black',
                        wraplength=600,
                        justify="center")
label_detail = tk.Label(album_frame,
                        textvariable=detail_text,
                        font=detail_font,
                        fg='white',
                        bg='black',
                        wraplength=600,
                        justify="center")


if sonos_settings.show_details == False:
    label_albumart.place (relx=0.5, rely=0.5, anchor=tk.CENTER)

if sonos_settings.show_details == True:
    label_albumart.place(x=360, y=thumbsize[1]/2, anchor=tk.CENTER)
    label_track.place (x=360, y=thumbsize[1]+20, anchor=tk.N)

    label_track.update()
    height_of_track_label = label_track.winfo_reqheight()

    if sonos_settings.show_artist_and_album:
        label_detail.place (x=360, y=710, anchor=tk.S)

album_frame.grid_propagate(False)

# Start in fullscreen mode
root.attributes('-fullscreen', fullscreen)
root.update()

tk_data = TkData(root, album_frame, curtain_frame, detail_text, label_albumart, track_name)

def setup_logging():
    """Set up logging facilities for the script."""
    log_level = getattr(sonos_settings, "log_level", logging.DEBUG)
    log_file = getattr(sonos_settings, "log_file", None)
    if log_file:
        log_path = os.path.expanduser(log_file)
    else:
        log_path = None

    fmt = "%(asctime)s %(levelname)7s - %(message)s"
    logging.basicConfig(format=fmt, level=log_level)

    # Suppress overly verbose logs from libraries that aren't helpful
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)

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

    if backlight is None:
        _LOGGER.error("Backlight control not available, please install the 'rpi_backlight' Python package: https://github.com/linusg/rpi-backlight#installation")

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
        await redraw(session, sonos_data, tk_data)

    webhook = SonosWebhook(sonos_data, webhook_callback)
    await webhook.listen()

    for signame in ('SIGINT', 'SIGTERM', 'SIGQUIT'):
        loop.add_signal_handler(getattr(signal, signame), lambda: asyncio.ensure_future(cleanup(loop, session, webhook)))

    while True:
        if sonos_data.webhook_active:
            update_interval = WEBHOOK_INTERVAL
        else:
            update_interval = POLLING_INTERVAL

        if time.time() - sonos_data.last_update > update_interval:
            await sonos_data.refresh()
            await redraw(session, sonos_data, tk_data)
        await asyncio.sleep(1)

async def cleanup(loop, session, webhook):
    """Cleanup tasks on shutdown."""
    _LOGGER.debug("Shutting down")
    set_backlight_power(True)
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

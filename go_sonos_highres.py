# This file is for use with the Pimoroni HyperPixel 4.0 Square (Non Touch) High Res display
# it integrates with your local Sonos sytem to display what is currently playing

from aiohttp import ClientSession, web
import asyncio
import signal

import tkinter as tk
import tkinter.font as tkFont
import time
import sys
from sonos_user_data import SonosData
import sonos_settings
from io import BytesIO
from PIL import ImageTk, Image, ImageFile
import demaster
import scrap

try:
    from rpi_backlight import Backlight
except ImportError:
    print ("Backlight control not available, please install the 'rpi_backlight' Python package: https://github.com/linusg/rpi-backlight#installation")
    backlight = None
else:
    backlight = Backlight()


class TkData():

    def __init__(self, root, detail_text, label_albumart, track_name):
        self.root = root
        self.detail_text = detail_text
        self.label_albumart = label_albumart
        self.track_name = track_name


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

# Declare global variables (don't mess with these)
last_update_timestamp = 0
previous_track = None
thumbwidth = thumbsize[1]
screenwidth = screensize[1]

ImageFile.LOAD_TRUNCATED_IMAGES = True

###############################################################################
# Functions

def set_backlight_power(new_state):
    """Control the backlight power of the HyperPixel display."""
    global backlight
    if backlight:
        if new_state is False and backlight.power:
            if remote_debug_key != "": print("Going idle, turning backlight off")
        try:
            backlight.power = new_state
        except PermissionError:
            print("Backlight control failed, ensure permissions are correct: https://github.com/linusg/rpi-backlight#installation")
            backlight = None

# Read values from the sensors at regular intervals
async def update(session, sonos_data, tk_data):
    global last_update_timestamp
    global previous_track

    last_update_timestamp = time.time()

    await sonos_data.refresh()

    if sonos_data.status == "API error":
        if remote_debug_key != "": print ("API error reported fyi")
        return

    current_trackname = sonos_data.trackname
    current_artist = sonos_data.artist
    current_album = sonos_data.album
    current_image_url = sonos_data.image

    # see if something is playing
    if sonos_data.status == "PLAYING":
        if remote_debug_key != "": print ("Music playing")

        checksum = f"{current_trackname}-{current_artist}-{current_album}-{current_image_url}"
        # check whether the track has changed - don't bother updating everything if not
        if checksum == previous_track:
            return

        if remote_debug_key != "": print ("Current track " + current_trackname + " is not same as previous track " + previous_track)

        # update previous trackname so we know what has changed in future
        previous_track = checksum

        # slim down the trackname
        if sonos_settings.demaster:
            current_trackname = demaster.strip_name (current_trackname)
            if remote_debug_key != "": print ("Demastered to " + current_trackname)

        # set the details we need from the API into variables
        tk_data.track_name.set(current_trackname)
        tk_data.detail_text.set(current_artist + " • "+ current_album)

        try:
            async with session.get(current_image_url) as response:
                image_url_response = await response.read()
            pil_image = Image.open(BytesIO(image_url_response))
        except:
            pil_image = Image.open (sys.path[0] + "/sonos.png")
            target_image_width = 500
            print ("Image failed to load so showing standard sonos logo")

        # set the image size based on whether we are showing track details as well
        if sonos_settings.show_details == True:
            target_image_width = thumbwidth
        else:
            target_image_width = screenwidth

        # resize the image
        wpercent = (target_image_width/float(pil_image.size[0]))
        hsize = int((float(pil_image.size[1])*float(wpercent)))
        pil_image = pil_image.resize((target_image_width,hsize), Image.ANTIALIAS)

        set_backlight_power(True)
        tk_image = ImageTk.PhotoImage(pil_image)
        tk_data.label_albumart.configure (image = tk_image)
    else:
        set_backlight_power(False)
        tk_data.track_name.set("")
        tk_data.detail_text.set("")
        tk_data.label_albumart.configure (image = "")
        previous_track = None
        if remote_debug_key != "": print ("Track not playing - doing nothing")

    tk_data.root.update()


def setup_tk():
    """Create the main Tk window."""
    # Create the main window
    root = tk.Tk()
    root.geometry("720x720")
    root.title("Music Display")

    # Create the main container
    frame = tk.Frame(root, bg='black', width=720, height=720)

    # Lay out the main container (expand to fit window)
    frame.pack(fill=tk.BOTH, expand=1)

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
    label_albumart = tk.Label(frame,
                            image = None,
                            font=image_font,
                            borderwidth=0,
                            highlightthickness=0,
                            fg='white',
                            bg='black')
    label_track = tk.Label(frame,
                            textvariable=track_name,
                            font=track_font,
                            fg='white',
                            bg='black',
                            wraplength=600,
                            justify="center")
    label_detail = tk.Label(frame,
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

    frame.grid_propagate(False)

    # Start in fullscreen mode
    root.attributes('-fullscreen', fullscreen)
    root.update()

    return TkData(root, detail_text, label_albumart, track_name)


async def main(loop):
    global last_update_timestamp
    if sonos_settings.room_name_for_highres == "":
        print ("No room name found in sonos_settings.py")
        print ("You can specify a room name manually below")
        print ("Note: manual entry works for testing purposes, but if you want this to run automatically on startup then you should specify a room name in sonos_settings.py")
        print ("You can edit the file with the command: nano sonos_settings.py")
        print ("")
        sonos_room = input ("Enter a Sonos room name for testing purposes>>>  ")
    else:
        sonos_room = sonos_settings.room_name_for_highres
        print ("Sonos room name set as " + sonos_room + " from settings file")

    session = ClientSession()
    sonos_data = SonosData(sonos_room, session)
    tk_data = setup_tk()

    async def webhook(request):
        """Handle a webhook received from node-sonos-http-api."""
        json = await request.json()
        if json['type'] == 'transport-state':
            if json['data']['roomName'] == sonos_room:
                await sonos_data.refresh(json['data']['state'])
                await update(session, sonos_data, tk_data)
        return web.Response(text="hello")

    server = web.Server(webhook)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()

    for signame in ('SIGINT', 'SIGTERM', 'SIGQUIT'):
        loop.add_signal_handler(getattr(signal, signame), lambda: asyncio.ensure_future(cleanup(loop, runner, session)))

    while True:
        if time.time() - last_update_timestamp > 30:
            await update(session, sonos_data, tk_data)
        await asyncio.sleep(1)

async def cleanup(loop, runner, session):
    set_backlight_power(True)
    await session.close()
    await runner.cleanup()

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

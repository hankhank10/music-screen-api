# This file is for use with the Pimoroni HyperPixel 4.0 Square (Non Touch) High Res display
# it integrates with your local Sonos sytem to display what is currently playing

import atexit
import tkinter as tk
import tkinter.font as tkFont
import time
import sys
import sonos_user_data
import sonos_settings
import requests
from io import BytesIO
from PIL import ImageTk, Image, ImageFile
import os
import demaster
import scrap

try:
    from rpi_backlight import Backlight
except ImportError:
    print ("Backlight control not available, please install the 'rpi_backlight' Python package: https://github.com/linusg/rpi-backlight#installation")
    backlight = None
else:
    backlight = Backlight()

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
#show_details = False   # if set to false then just shows the album art; if set to true then also displays track name + album/artist name
#show_artist_and_album = True   #if set to true then shows artist and album at the bottom; if false just shows track name; won't do anything if show_detail is false

# Declare global variables (don't mess with these)
root = None
frame = None
track_name = None
detail_text = None
tk_image = None
font_size = 0
previous_polled_trackname = ""
thumbwidth = thumbsize[1]
screenwidth = screensize[1]
sonos_room = None

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
def update():

    global root
    global track_name
    global tk_image
    global previous_polled_trackname

    # Get sonos data from API
    current_trackname, current_artist, current_album, current_image, playing_status = sonos_user_data.current(sonos_room)

    # see if something is playing
    if playing_status == "PLAYING":
        if remote_debug_key != "": print ("Music playing")

        # check whether the track has changed - don't bother updating everything if not
        if current_trackname != previous_polled_trackname:
            if remote_debug_key != "": print ("Current track " + current_trackname + " is not same as previous track " + previous_polled_trackname)

            # update previous trackname so we know what has changed in future
            previous_polled_trackname = current_trackname

            # slim down the trackname
            if sonos_settings.demaster:
                current_trackname = demaster.strip_name (current_trackname)
                if remote_debug_key != "": print ("Demastered to " + current_trackname)

            # set the details we need from the API into variables
            track_name.set(current_trackname)
            detail_text.set(current_artist + " • "+ current_album)

            # pull the image from the uri provided
            image_url = current_image

            image_failed_to_load = False
            try:
                image_url_response = requests.get(image_url, timeout=sonos_user_data.DEFAULT_TIMEOUT)
                pil_image = Image.open(BytesIO(image_url_response.content))
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
            label_albumart.configure (image = tk_image)

    if playing_status == "API error":
        if remote_debug_key != "": print ("API error reported fyi")
        time.sleep (5)

    if playing_status != "PLAYING":
        set_backlight_power(False)
        track_name.set("")
        detail_text.set("")
        label_albumart.configure (image = "")
        previous_polled_trackname = ""
        if remote_debug_key != "": print ("Track not playing - doing nothing")

    # Schedule the poll() function for another 500 ms from now
    root.after(500, update)

###############################################################################
# Main script

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

@atexit.register
def goodbye():
    """Clean up when script is exiting."""
    set_backlight_power(True)
    print("Exiting")

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

# Schedule the poll() function to be called periodically
root.after(20, update)

# Start in fullscreen mode and run
root.attributes('-fullscreen', fullscreen)
try:
    root.mainloop()
except KeyboardInterrupt:
    pass

"""Implementation of the DisplayController class."""
import logging
import os
import tkinter as tk
from tkinter import Y, font as tkFont

from PIL import ImageTk

from hyperpixel_backlight import Backlight

_LOGGER = logging.getLogger(__name__)

class SonosDisplaySetupError(Exception):
    """Error connecting to Sonos display."""

class DisplayController:  # pylint: disable=too-many-instance-attributes
    """Controller to handle the display hardware and GUI interface."""

    def __init__(self, loop, show_details, show_artist_and_album, show_details_timeout, overlay_text, show_play_state):
        """Initialize the display controller."""

        self.SCREEN_W = 720
        self.SCREEN_H = 720
        self.THUMB_W = 0
        self.THUMB_H = 0

        self.loop = loop
        self.show_details = show_details
        self.show_artist_and_album = show_artist_and_album
        self.show_details_timeout = show_details_timeout
        self.overlay_text = overlay_text
        self.show_play_state = show_play_state

        self.album_image = None
        self.thumb_image = None
        self.label_track = None
        self.label_detail = None
        self.label_play_state = None
        self.label_play_state_album = None
        self.track_font = None
        self.detail_font = None
        self.timeout_future = None
        self.is_showing = False

        self.backlight = Backlight()

        try:
            self.root = tk.Tk()
        except tk.TclError:
            self.root = None

        if not self.root:
            os.environ["DISPLAY"] = ":0"
            try:
                self.root = tk.Tk()
            except tk.TclError as error:
                _LOGGER.error("Cannot access display: %s", error)
                raise SonosDisplaySetupError

        self.root.geometry(f"{self.SCREEN_W}x{self.SCREEN_H}")

        self.album_frame = tk.Frame(
            self.root, bg="black", width=self.SCREEN_W, height=self.SCREEN_H
        )
        self.album_frame.grid(row=0, column=0, sticky="news")

        self.detail_frame = tk.Frame(
            self.root, bg="black", width=self.SCREEN_W, height=self.SCREEN_H
        )
        self.detail_frame.grid(row=0, column=0, sticky="news")

        self.curtain_frame = tk.Frame(
            self.root, bg="black", width=self.SCREEN_W, height=self.SCREEN_H
        )
        self.curtain_frame.grid(row=0, column=0, sticky="news")

        self.track_name = tk.StringVar()
        self.detail_text = tk.StringVar()
        self.play_state_text = tk.StringVar()

        self.detail_font = tkFont.Font(family="Helvetica", size=15)
        self.play_state_font = tkFont.Font(family="Helvetica", size=17)

        self.label_albumart = tk.Label(
            self.album_frame,
            image=None,
            borderwidth=0,
            highlightthickness=0,
            fg="white",
            bg="black",
        )
        self.label_albumart.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.label_albumart_detail = tk.Label(
            self.detail_frame,
            image=None,
            borderwidth=0,
            highlightthickness=0,
            fg="white",
            bg="black",
        )
        self.label_track = tk.Label(
            self.detail_frame,
            textvariable=self.track_name,
            fg="white",
            bg="black",
            wraplength=600,
            justify="center",
        )
        self.label_detail = tk.Label(
            self.detail_frame,
            textvariable=self.detail_text,
            font=self.detail_font,
            fg="white",
            bg="black",
            wraplength=600,
            justify="center",
        )
        self.label_play_state = tk.Label(
            self.detail_frame,
            textvariable=self.play_state_text,
            fg="white",
            bg="black",
            wraplength=700,
            justify="center",
        )
        self.label_play_state_album = tk.Label(
            self.album_frame,
            textvariable=self.play_state_text,
            fg="white",
            bg="black",
            wraplength=700,
            justify="center",
        )

        self.album_frame.grid_propagate(False)
        self.detail_frame.grid_propagate(False)

        self.root.attributes("-fullscreen", True)
        self.root.update()

    def show_album(self, show_details=None, detail_timeout=None):
        """Show album with optional detail display and timeout."""
        def handle_timeout():
            self.timeout_future = None
            self.show_album(show_details=False)

        if show_details is None and detail_timeout is None:
            self.curtain_frame.lower()
        elif show_details:
            self.detail_frame.lift()
            if detail_timeout:
                if self.timeout_future:
                    self.timeout_future.cancel()
                self.timeout_future = self.loop.call_later(detail_timeout, handle_timeout)
        else:
            self.album_frame.lift()
            self.label_play_state_album.destroy()

        self.is_showing = True
        self.root.update()
        self.backlight.set_power(True)

    def hide_album(self):
        """Hide album if showing."""
        if self.timeout_future:
            self.timeout_future.cancel()
            self.timeout_future = None
            self.show_album(show_details=False)

        self.is_showing = False
        self.backlight.set_power(False)
        self.curtain_frame.lift()
        self.root.update()

    def update(self, image, sonos_data):
        """Update displayed image and text."""

        def resize_image(image, length):
            """Resizes the image, assumes square image."""
            image = image.resize((length, length), ImageTk.Image.ANTIALIAS)
            return ImageTk.PhotoImage(image)

        display_trackname = sonos_data.trackname or sonos_data.station

        detail_text = ""
        play_state_text = ""

        if self.show_artist_and_album:
            detail_prefix = None
            detail_suffix = sonos_data.album or None

            if sonos_data.artist != display_trackname:
                detail_prefix = sonos_data.artist

            detail_text = " • ".join(filter(None, [detail_prefix, detail_suffix]))

        if self.show_play_state:
            play_state_volume = sonos_data.volume or None
            play_state_shuffle = sonos_data.shuffle or None
            play_state_repeat = sonos_data.repeat or None
            play_state_crossfade = sonos_data.crossfade or None

            play_state_volume_text = "Volume: " + str(play_state_volume)

            play_state_shuffle_text = "Shuffle: " + str(play_state_shuffle)

            play_state_repeat_text = "Repeat: " + str(play_state_repeat)

            play_state_crossfade_text = "Crossfade: " + str(play_state_crossfade)

            play_state_text = " • ".join(filter(None, [play_state_volume_text, play_state_shuffle_text, play_state_repeat_text, play_state_crossfade_text]))

        if self.show_artist_and_album:
            if len(display_trackname) > 30:
                if len(detail_text) > 60:
                    self.THUMB_H = 560
                    self.THUMB_W = 560
                else:
                    self.THUMB_H = 580
                    self.THUMB_W = 580
                if detail_text == "":
                    self.track_font = tkFont.Font(family="Helvetica", size=30)
                else:
                    self.track_font = tkFont.Font(family="Helvetica", size=25)
            else:
                if len(detail_text) > 60:
                    self.THUMB_H = 600
                    self.THUMB_W = 600
                else:
                    self.THUMB_H = 620
                    self.THUMB_W = 620
                if detail_text == "":
                    self.track_font = tkFont.Font(family="Helvetica", size=40)
                    self.THUMB_H = self.THUMB_H + 20
                    self.THUMB_W = self.THUMB_W + 20
                else:
                    self.track_font = tkFont.Font(family="Helvetica", size=30)

            if len(display_trackname) > 30 and len(display_trackname) < 36:
                self.THUMB_H = self.THUMB_H + 40
                self.THUMB_W = self.THUMB_W + 40
            
            #if len(detail_text) > 45 and len(detail_text) < 50:
            #    self.THUMB_H = self.THUMB_H + 20
            #    self.THUMB_W = self.THUMB_W + 20
        else:
            if len(display_trackname) > 22:
                self.THUMB_H = 610
                self.THUMB_W = 610
                self.track_font = tkFont.Font(family="Helvetica", size=30)
            else:
                self.THUMB_H = 640
                self.THUMB_W = 640
                self.track_font = tkFont.Font(family="Helvetica", size=40)

            if len(display_trackname) > 22 and len(display_trackname) < 35:
                self.THUMB_H = self.THUMB_H + 40
                self.THUMB_W = self.THUMB_W + 40

            #if len(detail_text) > 45 and len(detail_text) < 50:
            #    self.THUMB_H = self.THUMB_H + 20
            #    self.THUMB_W = self.THUMB_W + 20

        # Store the images as attributes to preserve scope for Tk
        self.album_image = resize_image(image, self.SCREEN_W)
        if self.overlay_text:
            self.thumb_image = resize_image(image, self.SCREEN_W)
            self.label_albumart_detail.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        else:
            self.thumb_image = resize_image(image, self.THUMB_W)
            self.label_albumart_detail.place(relx=0.5, y=self.THUMB_H / 2, anchor=tk.CENTER)

        self.label_track.place(relx=0.5, y=self.THUMB_H + 10, anchor=tk.N)

        if detail_text == "" or not self.show_artist_and_album:
            self.label_detail.destroy()
        else:
            if self.label_detail.winfo_exists() == 0:
                self.label_detail = tk.Label(
                    self.detail_frame,
                    textvariable=self.detail_text,
                    font=self.detail_font,
                    fg="white",
                    bg="black",
                    wraplength=600,
                    justify="center",
                )
            self.label_detail.place(relx=0.5, y=self.SCREEN_H - 10, anchor=tk.S)
            self.label_detail.configure(font=self.detail_font)

        if not self.show_play_state:
            self.label_play_state.destroy()
            self.label_play_state_album.destroy()
        else:
            if self.label_play_state.winfo_exists() == 0:
                self.label_play_state = tk.Label(
                    self.detail_frame,
                    textvariable=self.play_state_text,
                    font=self.play_state_font,
                    fg="white",
                    bg="black",
                    wraplength=700,
                    justify="center",
                )
            self.label_play_state.place(relx=0.5, y= 10, anchor=tk.N)
            self.label_play_state.configure(font=self.play_state_font)

            if self.label_play_state_album.winfo_exists() == 0:
                self.label_play_state_album = tk.Label(
                    self.album_frame,
                    textvariable=self.play_state_text,
                    font=self.play_state_font,
                    fg="white",
                    bg="black",
                    wraplength=700,
                    justify="center",
                )
            self.label_play_state_album.place(relx=0.5, y= 10, anchor=tk.N)
            self.label_play_state_album.configure(font=self.play_state_font)

        self.label_albumart.configure(image=self.album_image)
        self.label_albumart_detail.configure(image=self.thumb_image)
        self.label_track.configure(font=self.track_font)

        self.track_name.set(display_trackname)
        self.detail_text.set(detail_text)
        self.play_state_text.set(play_state_text)
        self.root.update_idletasks()
        self.show_album(self.show_details, self.show_details_timeout)

    def cleanup(self):
        """Run cleanup actions."""
        self.backlight.cleanup()

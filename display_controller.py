"""Implementation of the DisplayController class."""
import logging
import os
import tkinter as tk
from tkinter import font as tkFont

from PIL import ImageTk

from hyperpixel_backlight import Backlight

_LOGGER = logging.getLogger(__name__)

class SonosDisplaySetupError(Exception):
    """Error connecting to Sonos display."""

class DisplayController:  # pylint: disable=too-many-instance-attributes
    """Controller to handle the display hardware and GUI interface."""

    def __init__(self, loop, show_details, show_artist_and_album, show_details_timeout):
        """Initialize the display controller."""
        
        self.SCREEN_W = 720
        self.SCREEN_H = 720
        self.THUMB_W = 0
        self.THUMB_H = 0
        
        self.loop = loop
        self.show_details = show_details
        self.show_artist_and_album = show_artist_and_album
        self.show_details_timeout = show_details_timeout

        self.album_image = None
        self.thumb_image = None
        self.label_track = None
        self.label_detail = None
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

        self.detail_font = tkFont.Font(family="Helvetica", size=15)

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

        if self.show_artist_and_album:
            detail_prefix = None
            detail_suffix = sonos_data.album or None

            if sonos_data.artist != display_trackname:
                detail_prefix = sonos_data.artist

            detail_text = " • ".join(filter(None, [detail_prefix, detail_suffix]))

        if self.show_artist_and_album:
            if len(display_trackname) > 30:
                if len(detail_text) > 45:
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
                if len(detail_text) > 45:
                    self.THUMB_H = 600
                    self.THUMB_W = 600
                else:
                    self.THUMB_H = 620
                    self.THUMB_W = 620
                if detail_text == "":
                    self.track_font = tkFont.Font(family="Helvetica", size=40)
                else:
                    self.track_font = tkFont.Font(family="Helvetica", size=30)
        else:
            if len(display_trackname) > 25:
                self.THUMB_H = 600
                self.THUMB_W = 600
                self.track_font = tkFont.Font(family="Helvetica", size=30)
            else:
                self.THUMB_H = 620
                self.THUMB_W = 620
                self.track_font = tkFont.Font(family="Helvetica", size=40) 
        
        # Store the images as attributes to preserve scope for Tk
        self.album_image = resize_image(image, self.SCREEN_W)
        self.thumb_image = resize_image(image, self.THUMB_W)

        self.label_albumart_detail.place(relx=0.5, y=self.THUMB_H / 2, anchor=tk.CENTER)
        self.label_track.place(relx=0.5, y=self.THUMB_H + 10, anchor=tk.N)
        if detail_text == "":
            self.label_detail.place(relx=0.5, y=self.SCREEN_H + 10, anchor=tk.S)
        else:
            self.label_detail.place(relx=0.5, y=self.SCREEN_H - 10, anchor=tk.S)

        self.label_albumart.configure(image=self.album_image)
        self.label_albumart_detail.configure(image=self.thumb_image)
        self.label_track.configure(font=self.track_font)

        self.track_name.set(display_trackname)
        self.detail_text.set(detail_text)
        self.root.update_idletasks()
        self.show_album(self.show_details, self.show_details_timeout)

    def cleanup(self):
        """Run cleanup actions."""
        self.backlight.cleanup()

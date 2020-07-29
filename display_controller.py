"""Implementation of the DisplayController class."""
import logging
import tkinter as tk
from tkinter import font as tkFont

from PIL import ImageTk

from hyperpixel_backlight import Backlight

_LOGGER = logging.getLogger(__name__)

SCREEN_W = 720
SCREEN_H = 720
THUMB_W = 600
THUMB_H = 600


class DisplayController:  # pylint: disable=too-many-instance-attributes
    """Controller to handle the display hardware and GUI interface."""

    def __init__(self, loop, show_details, show_artist_and_album, show_details_timeout):
        """Initialize the display controller."""
        self.loop = loop
        self.show_details = show_details
        self.show_artist_and_album = show_artist_and_album
        self.show_details_timeout = show_details_timeout

        self.album_image = None
        self.thumb_image = None
        self.timeout_future = None
        self.is_showing = False

        self.backlight = Backlight()

        self.root = tk.Tk()
        self.root.geometry(f"{SCREEN_W}x{SCREEN_H}")

        self.album_frame = tk.Frame(
            self.root, bg="black", width=SCREEN_W, height=SCREEN_H
        )
        self.album_frame.grid(row=0, column=0, sticky="news")

        self.detail_frame = tk.Frame(
            self.root, bg="black", width=SCREEN_W, height=SCREEN_H
        )
        self.detail_frame.grid(row=0, column=0, sticky="news")

        self.curtain_frame = tk.Frame(
            self.root, bg="black", width=SCREEN_W, height=SCREEN_H
        )
        self.curtain_frame.grid(row=0, column=0, sticky="news")

        self.track_name = tk.StringVar()
        self.detail_text = tk.StringVar()

        if show_artist_and_album:
            track_font = tkFont.Font(family="Helvetica", size=30)
        else:
            track_font = tkFont.Font(family="Helvetica", size=40)
        detail_font = tkFont.Font(family="Helvetica", size=15)

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
        label_track = tk.Label(
            self.detail_frame,
            textvariable=self.track_name,
            font=track_font,
            fg="white",
            bg="black",
            wraplength=600,
            justify="center",
        )
        label_detail = tk.Label(
            self.detail_frame,
            textvariable=self.detail_text,
            font=detail_font,
            fg="white",
            bg="black",
            wraplength=600,
            justify="center",
        )
        self.label_albumart_detail.place(relx=0.5, y=THUMB_H / 2, anchor=tk.CENTER)
        label_track.place(relx=0.5, y=THUMB_H + 20, anchor=tk.N)
        label_detail.place(relx=0.5, y=SCREEN_H - 10, anchor=tk.S)

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

        # Store the images as attributes to preserve scope for Tk
        self.album_image = resize_image(image, SCREEN_W)
        self.thumb_image = resize_image(image, THUMB_W)

        self.label_albumart.configure(image=self.album_image)
        self.label_albumart_detail.configure(image=self.thumb_image)

        self.track_name.set(sonos_data.trackname or sonos_data.station)

        if self.show_artist_and_album:
            detail_text = sonos_data.artist
            if sonos_data.album:
                detail_text += f" • {sonos_data.album}"
            if sonos_data.station and not sonos_data.trackname:
                detail_text += f"\n{sonos_data.station}"
            self.detail_text.set(detail_text)

        self.show_album(self.show_details, self.show_details_timeout)

    def cleanup(self):
        """Run cleanup actions."""
        self.backlight.cleanup()

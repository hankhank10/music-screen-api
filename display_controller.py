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

    def __init__(self, show_details, show_artist_and_album):
        """Initialize the display controller."""
        self.show_details = show_details
        self.show_artist_and_album = show_artist_and_album

        self.album_image = None
        self.is_showing = False

        self.backlight = Backlight()

        self.root = tk.Tk()
        self.root.geometry(f"{SCREEN_W}x{SCREEN_H}")

        self.album_frame = tk.Frame(
            self.root, bg="black", width=SCREEN_W, height=SCREEN_H
        )
        self.album_frame.grid(row=0, column=0, sticky="news")

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
        label_track = tk.Label(
            self.album_frame,
            textvariable=self.track_name,
            font=track_font,
            fg="white",
            bg="black",
            wraplength=600,
            justify="center",
        )
        label_detail = tk.Label(
            self.album_frame,
            textvariable=self.detail_text,
            font=detail_font,
            fg="white",
            bg="black",
            wraplength=600,
            justify="center",
        )

        if show_details:
            self.label_albumart.place(relx=0.5, y=THUMB_H / 2, anchor=tk.CENTER)
            label_track.place(relx=0.5, y=THUMB_H + 20, anchor=tk.N)
            if show_artist_and_album:
                label_detail.place(relx=0.5, y=SCREEN_H - 10, anchor=tk.S)
        else:
            self.label_albumart.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.album_frame.grid_propagate(False)

        self.root.attributes("-fullscreen", True)
        self.root.update()

    def show_album(self, should_show):
        """Control if album art should be displayed or hidden."""
        if should_show != self.is_showing:
            if should_show:
                self.album_frame.lift()
            else:
                self.curtain_frame.lift()
            self.is_showing = should_show
        self.root.update()
        self.backlight.set_power(should_show)

    def update(self, image, track, artist, album):
        """Update displayed image and text."""
        if self.show_details:
            target_image_width = THUMB_W
        else:
            target_image_width = SCREEN_W

        wpercent = target_image_width / float(image.size[0])
        hsize = int(float(image.size[1]) * float(wpercent))
        image = image.resize((target_image_width, hsize))

        # Store the image as an attribute to preserve scope for Tk
        self.album_image = ImageTk.PhotoImage(image)
        self.label_albumart.configure(image=self.album_image)

        self.track_name.set(track)

        if self.show_artist_and_album:
            detail_text = artist
            if album:
                detail_text += f" • {album}"
            self.detail_text.set(detail_text)

    def cleanup(self):
        """Run cleanup actions."""
        self.backlight.cleanup()

# Music screen

Display your currently playing music track on an e-ink display.

![Example of what it looks like](https://user-images.githubusercontent.com/25515609/84536452-c6bd3b80-ace5-11ea-82b6-4c9f22ed3a6a.jpg)

Works in real time with your local Sonos sytem. Also includes functionality to pull last played tracks and music history from last.fm.

No authentication required for either service.

Note: this replaces the now depricated [ink-music-stats](https://github.com/hankhank10/ink-music-stats) repo.

# Required hardware

Raspberry Pi (Zero - 4)

[Pimoroni inky wHAT](https://shop.pimoroni.com/products/inky-what?variant=21214020436051)

# Installation

Install and have a running version of [node-sonos-http-api](https://github.com/jishi/node-sonos-http-api)

Install the Pimoroni inky wHAT on your Raspberry Pi.  Ensure that you have enabled I2C in ```raspi-config```

Install the Pimoroni *inky* library using ```pip install inky```

Clone or download this repo into your Raspberry Pi.

Run one of the following python scripts depending on your desired functionality:

```python3 gosonos.py "YOUR SONOS ROOM NAME"
python3 golast.py "YOUR LASTFM USERNAME"
```

You probably want to automate the running of these commands on startup using PM2 or something similar.
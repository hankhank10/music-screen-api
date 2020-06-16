# Music screen

Display your currently playing music track on a constantly updated e-ink display.

![Example of what it looks like](https://user-images.githubusercontent.com/25515609/84579142-7e744b00-adc3-11ea-8c77-584094464639.jpg)

Works in real time with your local Sonos sytem. Also includes functionality to pull last played tracks and music history from last.fm.

No authentication required for either service.

Note: this replaces the now deprecated [ink-music-stats](https://github.com/hankhank10/ink-music-stats) repo.

# Required hardware

Raspberry Pi (Zero - 4)

[Pimoroni inky wHAT](https://shop.pimoroni.com/products/inky-what?variant=21214020436051)

# Step-by-step beginner installation instructions

I have put together step-by-step basic instructions [on hackster here](https://www.hackster.io/mark-hank/currently-playing-music-on-e-ink-display-310645)

# Advanced user installation instructions

Install and have a running version of [node-sonos-http-api](https://github.com/jishi/node-sonos-http-api)

Put the Pimoroni inky wHAT hardware on your Raspberry Pi. (Do with power off, obviously)

Install the inky library with
```curl https://get.pimoroni.com/inky | bash```

(Don't be tempted to pip install the inky library - the install script does a bunch of other stuff you need)

Clone or download this repo into your Raspberry Pi.

Run one of the following python scripts depending on your desired functionality:

```
python3 go_sonos.py YOUR_SONOS_ROOM_NAME_IF_IT_IS_JUST_ONE_WORD
python3 go_sonos.py "YOUR_SONOS_ROOM_NAME_IF_IT_IS_MULTIPLE_WORDS"
python3 go_last.py YOUR_LASTFM_USERNAME
```

You probably want to automate the running of these commands on startup using PM2 or something similar.

# Important notice on "demaster"

This script uses my ["demaster" script](https://github.com/hankhank10/demaster) to remove some of the nonsense from the end of track names which make them difficult to display (eg - Live at etc, (Remastered 2011), etc). This is highly recommended for displaying on a screen as otherwise it becomes unweildy to read the track names.

Two important points for you to note here:

1. If you want to turn this off then you can by opening sonossettings.py and changing demaster to False. This will then show the full track name as reported by Sonos.

2. Demaster makes use of an online API to efficiently reduce the track names and ensure that it is able to learn from previous amendments. This means that in default mode track names are sent to a remote server when they are played to get the shorter name. No personally identifying information is associated with this API request but if you're uncomfortable with this then rather than disabling demaster entirely then you can set it to run in offline only mode by setting the offline_only_mode flag in demaster.py to True.  This means that the local script will attempt to do some limited reduction of nonsense in track names, but you won't benefit from the latest algorithm to do this - but it's still a lot better than nothing if you're worried about privacy.

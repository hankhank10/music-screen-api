# Music screen

A set of scripts to display current and recent music information.

It uses either the Pimoroni wHAT e-ink display to display track information; or the Pimoroni HyperPixel 4.0 Square (Non Touch) High Res display to display full colour album art.

![Example of what it looks like](https://user-images.githubusercontent.com/25515609/84962206-370cf800-b0fe-11ea-99c9-b3546d847ecc.jpg)

Works in real time with your local Sonos sytem. Also includes functionality to pull last played tracks and music history from last.fm.

No authentication required for either service.

Note: this replaces the now deprecated [ink-music-stats](https://github.com/hankhank10/ink-music-stats) repo.

# Required hardware

Raspberry Pi 3 or 4
Note: a Pi Zero WH can be made to run the e-ink version - BUT see below for note on how to get this working

[Pimoroni inky wHAT](https://shop.pimoroni.com/products/inky-what?variant=21214020436051)

[Pimoroni HyperPixel 4.0 Square Non Touch](https://shop.pimoroni.com/products/hyperpixel-4-square?variant=30138251477075)

# Step-by-step beginner installation instructions

I have put together step-by-step basic instructions:

- [e-INK version here](https://www.hackster.io/mark-hank/currently-playing-music-on-e-ink-display-310645)
- [High res version here](https://www.hackster.io/mark-hank/sonos-album-art-on-raspberry-pi-screen-5b0012)

# Optional backlight control

Thanks to a pull request from [jjlawren](https://github.com/jjlawren) there is now the option to have the backlight of the Hyperpixel turn off when music is not playing.

In order to activate this you need run the following commands:
```
pip3 install rpi-backlight
$ echo 'SUBSYSTEM=="backlight",RUN+="/bin/chmod 666 /sys/class/backlight/%k/brightness /sys/class/backlight/%k/bl_power"' | sudo tee -a /etc/udev/rules.d/backlight-permissions.rules

```

Full instructions here: https://github.com/linusg/rpi-backlight#installation

# Important notice on Pi Zero

The e-ink script can be got running with a Pi Zero, however you will want to note two things:

1. Save yourself a headache and ensure you're getting a Pi Zero WH (ie wireless and with headers pre-soldered)

2. It runs pretty poorly on a Pi Zero due to the processing requirements. Actually this script runs fine, but it can struggle to do this and the http-sonos-api consistently. If you are set on running on a Pi Zero then either have the sonos-api running on a different local machine (and redirect to that IP address in sonos_settings.py) or set the Pi_Zero flag in sonos_settings.py to True (this slows down the frequency of requests)

(Thanks to reddit user u/Burulambie for helping me trouble shoot this)

I wouldn't recommend running the high res colour version from a Pi Zero.

# Important notice on "demaster"

This script uses my ["demaster" script](https://github.com/hankhank10/demaster) to remove some of the nonsense from the end of track names which make them difficult to display (eg - Live at etc, (Remastered 2011), etc). This is highly recommended for displaying on a screen as otherwise it becomes unweildy to read the track names.

Two important points for you to note here:

1. If you want to turn this off then you can by opening sonossettings.py and changing demaster to False. This will then show the full track name as reported by Sonos.

2. Demaster makes use of an online API to efficiently reduce the track names and ensure that it is able to learn from previous amendments. This means that in default mode track names are sent to a remote server when they are played to get the shorter name. No personally identifying information is associated with this API request but if you're uncomfortable with this then rather than disabling demaster entirely then you can set it to run in offline only mode by setting the offline_only_mode flag in demaster.py to True.  This means that the local script will attempt to do some limited reduction of nonsense in track names, but you won't benefit from the latest algorithm to do this - but it's still a lot better than nothing if you're worried about privacy.

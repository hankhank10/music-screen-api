# Music screen

A set of scripts to display current and recent music information.

It uses either the Pimoroni wHAT e-ink display to display track information; or the Pimoroni HyperPixel 4.0 Square (Non Touch) High Res display to display full colour album art.

![sonos-music-api Examples of Display Modes](https://user-images.githubusercontent.com/42817877/153710473-2fbe9534-b7d6-423e-8fd3-20193611c99e.png)

![sonos-music-api Examples of Display Modes Show Play Settings](https://user-images.githubusercontent.com/42817877/209093576-1bf5e0c0-ef5d-473f-8d7a-9d06ddb2f1e0.png)

Works in real time with your local Sonos sytem. Also includes functionality to pull last played tracks and music history from last.fm.

No authentication required for either service.

Note: this replaces the now deprecated [ink-music-stats](https://github.com/hankhank10/ink-music-stats) repo.

Note: A Spotify developer account ([Information here](https://developer.spotify.com/)) is required to display the Spotify Code of the playing track 

# Required hardware

Raspberry Pi 3 or 4 are recommended. The Pi 3 A+ is a smaller form factor which fits behind the HyperPixel Square display nicely as long as no more than one USB port is needed for other projects.

Raspberry Pi Zero W can be used with some stipulations noted [here](#important-notice-on-pi-zero).

[Pimoroni inky wHAT](https://shop.pimoroni.com/products/inky-what?variant=21214020436051)

[Pimoroni HyperPixel 4.0 Square Non Touch](https://shop.pimoroni.com/products/hyperpixel-4-square?variant=30138251477075)

# Step-by-step beginner installation instructions

I have put together step-by-step basic instructions:

- [e-INK version here](https://www.hackster.io/mark-hank/currently-playing-music-on-e-ink-display-310645)
- [High res version here](https://www.hackster.io/mark-hank/sonos-album-art-on-raspberry-pi-screen-5b0012)

Note that before running go_sonos_highres.py you need to create your own copy of sonos_settings.py: there is an example file in this repo as sonos_settings.py.example

# Key dependencies to load if you know what you're doing and don't want to follow all the steps above

````
sudo apt install python3-tk
sudo apt install python3-pil 
sudo apt install python3-pil.imagetk
sudo pip3 install requests
sudo pip3 install aiohttp RPi.GPIO
````

# Webhook updates

Enabling webhook support in the `node-sonos-http-api` configuration is **strongly** recommended. Without this enabled, the script must repeatedly poll to check for updates.

Webhook support for `node-sonos-http-api` can be enabled by updating/creating the `settings.json` configuration file located in the base of the `node-sonos-http-api/` directory:
```
{
  "webhook": "http://localhost:8080/"
}
```
_Note_: This file does not exist by default and you may need to create it. Also note that the `settings.js` file is part of the `node-sonos-http-api` code and should **not** be modified.

The above configuration assumes that `node-sonos-http-api` is running on the same machine. If running on a different machine, replace `localhost` with the IP of the host running this script.



# Backlight control

Thanks to a pull request from [jjlawren](https://github.com/jjlawren) the backlight of the Hyperpixel will turn off when music is not playing to save power & the environment.

If running Raspbian / Raspberry Pi OS, this should work out of the box. If running a different distribution, you'll need to run the following commands:
```
sudo pip3 install RPi.GPIO
sudo gpasswd -a pi gpio

```

# Displaying Spotify Codes or Using Spotify Album Art

To display a Soptify Code or use Spotify album art instead of that loaded on to your Sonos system for the playing song, you need a Spotify Developer account ([Information here](https://developer.spotify.com/)), as well as adding your Client_ID and client_SECRET into the sonos_settings.py file and set the show_spotify_code and/or show_spotify_albumart to True as below:
```
#Spotify API Details
spotify_client_id = ""
spotify_client_secret = ""
spotify_market = None

# Show a Spotify Code graphic for the currently playing song if playing from Spotify
show_spotify_code = True

#Overide the albumart with that from Spotify if available
show_spotify_albumart = True

NOTE: You can localise the SPotify search to your country using the spotify_market setting in sonos_settings.py by substuting None for one of the country codes recognised by the Spotify API ([Information Here](https://developer.spotify.com/documentation/web-api/reference/#/operations/search))

```

# REST API

The script exposes some REST API endpoints to allow remote control and integration options.

| Method | Endpoint       | Payload | Notes |
| :----: | :------------: | ------- | ----- |
| `GET`  | `/state`       | None    | Provides current playing state in JSON format. |
| `POST` | `/set-room`    | `room`: name of room (`str`) | Change actively monitored speaker/room. |
| `POST` | `/show-detail` | `detail`: 0/1, true/false (`bool`, required)<br/><br/>`timeout`: seconds (`int`, optional)| Show/hide the detail view. Use `timeout` to revert to the full album view after a delay. Has no effect if paused/stopped. |

Examples:
```
curl http://<IP_OF_HOST>:8080/status
 -> {"room": "Bedroom", "status": "PLAYING", "trackname": "Living For The City", "artist": "Stevie Wonder", "album": "Innervisions", "duration": 442, "webhook_active": true}

curl --data "room=Kitchen" http://<IP_OF_HOST>:8080/set-room
 -> OK
 
curl --data "detail=true" --data "timeout=5" http://<IP_OF_HOST>:8080/show-detail
 -> OK
```

# Important notice on Pi Zero

### HyperPixel version

A Pi Zero W can run both `node-sonos-http-api` and the full color album art version as long as [webhooks](#webhook-updates) have been properly enabled. It updates slightly slower (1-2 seconds) than a Pi 3/4.

### E-ink version

_Note: The e-ink version has not been updated to use [webhooks](#webhook-updates) which the HyperPixel version uses and requires the performance tweaks below._

The e-ink script can be got running with a Pi Zero, however you will want to note two things:

1. Save yourself a headache and ensure you're getting a Pi Zero WH (ie wireless and with headers pre-soldered)

2. It runs pretty poorly on a Pi Zero due to the processing requirements. Actually this script runs fine, but it can struggle to do this and the http-sonos-api consistently. If you are set on running on a Pi Zero then either have the sonos-api running on a different local machine (and redirect to that IP address in sonos_settings.py) or set the Pi_Zero flag in sonos_settings.py to True (this slows down the frequency of requests)

(Thanks to reddit user u/Burulambie for helping me trouble shoot this)

# Important notice on "demaster"

This script uses my ["demaster" script](https://github.com/hankhank10/demaster) to remove some of the nonsense from the end of track names which make them difficult to display (eg - Live at etc, (Remastered 2011), etc). This is highly recommended for displaying on a screen as otherwise it becomes unweildy to read the track names.

Two important points for you to note here:

1. If you want to turn this off then you can by opening sonossettings.py and changing demaster to False. This will then show the full track name as reported by Sonos.

2. Demaster makes use of an online API to efficiently reduce the track names and ensure that it is able to learn from previous amendments. This means that in default mode track names are sent to a remote server when they are played to get the shorter name. No personally identifying information is associated with this API request but if you're uncomfortable with this then rather than disabling demaster entirely then you can set it to run in offline only mode by setting the `demaster_query_cloud` option in your `sonos_settings.py` to `False`.  This means that the local script will attempt to do some limited reduction of nonsense in track names, but you won't benefit from the latest algorithm to do this - but it's still a lot better than nothing if you're worried about privacy.

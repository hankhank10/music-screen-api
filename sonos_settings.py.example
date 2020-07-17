### Sonos settings

## General settings

sonos_http_api_address = "localhost"
sonos_http_api_port = "5005"

log_file = "~/music-screen-api.log"
log_level = "DEBUG"  # One of ERROR, WARNING, INFO, DEBUG (in order of least to most verbose)

demaster = True #crop song names to remove nonsense such as "Remastered" or "live at"

## High-res only settings
room_name_for_highres = ""   # the go_sonos_highres.py file cannot be reliably passed multi-word arguments on startup, so the room is defined here instead
show_details = False   # if set to False then just shows the album art; if set to true then also displays track name + album/artist name
show_artist_and_album = True   # if set to true then shows artist and album at the bottom; if false just shows track name; won't do anything if show_detail is false

## e-ink only settings
pi_zero = False  #if running on a pi-zero which is also running the sonos-http-api then set this to True to make it wait 120 seconds after boot before hitting the server to improve reliability on startup
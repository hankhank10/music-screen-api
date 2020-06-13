import urllib.request
import json
import sonos_settings

def current(sonos_room):
    # convert any spaces to url-suitable character
    sonos_room = sonos_room.replace(" ", "%20")

    # build URL
    url = "http://" + sonos_settings.sonos_http_api_address + ":" + sonos_settings.sonos_http_api_port + "/" + sonos_room + "/state"

    # download the raw json object and parse the json data
    data = urllib.request.urlopen(url).read().decode()
    obj = json.loads(data)

    # extract relevant data
    current_trackname = obj['currentTrack']['title']
    current_artist = obj['currentTrack']['artist']
    current_album = obj['currentTrack']['album']
    current_image = obj['currentTrack']['absoluteAlbumArtUri']
    playing_status = obj['playbackState']

    return current_trackname, current_artist, current_album, current_image, playing_status
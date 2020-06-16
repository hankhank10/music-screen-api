import requests
import json
import sonos_settings
import time

def find_unknown_radio_station_name(filename):
    # BBC streams started via alexa don't return their real name, which is annoying... but fixable:
    # if you find other stations which are not shown then you can add them below. Please put up on github will a pull request if you do
    if filename == "bbc_radio_two.m3u8": return "BBC Radio 2"
    if filename == "bbc_6music.m3u8": return "BBC Radio 6 Music"
    if filename == "bbc_radio_hereford_worcester.m3u8": return "BBC Hereford & Worcester"
    if filename == "bbc_radio_one.m3u8": return "BBC Radio 1"
    if filename == "bbc_1xtra.m3u8": return "BBC Radio 1Xtra"
    if filename == "bbc_radio_two.m3u8": return "BBC Radio 2"
    if filename == "bbc_radio_three.m3u8": return "BBC Radio 3"
    if filename == "bbc_radio_fourfm.m3u8": return "BBC Radio 4"
    if filename == "bbc_radio_five_live.m3u8": return "BBC Radio 5 Live"
    if filename == "bbc_radio_five_live_sports_extra.m3u8": return "BBC Radio 5 Live Sports Extra"
    if filename == "bbc_world_service.m3u8": return "BBC World Service"

    # if not found:
    return "Radio"

def current(sonos_room):
    # reset all the variables so we return a blank if it's not set by the function
    current_trackname = ""
    current_artist = ""
    current_album = ""
    current_image =""
    playing_status = ""

    # convert any spaces to url-suitable character
    sonos_room = sonos_room.replace(" ", "%20")

    # build URL
    url = "http://" + sonos_settings.sonos_http_api_address + ":" + sonos_settings.sonos_http_api_port + "/" + sonos_room + "/state"

    # download the raw json object and parse the json data
    try:
        data = requests.get(url)
    except requests.ConnectionError:
        print ("Error: http-sonos-api failed to answer; pausing 10 seconds to give it a chance to catch up")
        time.sleep (10)
        return "", "", "", "", "API error"

    data = requests.get (url)
    obj = json.loads(data.text)

    # extract relevant data
    playing_status = obj['playbackState']
    type_playing = obj['currentTrack']['type']

    # detect if its coming from Sonos radio, in which case forget that it's radio and pretend it's a normal track
    uri = obj['currentTrack']['uri']
    if uri.startswith('x-sonosapi-radio:sonos'):
        type_playing = "sonos_radio"

    if type_playing == "radio":
            
        if 'stationName' in obj['currentTrack']:
            # if Sonos has given us a nice station name then use that
            current_trackname = obj['currentTrack']['stationName']
        else:
            # if not then try to look it up (usually because its played from Alexa)
            current_trackname = str(find_unknown_radio_station_name(obj['currentTrack']['title']))
        
        current_artist = ""
        current_album = ""
        
        if 'absoluteAlbumArtUri' in obj['currentTrack']:
            current_image = obj['currentTrack']['absoluteAlbumArtUri']
        else:
            current_image = ""       

    if type_playing != "radio":
        current_trackname = obj['currentTrack']['title']
        if 'artist' in obj['currentTrack']: current_artist = obj['currentTrack']['artist']
        if 'album' in obj['currentTrack']: current_album = obj['currentTrack']['album']
        if 'absoluteAlbumArtUri' in obj['currentTrack']: current_image = obj['currentTrack']['absoluteAlbumArtUri']

    return current_trackname, current_artist, current_album, current_image, playing_status
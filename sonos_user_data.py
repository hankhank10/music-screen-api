# Note: this is not the file where you change your user settings for Sonos
# if you're looking for that then try sonos_settings.py
# sorry, I know it's confusingly named - but it's too late to change now!

import time
from urllib.parse import urljoin

import sonos_settings

WEBHOOK_TIMEOUT = 600   # 10 minutes


class SonosData():
    """Holds all data related to the chosen Sonos speaker."""

    def __init__(self, sonos_room, session):
        """Initialize the object."""
        self.last_poll = 0
        self.last_webhook = 0
        self.session = session
        self.room = sonos_room
        self.webhook_active = False

        self.trackname = ""
        self.artist = ""
        self.album = ""
        self.image = ""
        self.status = ""

    async def refresh(self, payload=None):
        """Refresh the Sonos media data with provided payload or a new get request."""
        if payload:
            if not self.webhook_active:
                print("Switching to webhook updates")
            self.last_webhook = time.time()
            self.webhook_active = True
            obj = payload
        else:
            self.last_poll = time.time()
            base_url = f"http://{sonos_settings.sonos_http_api_address}:{sonos_settings.sonos_http_api_port}"
            url = urljoin(base_url, f"{self.room}/state")

            try:
                async with self.session.get(url) as response:
                    obj = await response.json()
            except Exception as err:
                self.status = "API error"
                print(f"Error connecting to Sonos API: {err}")
                return

        try:
            self.status = obj['playbackState']
        except KeyError:
            print("Error: http-sonos-api object is missing playbackState")
            self.status = "API error"
            return

        if self.status == "PLAYING" and self.webhook_active:
            if self.last_poll - self.last_webhook > WEBHOOK_TIMEOUT:
                print("Webhook activity timed out, falling back to polling")
                self.webhook_active = False

        type_playing = obj['currentTrack']['type']

        # detect if its coming from Sonos radio, in which case forget that it's radio and pretend it's a normal track
        uri = obj['currentTrack']['uri']
        if uri.startswith('x-sonosapi-radio:sonos'):
            type_playing = "sonos_radio"

        if type_playing == "radio":

            if 'stationName' in obj['currentTrack']:
                # if Sonos has given us a nice station name then use that
                self.trackname = obj['currentTrack']['stationName']
            else:
                # if not then try to look it up (usually because its played from Alexa)
                self.trackname = str(find_unknown_radio_station_name(obj['currentTrack']['title']))

            self.artist = ""
            self.album = ""

            if 'absoluteAlbumArtUri' in obj['currentTrack']:
                self.image = obj['currentTrack']['absoluteAlbumArtUri']
            else:
                self.image = ""

        if type_playing != "radio":
            self.trackname = obj['currentTrack'].get('title', "")
            self.artist = obj['currentTrack'].get('artist', "")
            self.album = obj['currentTrack'].get('album', "")

            album_art_uri = obj['currentTrack'].get('albumArtUri')
            if album_art_uri and album_art_uri.startswith('http'):
                self.image = album_art_uri
            elif 'absoluteAlbumArtUri' in obj['currentTrack']:
                self.image = obj['currentTrack']['absoluteAlbumArtUri']


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

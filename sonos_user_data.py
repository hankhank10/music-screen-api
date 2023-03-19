"""
Helper class to retrieve and process data from `node-http-sonos-api`.
"""
from datetime import timedelta
import logging
import re
import time
from urllib.parse import urljoin
import sonos_settings

from aiohttp import ClientConnectorError


_LOGGER = logging.getLogger(__name__)

WEBHOOK_TIMEOUT = 130


class SonosData():
    """Holds all data related to the chosen Sonos speaker."""

    def __init__(self, api_host, api_port, sonos_room, session):
        """Initialize the object."""
        self.api_host = api_host
        self.api_port = api_port
        self.last_poll = 0
        self.last_webhook = 0
        self.previous_image_uri = None
        self.previous_track = None
        self.room = sonos_room
        self.session = session
        self.webhook_active = False
        self._speaker_uri = None
        self._track_is_new = True

        self.type = ""
        self.raw_trackname = ""
        self.trackname = ""
        self.artist = ""
        self.album = ""
        self.station = ""
        self.duration = 0
        self.image_uri = ""
        self.status = ""

        self.volume = 0
        self.repeat = ""
        self.shuffle = ""
        self.crossfade = ""

    @property
    def last_update(self):
        if self.last_webhook > self.last_poll:
            return self.last_webhook
        return self.last_poll

    def set_room(self, room):
        """Change the actively monitored room."""
        self.room = room
        _LOGGER.info("Monitoring room: %s", room)

    def get_speaker_uri(self, json_data):
        """Return the speaker's URL based on the state JSON."""
        if self._speaker_uri:
            return self._speaker_uri

        next_track_art = json_data['nextTrack'].get("absoluteAlbumArtUri", "")
        match = re.search("(^https?:\/\/.*:1400)\/getaa\?.*", next_track_art)
        if match:
            self._speaker_uri = match.group(1)
            _LOGGER.debug("URL for %s found: %s", self.room, self._speaker_uri)
            return self._speaker_uri

    def is_playing(self):
        """Return True if actively playing."""
        return self.status == "PLAYING"

    def is_track_new(self):
        """Return True if the track has changed since last update."""
        is_new = self._track_is_new
        self._track_is_new = False
        return is_new

    def set_track_info(self, payload):

        """Update attributes from the JSON payload. Returns new track_id or None."""
        self.raw_trackname = payload['currentTrack'].get('title', "")
        self.artist = payload['currentTrack'].get('artist', "")
        self.album = payload['currentTrack'].get('album', "")
        self.station = payload['currentTrack'].get('stationName', "")
        self.uri = payload['currentTrack'].get('uri', "")

        self.volume = payload.get('volume', "")
        self.repeat = payload['playMode'].get('repeat', "")
        self.shuffle = payload['playMode'].get('shuffle', "")
        self.crossfade = payload['playMode'].get('crossfade', "")

        if sonos_settings.artist_and_album_newlook :
           if self.raw_trackname.startswith("x-sonosapi-") :
              self.raw_trackname = self.station

           if self.artist == self.station and self.type == "radio" :
              if self.raw_trackname.count("~") : c = "~"
              elif self.raw_trackname.count("˗") : c = "˗"
              elif self.raw_trackname.count("*") : c = "*"
              elif self.raw_trackname.count("|") : c = "|"
              elif self.raw_trackname.count(" - ") : c = " - "
              elif self.raw_trackname.count(" / ") : c = " / "
              else : c = ""

              if c :
                 oldstr=self.raw_trackname.casefold()
                 splitstr = oldstr.split(c)
                 SplitStr = self.raw_trackname.split(c)
                 if self.raw_trackname.startswith("BR P|TYPE=SNG|") :
                    if self.raw_trackname == "BR P|TYPE=SNG|TITLE |ARTIST |ALBUM" :
                        if "bbc_radio" in self.uri :
                            self.raw_trackname = "BBC " + self.station
                        else :
                            self.raw_trackname = self.station
                        self.artist = ""
                    else : 
                        #self.artist = ' '.join(word[0].upper() + word[1:] for word in splitstr[3].split())[6:]
                        self.artist = SplitStr[3][7:]
                        #self.raw_trackname = ' '.join(word[0].upper() + word[1:] for word in splitstr[2].split())[5:]
                        self.raw_trackname = SplitStr[2][6:]
                    if c == "~" :
                        self.album = ' '.join(word[0].upper() + word[1:] for word in splitstr[2].split())
                    else :
                        self.album = ""
    #                    self.album = self.station
                 else :
                    self.artist = ' '.join(word[0].upper() + word[1:] for word in splitstr[0].split())
                    self.raw_trackname = ' '.join(word[0].upper() + word[1:] for word in splitstr[1].split())
                    if c == "~" :
                        self.album = ' '.join(word[0].upper() + word[1:] for word in splitstr[2].split())
                    else :
                        self.album = ""
    #                    self.album = self.station

        # Abort update if all data is empty
        if not any([self.album, self.artist, self.duration, self.station, self.raw_trackname]):
            _LOGGER.debug("No data returned by the API, skipping update")
            return None

        if self.type == "radio" and not self.station:
            # if not then try to look it up (usually because its played from Alexa)
            self.station = find_unknown_radio_station_name(self.raw_trackname)

        # Clear uninteresting tracknames
        if self.raw_trackname.startswith("x-sonosapi-") or self.raw_trackname.endswith(".m3u8"):
            self.trackname = ""
        else:
            self.trackname = self.raw_trackname


        track_id = self.artist
        if self.trackname:
            track_id += f" - {self.trackname}"
        if self.album:
            track_id += f" ({self.album})"
        if self.duration:
            track_id += f" - {timedelta(seconds=self.duration)}"
        if self.station:
            track_id += f" [{self.station}]"

        return track_id

    async def refresh(self, payload=None):
        """Refresh the Sonos media data with provided payload or a new get request."""
        if payload:
            if not self.webhook_active:
                _LOGGER.info("Switching to webhook updates")
            self.last_webhook = time.time()
            self.webhook_active = True
            obj = payload
        else:
            self.last_poll = time.time()
            base_url = f"http://{self.api_host}:{self.api_port}"
            url = urljoin(base_url, f"{self.room}/state")

            try:
                async with self.session.get(url) as response:
                    obj = await response.json()
            except ClientConnectorError as err:
                self.status = "API error"
                _LOGGER.error("Connection failed. Ensure `node-sonos-http-api` is running: (%s)", err)
                return
            except Exception as err:
                self.status = "API error"
                _LOGGER.exception("Error connecting to Sonos API: %s", err)
                return

        self.status = obj.get('playbackState', "API error")

        # Don't bother processing the payload unless media is actively playing
        if self.status != "PLAYING":
            return

        self.type = obj['currentTrack']['type']
        self.duration = obj['currentTrack']['duration']

        if "bluetooth:" in obj["currentTrack"]["uri"]:
            self.type = track_id = "Bluetooth"

        if self.type in ("line_in", "Bluetooth"):
            uri = obj['currentTrack']['uri']
            if uri.startswith('x-sonos-htastream:'):
                self.type = track_id = "TV"
            elif self.type != "Bluetooth":
                track_id = "Line-In"
            self.image_uri = None
            self.trackname = track_id
            self.artist = ""
            self.album = ""
            self.station = ""
        else:
            track_id = self.set_track_info(obj)

            if not track_id:
                return

            album_art_uri = obj['currentTrack'].get('albumArtUri', "")
            speaker_uri = self.get_speaker_uri(obj)
            if album_art_uri.startswith('http'):
                self.image_uri = album_art_uri
            elif speaker_uri and album_art_uri:
                self.image_uri = f"{speaker_uri}{album_art_uri}"
            else:
                self.image_uri = obj['currentTrack'].get('absoluteAlbumArtUri', "")

        if track_id != self.previous_track:
            _LOGGER.info("New track: %s", track_id)
        elif self.image_uri != self.previous_image_uri:
            _LOGGER.debug("Updated image URI: %s", self.image_uri)
        else:
            return

        self.previous_image_uri = self.image_uri
        self.previous_track = track_id
        self._track_is_new = True

        if self.webhook_active and (self.last_poll - self.last_webhook > WEBHOOK_TIMEOUT):
            _LOGGER.warning("Webhook activity timed out, falling back to polling")
            self.webhook_active = False



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

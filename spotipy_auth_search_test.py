#This utility can be used to help troubleshoot authentication of your Spotify API credentials and searching Spotify using spotipy
# Run using python3 spotipy_auth_search_test.py 

import re
import sys
try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    import spotipy.util as util
except:
    print("ERROR: You need to install spotipy to use this script, bash command is 'pip install spotipy'")

try:
    import sonos_settings
except ImportError:
    print("ERROR: Config file not found. Copy 'sonos_settings.py.example' to 'sonos_settings.py' before you edit. You can do this with the command: cp sonos_settings.py.example sonos_settings.py")
    sys.exit(1)

spotify_client_id = getattr(sonos_settings, "spotify_client_id", None)
spotify_client_secret = getattr(sonos_settings, "spotify_client_secret", None)
spotify_market = getattr(sonos_settings, "spotify_market", None)

if spotify_client_id and spotify_client_secret:
    artist = input("Enter Artist: ")
    artist = re.sub("`|´|’|'", "", artist)
    trackname = input("Enter Song Name: ")
    trackname = re.sub("`|´|’|'", "", trackname)

    try:
        client_credentials_manager = SpotifyClientCredentials(spotify_client_id, spotify_client_secret)
        spotify_auth_success = True
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        print("INFO: Spotify Authorisation Successful")

    except Exception as err:
        spotify_auth_success = False
        print("ERROR: Spotify Authorisation Failed, please review your 'sonos_settings.py' to ensure your Spotify API credentials are correct")
        sys.exit(1)

    if spotify_auth_success:
        track_results = spotify.search(q="artist:" + artist + " track:" + trackname, type="track", limit=1, offset=0, market=spotify_market)
        artist_results = spotify.search(q="artist:" + artist, type="artist", limit=1, offset=0, market=spotify_market)

        if track_results['tracks']['total'] != 0:
            track_results = track_results['tracks']['items'][0]  # Find top result
            uri = track_results['uri']
            print("The Spotify URI for your track is: " + uri)
            albumart_uri = track_results['album']['images'][0]['url']
            print("The Spotify album art URI for your track is: " + albumart_uri)
        else:
            print("INFO: Spotify track search returned no results")

        if artist_results['artists']['total'] != 0:
            artist_results = artist_results['artists']['items'][0]  # Find top result
            artist_uri = artist_results['uri']
            print("The Spotify URI for your artist is: " + artist_uri)
            artistArt_uri = artist_results['images'][0]['url']
            print("The Spotify artist art URI for your track is: " + artistArt_uri)
        else:
            print("INFO: Spotify artist and song title search returned no results")
else:
    print("ERROR: No client ID or Secret in 'sonos_settings.py' file")

# this is the demaster script which removes nonsense like "Remastered" and "Live at" from track names
# latest can be downloaded from https://github.com/hankhank10/demaster

import requests

# application settings
api_base_url = 'http://demaster.hankapi.com/demaster?format=simple&long_track_name='

# set user settings
offline_only_mode = False

def strip_name_offline(full_song_name):

    text_to_parse = full_song_name
    lower_text_to_parse = text_to_parse.lower

    offending_text = [
        '- Remast',
        '(Remast',
        '- Live ',
        '(Live at',
        '- Mono / Remast',
        '- From '
        ]

    for x in range (1990,2025):
        new_offending_text = '- ' + str(x) + ' Remast'
        offending_text.append (new_offending_text)

    for x in range (1990,2025):
        new_offending_text = '(' + str(x) + ' Remast'
        offending_text.append (new_offending_text)

    for item in offending_text:
        if text_to_parse.find(item) >=0:
            split_out_text = text_to_parse.partition (item)
            return split_out_text[0]

    return full_song_name

def strip_name_api(full_song_name):
    
    request_error = False
    api_url = api_base_url + full_song_name
    print ("Checking API at "+  api_url)

    try:
        r = requests.get(api_url)
    except requests.ConnectionError:
        short_song_name = "##Error##"
        request_error = True
        
    if r.status_code != 200:
        request_error = True
        short_song_name = "##Error##"

    if request_error is False:
        short_song_name = r.text
        print ("Returning text")

    return short_song_name

def strip_name(full_song_name, offline_only_mode=False):
    if offline_only_mode == True:
        # If we are running in offline-only mode then just parse locally
        print ("Just using offline as we are in offline_only_mode")
        return strip_name_offline(full_song_name)

    # If not, try online API
    online_api_response = strip_name_api(full_song_name)
    
    # if there is a connection error, try offline instead
    if online_api_response == "##Error##":
        print ("Online API failed, returning offline version")
        online_api_response = strip_name_offline(full_song_name)

    # return whatever we have generated
    return online_api_response
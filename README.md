# Last.fm user data API

Simple python script which pulls down user data from last.fm

This information is publicly available for all users so there is no need to be logged in to last.fm. You also don't need to change the public key in the code.

# Installation

Clone or download lastfm_user_data.py into your project folder.  Add the following to the start of your script:

```include lastfm_user_data```

# Functionality
## Pull static user data

The first function returns static data about a specific user, for instance the following command which will return the user's home page URL:

```lastfm_user_data.static_data(requested_username, "url")```

It will return any of the data made available by the API if requested. You can see an example list of which static fields are available [here](
http://ws.audioscrobbler.com/2.0/?method=user.getinfo&user=test&api_key=079a7d64ea52c358ad4f0afbe2f900b3&format=json)

## Return play counts 

.playcount returns an integer of the number of tracks played by that user over a specific period:

```lastfm_user_data.playcount(requested_username, "") # this defaults to forever
lastfm_user_data.playcount(requested_username, "this_year")
lastfm_user_data.playcount(requested_username, "this_month")
lastfm_user_data.playcount(requested_username, "this_week")
lastfm_user_data.playcount(requested_username, "today")
lastfm_user_data.playcount(requested_username, "last30days")
lastfm_user_data.playcount(requested_username, "last7days")
lastfm_user_data.playcount(requested_username, "last24hours")
lastfm_user_data.playcount(requested_username, "last_hour")
```

## Return last track played

.lastplayed returns four text variables: the name of the track, artist, album and the album art image url.

# Example

There is an example (example.py) provided which calls and outputs the playcount for a specified user.

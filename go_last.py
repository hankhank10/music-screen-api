import time # needed to delay x seconds between checks
import lastfm_user_data # the api which pulls the lastfm data
import sys # needed to pull command line arguments
import ink_printer # does the printing to ink

# set globals
previous_track_name = ""

# define variables
display_stats = False # can be set to detailed or summary

# set the frequency based on whether we are pulling detail or not - needs to be longer if we are
if display_stats == True:
    frequency = 10  # number of seconds between checks of the API
if display_stats == False:
    frequency = 1  # number of seconds between checks of the API

# check if a command line argument has been passed to identify the user, if not ask
if len(sys.argv) == 1:
    # if no username passed then ask the user to input a username
    requested_username = input ("Enter a last.fm username to check the playcount of >>>  ")
else:
    # if command line includes username then set it to that
    requested_username = str(sys.argv[1])
    
# loop to refresh every [frequency] seconds
while True:
    # gather last played information from lastfm api
    print ("Checking API for last played: ", end = '')
    lastplayed_track, lastplayed_artist, lastplayed_album, lastplayed_image = lastfm_user_data.lastplayed (requested_username)
    
    # see if there is new data to display
    if lastplayed_track == previous_track_name:  #check if the track name is same as what we displayed last time
        print ("no change to data - not refreshing")
    else:
        print ("new data found from api - refreshing screen")

        if display_stats == True:
            # find more info
            played_all_time = lastfm_user_data.playcount(requested_username, "") + " all time"
            played_this_year = lastfm_user_data.playcount(requested_username, "this_year") + " this year"
            played_this_month = lastfm_user_data.playcount(requested_username, "this_month") + " this month"
            played_this_week = lastfm_user_data.playcount(requested_username, "this_week") + " this week"
            played_today = lastfm_user_data.playcount(requested_username, "today") + " today"
        
        if display_stats == True:
            # print to the ink
            ink_printer.print_text_to_ink (lastplayed_track, lastplayed_artist, lastplayed_album, played_all_time, played_this_year, played_this_month, played_this_week, played_today)

        if display_stats == False:
            #print to the ink
            ink_printer.print_text_to_ink (lastplayed_track, lastplayed_artist, lastplayed_album)

        # keep a record of the previous track name to see if it changes next time
        previous_track_name = lastplayed_track

    print ("Waiting " + str(frequency) + " seconds")
    time.sleep (frequency)

# This file is for use with the Pimoroni inky wHAT display
# it integrates with your local Sonos sytem to display what is currently playing

import time # needed to delay x seconds between checks
import sonos_user_data # the api which pulls the lastfm data
import sys # needed to pull command line arguments
import ink_printer # does the printing to ink

import sonos_settings
import demaster

# user variables
if sonos_settings.pi_zero:
    frequency = 1  # number of seconds between checks of the API
    sleep_mode_sheep_to_count = 20
else:
    frequency = 0.5
    sleep_mode_sheep_to_count = 10
sleep_mode_enabled = True
sleep_mode_frequency = 5
sleep_mode_output = "logo" # can also be "blank"

# set globals to nil at the start of the script
previous_track_name = ""
sleep_mode_sleeping = False
number_of_sheep_counted = 0

# check if a command line argument has been passed to identify the user, if not ask
if len(sys.argv) == 1:
    # if no room name passed then ask the user to input a room name
    sonos_room = input ("Enter a Sonos room name >>>  ")
else:
    # if command line includes username then set it to that
    sonos_room = str(sys.argv[1])
    print (sonos_room)
    
if sonos_settings.pi_zero:
    print ("Pausing for 60 seconds on startup to let pi zero catch up")
    time.sleep (60)

# loop to refresh every [frequency] seconds
while True:
    # gather last played information from Sonos api
    print ("Checking API for last played: ", end = '')
    current_track, current_artist, current_album, current_image, play_status = sonos_user_data.current (sonos_room)
    
    # check if anything is playing
    if play_status == "PLAYING":
        # wake from sleep mode if we're in it
        sleep_mode_sleeping = False
        number_of_sheep_counted = 0
       
        # see if there is new data to display
        if current_track == previous_track_name:  #check if the track name is same as what we displayed last time
            print ("no change to data - not refreshing")
        else:
            print ("new data found from api - refreshing screen")
            previous_track_name = current_track

            # demaster the track name if set to do so
            if sonos_settings.demaster == True:
                current_track = demaster.strip_name (current_track)

            #print to the ink
            ink_printer.print_text_to_ink (current_track, current_artist, current_album)

            # keep a record of the previous track name to see if it changes next time
    else:
        # nothing is playing right now

        # ... but check whether this is just a momentary pause
        if number_of_sheep_counted <= sleep_mode_sheep_to_count:
            # not enough sleep counted yet to go to sleep - add one
            number_of_sheep_counted = number_of_sheep_counted + 1
            print ("Counting " + str(number_of_sheep_counted) + " sheep")
        
        else:
            # if enough sheep have been counted then put into sleep mode
        
            # check if the screen is already blank, if not make it blank
            if sleep_mode_sleeping == False:
                # set the screen depending on settings
                if sleep_mode_output == "logo":
                    if sonos_settings.inverted:
                        ink_printer.show_image('/home/pi/music-screen-api/sonos-inky-inverted.png')
                    else:
                        ink_printer.show_image('/home/pi/music-screen-api/sonos-inky.png')
                else:
                    ink_printer.blank_screen()
            
            # if going to sleep is enabled then put it into sleep mode
            if sleep_mode_enabled == True:
                sleep_mode_sleeping = True
                previous_track_name = ""
                print ("Nothing playing, sleep mode")

    if sleep_mode_sleeping == False:
        time.sleep (frequency)
        print ("Waiting " + str(frequency) + " seconds")
    else:
        time.sleep (sleep_mode_frequency)
        print ("Waiting " + str(frequency) + " seconds as in sleep mode")

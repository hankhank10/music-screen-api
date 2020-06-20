from inky import InkyWHAT
from PIL import Image, ImageFont, ImageDraw, ImageOps
from font_source_serif_pro import SourceSerifProSemibold
from font_source_sans_pro import SourceSansProSemibold
from font_hanken_grotesk import HankenGroteskBold, HankenGroteskMedium
import argparse

# user variable settings
rotate = 0  # this can only be 0 or 180 depending on whether you want it upside down or not
inverted = True  # back to black

# Set amount of padding
top_padding = 15
top_padding_extra_for_radio = 75  #if playing radio then there is no artist or album, so makes sense to put the data we do have more centrally
left_padding = 10
line_padding = 5

#set font sizes for detail
detail_fontsize_for_track = 30
detail_fontsize_for_artist = 24
detail_fontsize_for_album = 24
detail_fontsize_for_gap_before_stats = 34
detail_fontsize_for_stats = 20

#set font sizes for summary
summary_top_gap = 10
summary_fontsize_for_track = 45
summary_gap_between_track_and_artist = 50
summary_fontsize_for_artist = 27
summary_gap_between_artist_and_album = 20
summary_fontsize_for_album = 27

# Set up the correct display and scaling factors
inky_display = InkyWHAT("black")
inky_display.set_border(inky_display.BLACK)
x = 0
y = 0
if inverted == True:
    foreground_colour = inky_display.WHITE
    background_colour = inky_display.BLACK
else:  
    foreground_colour = inky_display.BLACK
    background_colour = inky_display.WHITE

# find the size of the display
display_width = inky_display.WIDTH
display_height = inky_display.HEIGHT

# this function prints a new line to the image
def write_new_line(text_to_write, font_size, alignment = "center", reflow=False):
    global line_y
    
    # set font - you can change this to others defined at the top of the script if you like
    font = ImageFont.truetype(SourceSansProSemibold, font_size)

    # work out the size of the text
    text_width, text_height = font.getsize(text_to_write)

    # set the x based on alignment
    if alignment == "center":
        # and set the x to start so that is appears in the middle
        line_x = (display_width - text_width) / 2
    if alignment == "left":
        line_x = left_padding

    # write text to the canvas
    draw.text((line_x, line_y), text_to_write, foreground_colour, font=font)
    print ("Printing to ink >>> " + text_to_write)
    
    # move to next line
    line_y = line_y + text_height + line_padding

def print_text_to_ink(track, artist, album, stat1 = "", stat2 = "", stat3 = "", stat4 = "", stat5 =""):
    global line_y
    line_y = 0

    if (rotate is not 0) and (rotate is not 180):
        # quits out with error if you ignored the comment above
        exit ("Rotation can only be 0 or 180")

    # reset the y start point to the top
    line_y = top_padding

    # create a new canvas to draw on
    global img
    global draw
    
    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
    draw = ImageDraw.Draw(img)

    for y in range(0, inky_display.HEIGHT):
        for x in range(0, inky_display.WIDTH):
            img.putpixel((x, y), background_colour)

    # work out if we are in detailed mode or summary mode based on whether we have been passed stat1 or not
    if stat1 is not "":
        # we are in detailed mode
        # write the various lines to the image
        write_new_line (track, detail_fontsize_for_track, "center")
        write_new_line (artist, detail_fontsize_for_artist, "center")
        write_new_line (album, detail_fontsize_for_album, "center")
        write_new_line (" ", detail_fontsize_for_gap_before_stats, "left")
        write_new_line (stat1, detail_fontsize_for_stats, "left")
        write_new_line (stat2, detail_fontsize_for_stats, "left")
        write_new_line (stat3, detail_fontsize_for_stats, "left")
        write_new_line (stat4, detail_fontsize_for_stats, "left")
        write_new_line (stat5, detail_fontsize_for_stats, "left")

    if stat2 == "":
        # we are in summary mode

        # sometimes the track name is too long to show so we need to reflow it - work out how to do that here
        # set font for track
        font = ImageFont.truetype(SourceSansProSemibold, summary_fontsize_for_track)

        # split the track into lines
        words = track.split (" ")
        reflowed = ""
        line_length = 0

        for i in range(len(words)):
            word = words[i] + " "
            word_length = font.getsize(word)[0]
            line_length += word_length

            if line_length < display_width:
                reflowed += word
            else:
                line_length = word_length
                reflowed = reflowed[:-1] + "\n " + word
        
        track = reflowed

        # work out how many lines in the track string
        number_of_track_lines = len(track.splitlines())
        print ("Track name is split over " + str(number_of_track_lines) + " lines")

        # write the various lines to the image
        write_new_line (" ", summary_top_gap)

        if artist == "" and album == "":
            write_new_line (" ", top_padding_extra_for_radio)

        for line in track.splitlines():
            write_new_line (line, summary_fontsize_for_track, "center", True)       

        write_new_line (" ", summary_gap_between_track_and_artist)
        write_new_line (artist, summary_fontsize_for_artist)
        write_new_line (" ", summary_gap_between_artist_and_album)
        write_new_line (album, summary_fontsize_for_album)
    
    if rotate == 180:
        img = img.rotate(180)

    # display the image on the screen
    
    inky_display.set_image(img)
    inky_display.show()

def blank_screen():
    print ("Blank")   
    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
    draw = ImageDraw.Draw(img)
    inky_display.set_image(img)
    inky_display.show()
    line_y = 0

def show_image(img_file):
    # Open the image file that was passed in from the argument
    img = Image.open(img_file)

    # Get the width and height of the image
    w, h = img.size

    # Calculate the new height and width of the image
    h_new = 300
    w_new = int((float(w) / h) * h_new)
    w_cropped = 400

    # Resize the image with high-quality resampling
    img = img.resize((w_new, h_new), resample=Image.LANCZOS)

    # Calculate coordinates to crop image to 400 pixels wide
    x0 = (w_new - w_cropped) / 2
    x1 = x0 + w_cropped
    y0 = 0
    y1 = h_new

    # Crop image
    img = img.crop((x0, y0, x1, y1))

    # Convert the image to use a white / black / red colour palette
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette((255, 255, 255, 0, 0, 0, 255, 0, 0) + (0, 0, 0) * 252)

    img = img.convert("RGB").quantize(palette=pal_img)

    #if inverted == True:
    #img = ImageOps.invert(img)

    # Display the final image on Inky wHAT
    inky_display.set_image(img)
    inky_display.show()



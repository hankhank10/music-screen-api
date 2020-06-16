# this is the demaster script which removes nonsense like "Remastered" and "Live at" from track names
# latest can be downloaded from https://github.com/hankhank10/demaster

def strip_name(full_song_name):

    text_to_parse = full_song_name
    lower_text_to_parse = text_to_parse.lower

    offending_text = [
        '- Remast',
        '(Remast',
        '- Live at',
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

from ac2.plugins.metadata import MetadataDisplay

from inky import InkyWHAT

from PIL import Image, ImageFont, ImageDraw
from font_source_serif_pro import SourceSerifProSemibold
from font_source_sans_pro import SourceSansProSemibold

import requests
import logging
import os
import inky

logger = logging.getLogger("inkyDisplay")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/var/log/inky_display.log')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)


class InkyDisplay(MetadataDisplay):

    def __init__(self, url=None, request_type="json"):
        super().__init__()
        logger.info("InkyDisplay started")
        self.request_type = request_type
        self.url = url
        self.metadata = None

    def notify(self, metadata):
        if not metadata.sameSong(self.metadata):
            if metadata.title and metadata.artist:
                self.metadata = metadata
                logger.info(f"Changed to: {self.metadata}")

                colour = "red"

                # Set up the correct display and scaling factors
                inky_display = InkyWHAT(colour)
                inky_display.set_border(inky_display.WHITE)

                w = inky_display.WIDTH
                h = inky_display.HEIGHT

                # Create a new canvas to draw on

                img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
                draw = ImageDraw.Draw(img)

                # Load the fonts

                font_size = 24

                author_font = ImageFont.truetype(SourceSerifProSemibold, font_size)
                quote_font = ImageFont.truetype(SourceSansProSemibold, font_size)

                # The amount of padding around the quote. Note that
                # a value of 30 means 15 pixels padding left and 15
                # pixels padding right.
                #
                # Also define the max width and height for the quote.

                padding = 50
                max_width = w - padding
                max_height = h - padding - author_font.getsize("ABCD ")[1]

                below_max_length = False

                # Only pick a quote that will fit in our defined area
                # once rendered in the font and size defined.

                while not below_max_length:
                    # person = random.choice(people)           # Pick a random person from our list
                    # quote = wikiquotes.random_quote(person, "english")
                    person = self.metadata.artist
                    quote = self.metadata.title
                    reflowed = self._reflow_quote(quote, max_width, quote_font)
                    p_w, p_h = quote_font.getsize(reflowed)  # Width and height of quote
                    p_h = p_h * (reflowed.count("\n") + 1)   # Multiply through by number of lines

                    if p_h < max_height:
                        below_max_length = True              # The quote fits! Break out of the loop.

                    else:
                        return
                # x- and y-coordinates for the top left of the quote

                quote_x = (w - max_width) / 2
                quote_y = ((h - max_height) + (max_height - p_h - author_font.getsize("ABCD ")[1])) / 2

                # x- and y-coordinates for the top left of the author

                author_x = quote_x
                author_y = quote_y + p_h

                author = "- " + person

                # Draw red rectangles top and bottom to frame quote

                draw.rectangle((padding / 4, padding / 4, w - (padding / 4), quote_y - (padding / 4)), fill=inky_display.RED)
                draw.rectangle((padding / 4, author_y + author_font.getsize("ABCD ")[1] + (padding / 4) + 5, w - (padding / 4), h - (padding / 4)), fill=inky_display.RED)

                # Add some white hatching to the red rectangles to make
                # it look a bit more interesting

                hatch_spacing = 12

                for x in range(0, 2 * w, hatch_spacing):
                    draw.line((x, 0, x - w, h), fill=inky_display.WHITE, width=3)

                # Write our quote and author to the canvas

                draw.multiline_text((quote_x, quote_y), reflowed, fill=inky_display.BLACK, font=quote_font, align="left")
                draw.multiline_text((author_x, author_y), author, fill=inky_display.RED, font=author_font, align="left")

                # Display the completed canvas on Inky wHAT

                inky_display.set_image(img.rotate(180))
                inky_display.show()


    def _reflow_quote(self, quote, width, font):
        # This function will take a quote as a string, a width to fit
        # it into, and a font (one that's been loaded) and then reflow
        # that quote with newlines to fit into the space required.
        words = quote.split(" ")
        reflowed = '"'
        line_length = 0

        for i in range(len(words)):
            word = words[i] + " "
            word_length = font.getsize(word)[0]
            line_length += word_length

            if line_length < width:
                reflowed += word
            else:
                line_length = word_length
                reflowed = reflowed[:-1] + "\n  " + word

        reflowed = reflowed.rstrip() + '"'

        return reflowed
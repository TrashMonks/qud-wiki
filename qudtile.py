# https://stackoverflow.com/questions/3752476/python-pil-replace-a-single-rgba-color

from pathlib import Path

from PIL import Image, ImageQt

QUD_COLORS = {'r': (166, 74, 46),  # dark red
              'R': (215, 66, 0),  # bright red
              'w': (152, 135, 95),  # brown
              'W': (207, 192, 65),  # yellow
              'c': (64, 164, 185),  # dark cyan
              'C': (119, 191, 207),  # bright cyan
              'b': (0, 72, 189),  # dark blue
              'B': (0, 150, 255),  # bright blue
              'g': (0, 148, 3),  # dark green
              'G': (0, 196, 32),  # bright green
              'm': (177, 84, 207),  # dark magenta
              'M': (218, 91, 214),  # bright magenta
              'y': (177, 201, 195),  # bright grey
              'Y': (255, 255, 255),  # white
              'k': (15, 59, 58),  # black
              'K': (21, 83, 82),  # dark grey
              'o': (241, 95, 34),
              'O': (233, 159, 16),
              }

# From modding wiki but wrong?
# QUD_COLORS = {'r': (128, 0, 0),  # dark red
#               'R': (255, 0, 0),  # bright red
#               'w': (153, 51, 0),  # brown
#               'W': (255, 255, 0),  # yellow
#               'c': (51, 204, 204),  # dark cyan
#               'C': (0, 255, 255),  # bright cyan
#               'b': (0, 0, 128),  # dark blue
#               'B': (51, 102, 255),  # bright blue
#               'g': (0, 128, 0),  # dark green
#               'G': (0, 255, 0),  # bright green
#               'm': (128, 0, 128),  # dark magenta
#               'M': (255, 0, 255),  # bright magenta
#               'y': (192, 192, 192),  # bright grey
#               'Y': (255, 255, 255),  # white
#               'k': (0, 0, 0),  # black
#               'K': (128, 128, 128),  # dark grey
#               }
QUD_REG_COLOR = (0, 0, 0, 255)
QUD_DETAIL_COLOR = (255, 255, 255, 255)
QUD_VIRIDIAN = (15, 64, 63, 255)

tiles_dir = Path('tiles')
blank_image = Image.new('RGBA', (16, 24), color=(0, 0, 0, 255))
# index keys are like "creatures/caste_flipped_22.bmp" as in XML
image_cache = {}


class QudTile:
    """Class to load and color a Qud tile."""
    def __init__(self, filename, tilecolor, detailcolor):
        if tilecolor is None:
            tilecolor = 'y'
        else:
            if '^' in tilecolor:
                # this seems to be for setting background
                tilecolor = tilecolor.split('^')[0]
            tilecolor = tilecolor.strip('&')
        if detailcolor is None:
            detailcolor = 'Y'
        else:
            detailcolor = detailcolor.strip('&')
        if filename in image_cache:
            image = image_cache[filename]
        else:
            fullpath = tiles_dir / filename
            try:
                image = Image.open(fullpath)
            except:
                print("Couldn't load tile at " + str(fullpath.absolute()))
                image = blank_image
            image_cache[filename] = image

        for y in range(image.height):
            for x in range(image.width):
                px = image.getpixel((x, y))
                if px == QUD_REG_COLOR:
                    image.putpixel((x, y), QUD_COLORS[tilecolor])
                elif px == QUD_DETAIL_COLOR:
                    image.putpixel((x, y), QUD_COLORS[detailcolor])
                else:
                    image.putpixel((x, y), QUD_VIRIDIAN)
        self.image = image
        self.qtimage = ImageQt.ImageQt(image)

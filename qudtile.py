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

TILE_COLOR = (0, 0, 0, 255)
DETAIL_COLOR = (255, 255, 255, 255)
QUD_VIRIDIAN = (15, 64, 63, 255)

tiles_dir = Path('Textures')
blank_image = Image.new('RGBA', (16, 24), color=(0, 0, 0, 0))
blank_qtimage = ImageQt.ImageQt(blank_image)
# index keys are like "creatures/caste_flipped_22.bmp" as in XML
image_cache = {}


class QudTile:
    """Class to load and color a Qud tile."""
    def __init__(self, filename, colorstring, tilecolor, detailcolor):
        self.filename = filename
        if tilecolor is None:
            tilecolor = colorstring
        if tilecolor is None:
            self.tilecolor = QUD_COLORS['y']
        else:
            if '^' in tilecolor:
                # TODO: this seems to be for setting background
                tilecolor = tilecolor.split('^')[0]
            self.tilecolor = QUD_COLORS[tilecolor.strip('&')]
        if detailcolor is None:
            self.detailcolor = QUD_COLORS['k']
        else:
            self.detailcolor = QUD_COLORS[detailcolor.strip('&')]
        if filename in image_cache:
            self.image = image_cache[filename].copy()
            self.color_image()
        else:
            fullpath = tiles_dir / filename
            try:
                self.image = Image.open(fullpath)
                self.color_image()
            except FileNotFoundError:
                self.image = blank_image
            image_cache[filename] = self.image
        self.qtimage = ImageQt.ImageQt(self.image)

    def color_image(self):
        for y in range(self.image.height):
            for x in range(self.image.width):
                px = self.image.getpixel((x, y))
                if px == TILE_COLOR:
                    self.image.putpixel((x, y), self.tilecolor)
                elif px == DETAIL_COLOR:
                    self.image.putpixel((x, y), self.detailcolor)
                elif px[3] == 0:
                    self.image.putpixel((x, y), QUD_VIRIDIAN)
                    pass  # fully transparent
                else:
                    # uncomment for debugging of extra tile colors
                    # print(self.filename, self.tilecolor, self.detailcolor, px)
                    pass
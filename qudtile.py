# https://stackoverflow.com/questions/3752476/python-pil-replace-a-single-rgba-color
import io
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
tricolor_image_cache = set()
bad_tile_color = set()
bad_detail_color = set()
uses_details = set()


class QudTile:
    """Class to load and color a Qud tile."""
    def __init__(self, filename, colorstring, raw_tilecolor, raw_detailcolor, qudname):
        self.blacklisted = False  # set True if problems with tile generation encountered
        self.filename = filename
        self.raw_tilecolor = raw_tilecolor
        self.raw_detailcolor = raw_detailcolor
        self.qudname = qudname
        if raw_tilecolor is None:
            raw_tilecolor = colorstring  # fall back to text mode color
        if raw_tilecolor is None:
            self.tilecolor = QUD_COLORS['y']  # render in white
        else:
            if '^' in raw_tilecolor:
                # TODO: this seems to be for setting background
                raw_tilecolor = raw_tilecolor.split('^')[0]
            raw_tilecolor = QUD_COLORS[raw_tilecolor.strip('&')]
            self.tilecolor = raw_tilecolor
        if filename.lower().startswith('assets_content_textures'):
            # repair bad access paths
            filename = filename[24:]
            filename = filename.replace('_', '/', 1)
        if raw_detailcolor is None or raw_detailcolor == 'k':
            # self.detailcolor = QUD_COLORS['k']  # on-ground rendering
            self.detailcolor = (0, 0, 0)  # in-inventory rendering (more detail)
            bad_detail_color.add(self.qudname)
        else:
            self.detailcolor = QUD_COLORS[raw_detailcolor.strip('&')]
        if filename in image_cache:
            self.image = image_cache[filename].copy()
            self._color_image()
        else:
            fullpath = tiles_dir / filename
            try:
                self.image = Image.open(fullpath)
                image_cache[filename] = self.image.copy()
                self._color_image()
            except FileNotFoundError:
                print(f'Couldn\'t render tile for {self.qudname}: {filename} not found')
                self.blacklisted = True
                self.image = blank_image
        self.qtimage = ImageQt.ImageQt(self.image)

    def _color_image(self):
        for y in range(self.image.height):
            for x in range(self.image.width):
                px = self.image.getpixel((x, y))
                if px == TILE_COLOR:
                    self.image.putpixel((x, y), self.tilecolor)
                elif px == DETAIL_COLOR:
                    self.image.putpixel((x, y), self.detailcolor)
                    uses_details.add(self.qudname)
                elif px[3] == 0:
                    pass  # fully transparent
                else:
                    if self.qudname in tricolor_image_cache:
                        pass
                    else:
                        tricolor_image_cache.add(self.qudname)
                        self.blacklisted = True
                        # print(f"No tile will be generated for {self.qudname} because of color {px}")

    def get_big_image(self):
        """Draw the 160x240 image for the wiki."""
        return self.image.resize((160, 240))

    def get_big_qtimage(self):
        """Draw the 160x240 image for the explorer."""
        return ImageQt.ImageQt(self.get_big_image())

    def get_big_bytesio(self):
        """Get a BytesIO representation of a PNG encoding of the big image.

        Used for uploading to the wiki."""
        png_b = io.BytesIO()
        self.get_big_image().save(png_b, format='png')
        return png_b

    def get_big_bytes(self):
        """Return the bytes representation of big self in PNG format."""
        bytesio = self.get_big_bytesio()
        bytesio.seek(0)
        return bytesio.read()

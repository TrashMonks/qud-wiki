from PySide6.QtCore import QDir
from PySide6.QtGui import QFontDatabase
from hagadias.helpers import parse_qud_colors
import re


def displayname_to_wiki(phrase: str):
    """Convert display names from the new color templating format to usage of
    the wiki's {{Qud shader}} template.

    See hagadias.helpers.parse_qud_colors for details of the new in-game
    coloring templates.

    {{Qud shader}} syntax: https://wiki.cavesofqud.com/Template:Qud_shader/doc
    Example: {{Qud shader|text=Stopsvalinn|colors=R-r-K-y-Y|type=sequence|unbolded=true}}"""
    parsed = parse_qud_colors(phrase)
    output = []
    for text, shader in parsed:
        if shader is None:
            output.append(text)
        elif re.search(r'^[A-z](?:-[A-z])* [A-z]+$', shader) is not None:
            # shader with arguments - matches things like 'W-w sequence',
            # 'b-B-Y-Y-Y-Y-Y-Y-B-b alternation', or 'C sequence'. Previously we just checked for a
            # space, but that unintentionally captured multi-word shader names like 'palladium mesh'
            colors, _type = shader.split(' ')
            template = '{{Qud shader|text={{(}}' + text + '{{)}}|colors=' + colors + '|type=' \
                       + _type + '}}'  # text surrounded in {} to preserve whitespace
            output.append(template)
        else:
            # plain shader
            template = '{{Qud shader|' + shader + '|{{(}}' + text + '{{)}}}}'
            output.append(template)
    return ''.join(output)


def load_fonts_from_dir(directory):
    """Loads .ttf files from the specified directory and returns their font names as a set."""
    families = set()
    for fi in QDir(directory).entryInfoList(["*.ttf"]):
        _id = QFontDatabase.addApplicationFont(fi.absoluteFilePath())
        families |= set(QFontDatabase.applicationFontFamilies(_id))
    return families

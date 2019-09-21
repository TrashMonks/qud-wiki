"""Functionality for loading the Qud object blueprint XML into a tree of QudObjects.

For on-demand access to individual Qud objects by name, use the `qindex` from qudobject.py."""

import re
import sys
import time

# Force Python XML parser
sys.modules['_elementtree'] = None
from xml.etree import ElementTree as ET  # noqa E402

from qudobject_wiki import QudObjectWiki  # noqa E402

# Objects must still register themselves in the qindex because they need access to their parent by
# name during creation for inheritance calculations.
qindex = {}  # fast lookup of name->QudObject


class LineNumberingParser(ET.XMLParser):
    """An alternate parser for ElementTree that captures information about the source from the
    underlying expat parser."""

    def _start(self, *args, **kwargs):
        # Here we assume the default XML parser which is expat
        # and copy its element position attributes into output Elements
        element = super(self.__class__, self)._start(*args, **kwargs)
        element._start_line_number = self.parser.CurrentLineNumber
        element._start_column_number = self.parser.CurrentColumnNumber
        element._start_byte_index = self.parser.CurrentByteIndex
        return element

    def _end(self, *args, **kwargs):
        element = super(self.__class__, self)._end(*args, **kwargs)
        element._end_line_number = self.parser.CurrentLineNumber
        element._end_column_number = self.parser.CurrentColumnNumber
        element._end_byte_index = self.parser.CurrentByteIndex
        return element


def repair_invalid_chars(contents):
    """Return a version of an XML file with invalid control characters substituted."""
    ch_re = re.compile("&#11;")
    contents = re.sub(ch_re, '♂', contents)
    ch_re = re.compile("&#15;")
    contents = re.sub(ch_re, '☼', contents)
    return contents


def repair_invalid_linebreaks(contents):
    """Return a version of an XML file with invalid line breaks replaced with XML line breaks."""
    pat_linebreaks = r"^\s*<[^!][^>]*\n.*?>"
    match = re.search(pat_linebreaks, contents, re.MULTILINE)
    while match:
        before = match.string[:match.start()]
        fixed = match.string[match.start():match.end()].replace('\n', '&#10;')
        after = match.string[match.end():]
        contents = before + fixed + after
        match = re.search(pat_linebreaks, contents, re.MULTILINE)
    return contents


def load(path):
    """Load ObjectBlueprints.xml from the specified filepath and return a reference to the root."""
    with open(path, 'r', encoding='utf-8') as f:
        contents = f.read()
    # Do some repair of invalid XML:
    # First, replace some invalid control characters intended for CP437 with their Unicode equiv
    start = time.time()
    print("Repairing invalid XML characters... ", end='')
    contents = repair_invalid_chars(contents)
    print(f"done in {time.time() - start:.2f} seconds")
    # Second, replace line breaks inside attributes with proper XML line breaks
    start = time.time()
    print("Repairing invalid XML line breaks... ", end='')
    contents = repair_invalid_linebreaks(contents)
    print(f"done in {time.time() - start:.2f} seconds")
    contents_b = contents.encode('utf-8')  # start/stop markers are in bytes, not characters
    raw = ET.fromstring(contents, parser=LineNumberingParser())
    print("Building Qud object hierarchy and adding tiles...")
    # Build the Qud object hierarchy from the XML data
    last_stop = 0
    for element in raw:
        # parsing 'ends' at the close tag, so add 9 bytes to include '</object>'
        start, stop = element._start_byte_index, element._end_byte_index + 9
        source = contents_b[start:stop].decode('utf-8')
        # capture comments, etc. before start tag for later saving
        full_source = contents_b[last_stop:stop].decode('utf-8')
        last_stop = stop
        if element.tag != 'object':
            continue
        obj = QudObjectWiki(element, source, full_source, qindex)
    tail = contents_b[last_stop:].decode('utf-8')
    obj.source = source + tail  # add tail of file to the XML source of last object loaded
    qud_object_root = qindex['Object']
    return qud_object_root

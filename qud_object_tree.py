"""Functionality for loading the Qud object blueprint XML into a tree of QudObjects.

For on-demand access to individual Qud objects by name, use the `qindex` from qudobject.py."""

import re
import time

from xml.etree import ElementTree as et

from qudobject import qindex
from qudobject_wiki import QudObjectWiki


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
    raw = et.fromstring(contents)
    print("Building Qud object hierarchy and adding tiles...")
    # Build the Qud object hierarchy from the XML data
    for element in raw:
        if element.tag != 'object':
            continue
        QudObjectWiki(element)  # registers itself in qindex
    qud_object_root = qindex['Object']
    return qud_object_root

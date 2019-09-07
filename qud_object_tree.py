"""Functionality for loading the Qud object blueprint XML into a tree of QudObjects.

For on-demand access to individual Qud objects by name, use the `qindex` from qudobject.py."""

import re
import time

from xml.etree import ElementTree as et

from qudobject import QudObject, qindex


def load(path):
    """Load ObjectBlueprints.xml from the specified filepath and return a reference to the root."""
    print("Repairing invalid XML characters... ", end='')
    start = time.time()
    # Do some repair of invalid XML:
    # First, replace some invalid control characters intended for CP437 with their Unicode equiv
    with open(path, 'r', encoding='utf-8') as f:
        contents = f.read()
    ch_re = re.compile("&#11;")
    contents = re.sub(ch_re, '♂', contents)
    ch_re = re.compile("&#15;")
    contents = re.sub(ch_re, '☼', contents)
    print(f"done in {time.time() - start:.2f} seconds")

    print("Repairing invalid XML line breaks... ", end='')
    start = time.time()
    # Second, replace line breaks inside attributes with proper XML line breaks
    # ^\s*<[^!][^>]*\n[^>]*>
    pat_linebreaks = r"^\s*<[^!][^>]*\n.*?>"
    match = re.search(pat_linebreaks, contents, re.MULTILINE)
    while match:
        before = match.string[:match.start()]
        fixed = match.string[match.start():match.end()].replace('\n', '&#10;')
        after = match.string[match.end():]
        contents = before + fixed + after
        match = re.search(pat_linebreaks, contents, re.MULTILINE)
    # Uncomment to have a diff-able file to double check XML repairs.
    # with open('test_output.xml', 'w', encoding='utf-8') as f:
    #     f.write(contents)
    print(f"done in {time.time() - start:.2f} seconds")

    raw = et.fromstring(contents)

    print("Building Qud object hierarchy and adding tiles...")
    # Build the Qud object hierarchy from the XML data
    for element in raw:
        if element.tag != 'object':
            continue
        QudObject(element)  # registers itself in qindex

    # import into other modules for access to the root of the Qud object hierarchy
    qud_object_root = qindex['Object']
    return qud_object_root

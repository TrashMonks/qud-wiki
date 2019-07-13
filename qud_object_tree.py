"""Functionality for loading the Qud object blueprint XML into a tree of QudObjects.

For on-demand access to individual Qud objects by name, use the `qindex` from qudobject.py."""

import re

from xml.etree import ElementTree as et

from qudobject import QudObject, qindex


def load(path):
    """Load ObjectBlueprints.xml from the specified filepath and return a reference to the root."""
    # Do some repair of invalid XML:
    # First, delete some invalid characters
    pat_invalid = re.compile("(&#15;)|(&#11;)")
    with open(path, 'r', encoding='utf-8') as f:
        contents = f.read()
    contents = re.sub(pat_invalid, '', contents)

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

    raw = et.fromstring(contents)

    # Build the Qud object hierarchy from the XML data
    for element in raw:
        if element.tag != 'object':
            continue
        newobj = QudObject(element)

    # import into other modules for access to the root of the Qud object hierarchy
    qud_object_root = qindex['Object']
    return qud_object_root

"""Functionality for loading the Qud object blueprint XML into a tree of QudObjects.

For on-demand access to individual Qud objects by name, use the `qindex` from qud_object.py."""

import re

from xml.etree import ElementTree as et

from qud_object import QudObject, qindex


def load(path):
    """Load ObjectBlueprints.xml from the specified filepath and return a reference to the root."""
    # Do some repair of invalid XML
    pattern = re.compile("(&#15;)|(&#11;)")
    repaired = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            repaired.append(pattern.sub('', line))
    raw = et.fromstringlist(repaired)

    # Build the Qud object hierarchy from the XML data
    for element in raw:
        if element.tag != 'object':
            continue
        newobj = QudObject(element, qindex)

    # import into other modules for access to the root of the Qud object hierarchy
    qud_object_root = qindex['Object']
    return qud_object_root

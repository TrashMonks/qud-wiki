"""pytest functions to test functions in qudobject.py"""

import os

import qud_object_tree  # to build the qindex in qudobject.py
from qudobject import *  # what we are actually testing

# fallback location
TEST_XML_LOC = "C:/Steam/SteamApps/common/Caves of Qud/CoQ_Data/StreamingAssets/Base/ObjectBlueprints.xml"

if os.path.exists('last_xml_location'):
    with open('last_xml_location') as f:
        filename = f.read()
    qud_object_tree.load(filename)
else:
    qud_object_tree.load(TEST_XML_LOC)


def test_escape_ampersands():
    assert escape_ampersands('&yfloating&G &Yglowsphere') == '&amp;yfloating&amp;G &amp;Yglowsphere'


def test_strip_qud_color_codes():
    assert strip_qud_color_codes('&yfloating&G &Yglowsphere') == 'floating glowsphere'


def test_inherits_from():
    obj = qindex['Stopsvaalinn']
    assert obj.inherits_from('BaseShield')
    assert obj.inherits_from('Item')
    assert obj.inherits_from('InorganicObject')
    assert obj.inherits_from('PhysicalObject')
    assert obj.inherits_from('Object')
    assert not obj.inherits_from('Widget')
    obj = qindex['Object']
    assert obj.inherits_from('Object')


def test_is_specified():
    obj = qindex['Stopsvaalinn']
    assert obj.is_specified('part_Commerce_Value')
    assert not obj.is_specified('fart_Commerce_Value')


def test_properties():
    obj = qindex['Asphodel']
    assert obj.lv == '30'
    assert obj.hp == '500'
    assert obj.av == '11'  # natural 8 + clay pot
    # assert obj.dv == '12'  # base 6 plus (28 - 16) / 2

import qud_object_tree  # to build the qindex in qud_object.py
from qud_object import *  # what we are actually testing


def test_yes_no_none():
    @yes_no_none
    def f(x):
        return x
    assert f('true') == 'yes'
    assert f('false') == 'no'
    assert f(True) == 'yes'
    assert f(False) == 'no'


def test_inherits_from():
    obj = qindex['Stopsvaalinn']
    assert obj.inherits_from('BaseShield')
    assert obj.inherits_from('Item')
    assert obj.inherits_from('InorganicObject')
    assert obj.inherits_from('PhysicalObject')
    assert obj.inherits_from('Object')
    assert not obj.inherits_from('Widget')
    obj = qindex['Object']
    assert not obj.inherits_from('Object')


def test_is_specified():
    obj = qindex['Stopsvaalinn']
    assert obj.is_specified('part_Commerce_Value')
    assert not obj.is_specified('fart_Commerce_Value')


def test_properties():
    obj = qindex['Asphodel']
    assert obj.lv == '30'
    assert obj.hp == '500'
    assert obj.av == '8'
    assert obj.dv == '12'
    assert obj.ma == '12'

"""attr specification:
QudObject.part_name_attribute"""

from xml.etree.ElementTree import Element

from anytree import NodeMixin

qindex = {}  # fast lookup of name->QudObject


class QudObject(NodeMixin):
    """Represents a Caves of Qud object blueprint with attribute inheritance"""
    def __init__(self, blueprint: Element):
        self.name = blueprint.get('Name')
        qindex[self.name] = self
        parent_name = blueprint.get('Inherits')
        if parent_name:
            self.parent = qindex[parent_name]
        else:
            self.parent = None
        self.attributes = {}
        for element in blueprint:
            if 'Name' not in element.attrib:
                # don't need these for now - inventory, etc.
                # print(self.name, element.tag, element.attrib)
                continue
            if element.tag not in self.attributes:
                self.attributes[element.tag] = {}
            element_name = element.attrib.pop('Name')
            self.attributes[element.tag][element_name] = element.attrib

    def is_specified(self, attr):
        """Return True if `attr` is specified explicitly for this object,
        False if it is inherited or does not exist"""
        path = attr.split('_')
        try:
            tag = self.attributes[path[0]]
            name = tag[path[1]]
            attrib = name[path[2]]
            return True
        except KeyError:
            return False


    def __getattr__(self, attr):
        if attr.startswith('_'):  # guard against NodeMixIn housekeeping
            raise AttributeError
        if attr == 'attributes':  # guard against recursion
            raise AttributeError
        path = attr.split('_')
        try:
            seek = self.attributes[path[0]]
            if len(path) > 1:
                seek = seek[path[1]]
            if len(path) > 2:
                seek = seek[path[2]]
        except KeyError:
            if self.is_root:
                seek = None
            else:
                seek = self.parent.__getattr__(attr)
        return seek

    def __str__(self):
        return self.name + ' ' + str(self.attributes)

    def __repr__(self):
        return 'QudObject(' + self.name + ')'

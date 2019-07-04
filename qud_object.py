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

    def inherits_from(self, name: str):
        """Returns True if this object inherits from the object named 'name', False otherwise."""
        if self.is_root:
            return False
        if self.parent.name == name:
            return True
        return self.parent.inherits_from(name)

    def is_specified(self, attr):
        """Return True if `attr` is specified explicitly for this object,
        False if it is inherited or does not exist"""
        # TODO: doesn't work right
        path = attr.split('_')
        try:
            seek = self.attributes[path[0]]
            if len(path) > 1:
                seek = seek[path[1]]
            if len(path) > 2:
                seek = seek[path[2]]
        except KeyError:
            return False
        return True

    def __getattr__(self, attr):
        """Implemented to get inherited tags from the Qud object tree

        Example: given the following Qud object:
          <object Name="Bandage" Inherits="Item">
            <part Name="Examiner" Complexity="0"></part>
            <part Name="Render" Tile="Items/sw_hit.bmp" DetailColor="R" DisplayName="&amp;ybandage" ColorString="&amp;y" RenderString="012" RenderLayer="5"></part>
            <part Name="Physics" Category="Meds" Weight="0"></part>
            <part Name="Description" Short="A roll of gauze, suited to staunch bleeding."></part>
            <part Name="Commerce" Value="1"></part>
            <part Name="Medication"></part>
            <part Name="BandageMedication"></part>
            <tag Name="AlwaysStack" Value="Yes"></tag>
            <intproperty Name="Inorganic" Value="0" />
          </object>

        this_object.part_Render_Tile would retrieve 'Items/sw_hit.bmp'
        this_object.tag would retrieve {'AlwaysStack': {'Value': 'Yes'}}
        this_object.stat_Strength would retrieve None (after searching the inheritance tree)
        'meds' if this_object.part_Medication is not None else 'no_meds'
          would evaluate to 'meds'
        thisobject.tag_TinkerCategory would retrieve {'Value': 'utility'}
          (inherited from Item)
        """
        if attr.startswith('_'):  # guard against NodeMixIn housekeeping
            raise AttributeError
        if attr == 'attributes':  # guard against uninvited recursion
            raise AttributeError
        path = attr.split('_')
        try:
            seek = self.attributes[path[0]]  # XML tag portion
            if len(path) > 1:
                seek = seek[path[1]]  # Name portion
            if len(path) > 2:
                seek = seek[path[2]]  # attribute portion
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

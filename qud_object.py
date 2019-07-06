"""attr specification:
QudObject.part_name_attribute"""

import re
from xml.etree.ElementTree import Element

from anytree import NodeMixin

from config import config

IMAGE_OVERRIDES = config['Image overrides']


class QudObject(NodeMixin):
    """Represents a Caves of Qud object blueprint with attribute inheritance.

    Parameters:
        blueprint: an XML Element to parse into dictionaries
        qindex: a dictionary to stash our Name:self mapping, for use later"""

    def __init__(self, blueprint: Element, qindex):
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
        """Implemented to get explicit or inherited tags from the Qud object tree.

        These virtual attributes take the form
          (XML tag) _ (Value of name attribute) _ (Other attribute)

        Example: given the following Qud object in the XML source file:
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

        For the most basic usage,
            `this_object.part_Render_Tile` would retrieve the string 'Items/sw_hit.bmp'

        Other uses:
        this_object.tag would retrieve the dictionary {'AlwaysStack': {'Value': 'Yes'}}
        this_object.stat_Strength would retrieve None (after searching the inheritance tree)
        The expression:
          'meds' if this_object.part_Medication is not None else 'no_meds'
        would evaluate to 'meds'
        thisobject.tag_TinkerCategory would retrieve the dictionary {'Value': 'utility'}
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

    def wikify(self):
        """Return a string representation of self in the Caves of Qud wiki item template format."""
        fields = ('image', 'lv', 'pv', 'maxpv', 'vibro', 'pvpowered', 'hp', 'av', 'dv',
                  'ma', 'tohit', 'ammo', 'accuracy', 'shots', 'maxammo', 'maxvol',
                  'liquidgen', 'liquidtype', 'maxcharge', 'charge', 'weight', 'commerce',
                  'complexity', 'tier', 'bits', 'canbuild', 'skill', 'renderstr', 'id',
                  'bookid', 'lightradius', 'hunger', 'thirst', 'twohanded', 'metal',
                  'lightprojectile', 'extra', 'strength', 'agility', 'toughness',
                  'intelligence', 'willpower', 'ego', 'acid', 'electric', 'cold', 'heat')
        output = "{{Item\n"
        output += "| title = {{Qud text|" + self.title + "}}\n"
        for stat in fields:
            if getattr(self, stat) is not None:
                output += f"| {stat} = {getattr(self, stat)}\n"
        output += "| desc = {{ Qud text|" + self.desc + "}}\n"
        output += "}}\n"
        return output

    def __str__(self):
        return self.name + ' ' + str(self.attributes)

    def __repr__(self):
        return 'QudObject(' + self.name + ')'

    # The following properties are implemented to make wiki formatting far simpler.
    # Sorted alphabetically.

    @property
    def accuracy(self):
        """How accurate the gun is."""
        return self.part_MissileWeapon_WeaponAccuracy

    @property
    def acid(self):
        """The elemental resistance/weakness the mutation has."""
        return self.stat_AcidResistance

    @property
    def agility(self):
        """The agility the mutation affects, or the agility of the creature."""
        if self.inherits_from('Creature'):
            if self.stat_Agility_sValue:
                return self.stat_Agility_sValue
            elif self.stat_Agility_Value:
                return self.stat_Agility_Value

    @property
    def ammo(self):
        """What type of ammo is used."""
        # TODO
        pass

    @property
    def av(self):
        if self.stat_AV_Value:  # the AV of creatures and stationary objects
            av = self.stat_AV_Value
        if self.part_Armor_AV:  # the AV of armor
            av = self.part_Armor_AV
        if self.part_Shield_AV:  # the AV of a shield
            av = self.part_Shield_AV
        return av

    @property
    def bits(self):
        # TODO
        pass

    @property
    def bookid(self):
        """Id in books.xml."""
        # TODO

    @property
    def canbuild(self):
        # TODO
        pass

    @property
    def charge(self):
        """How much charge is used per shot."""

    @property
    def cold(self):
        """The elemental resistance/weakness the mutation has."""
        return self.stat_ColdResistance

    @property
    def commerce(self):
        """The value of the object."""
        return self.part_Commerce_Value

    @property
    def complexity(self):
        # TODO
        pass

    @property
    def damage(self):
        return self.part_MeleeWeapon_BaseDamage

    @property
    def desc(self):
        """The short description of the object, with color codes included (ampersands escaped)."""
        return re.sub('&', '&amp;', self.part_Description_Short)

    @property
    def dv(self):
        # TODO: calculate DV of NPCs
        return self.stat_DV_Value

    @property
    def ego(self):
        """The ego the mutation effects, or the ego of the creature."""
        if self.inherits_from('Creature'):
            if self.stat_Ego_sValue:
                return self.stat_Ego_sValue
            elif self.stat_Ego_Value:
                return self.stat_Ego_Value

    @property
    def electric(self):
        """The elemental resistance/weakness the mutation has."""
        return self.stat_ElectricResistance

    @property
    def extra(self):
        """Any other features that do not have an associated variable."""
        # TODO
        pass

    @property
    def heat(self):
        """The elemental resistance/weakness the mutation has."""
        return self.stat_HeatResistance

    @property
    def hp(self):
        if self.stat_Hitpoints_sValue:
            return self.stat_Hitpoints.sValue
        elif self.stat_Hitpoints_Value:
            return self.stat_Hitpoints_Value

    @property
    def hunger(self):
        """How much hunger it satiates."""
        # TODO
        pass

    @property
    def id(self):
        """The name of the object in ObjectBlueprints.xml."""
        return self.name

    @property
    def image(self):
        """The image. If the item has no associated sprite, return None."""
        if self.name in IMAGE_OVERRIDES:
            return IMAGE_OVERRIDES[self.name]
        else:
            # "Creatures/sw_flower.bmp" becomes "sw_flower.png"
            tile = self.part_Render_Tile.split('/')[-1]
            tile = re.sub('bmp$', 'png', tile)
            return tile

    @property
    def intelligence(self):
        """The intelligence the mutation affects, or the intelligence of the creature."""
        if self.inherits_from('Creature'):
            if self.stat_Intelligence_sValue:
                return self.stat_Intelligence_sValue
            elif self.stat_Intelligence_Value:
                return self.stat_Intelligence_Value

    @property
    def lightprojectile(self):
        # TODO
        pass

    @property
    def lightradius(self):
        """Radius of light it gives off."""
        # TODO
        pass

    @property
    def liquidgen(self):
        """For liquid generators. how many turns it takes for 1 dram to generate."""
        # TODO
        pass

    @property
    def liquidtype(self):
        """For liquid generators, the type of liquid generated."""

    @property
    def lv(self):
        """The object's level."""
        return self.stat_Level_Value

    @property
    def ma(self):
        return self.stat_MA_Value

    @property
    def maxammo(self):
        """How much ammo a gun can have loaded at once."""
        # TODO
        pass

    @property
    def maxcharge(self):
        """How much charge it can hold (usually reserved for cells)."""
        # TODO
        pass

    @property
    def maxvol(self):
        """The maximum liquid volume."""
        # TODO
        pass

    @property
    def maxpv(self):
        """The max strength bonus + base PV."""
        maxpv = self.pv
        if self.part_MeleeWeapon_MaxStrengthBonus:
            maxpv += int(self.part_MeleeWeapon_MaxStrengthBonus)
        return maxpv

    @property
    def metal(self):
        """Whether the object is made out of metal."""
        # TODO
        pass

    @property
    def pen_bonus(self):
        # TODO
        if self.part_MeleeWeapon_PenBonus:
            pass

    @property
    def pv(self):
        """The base PV, which is by default 4 if not set. Optional."""
        pv = 4
        if self.part_MeleeWeapon_PenBonus:
            pv += int(self.part_MeleeWeapon_PenBonus)
        return pv

    @property
    def pvpowered(self):
        # TODO
        pass

    @property
    def renderstr(self):
        """What the item looks like with tiles mode off."""
        # TODO
        pass

    @property
    def shots(self):
        """How many shots are fired in one round."""
        # TODO
        pass

    @property
    def skill(self):
        """The skill tree required for use."""
        return self.part_MeleeWeapon_Skill

    @property
    def strength(self):
        """The strength the mutation affects, or the strength of the creature."""
        if self.inherits_from('Creature'):
            if self.stat_Strength_sValue:
                return self.stat_Strength_sValue
            elif self.stat_Strength_Value:
                return self.stat_Strength_Value

    @property
    def thirst(self):
        """How much thirst it slakes."""
        # TODO
        pass

    @property
    def tier(self):
        return self.tag_Tier_Value

    @property
    def title(self):
        """The display name of the item."""
        return re.sub('&', '&amp;', self.part_Render_DisplayName)

    @property
    def tohit(self):
        """The bonus or penalty to hit."""
        # TODO
        pass

    @property
    def toughness(self):
        """The toughness the mutation affects, or the toughness of the creature."""
        if self.inherits_from('Creature'):
            if self.stat_Toughness_sValue:
                return self.stat_Toughness_sValue
            elif self.stat_Toughness_Value:
                return self.stat_Toughness_Value

    @property
    def twohanded(self):
        """Whether this is a two-handed item."""
        if self.part_Physics_bUsesTwoSlots:
            return 'true'
        return 'false'

    @property
    def vibro(self):
        """Whether this is a vibro weapon."""
        if self.inherits_from('NaturalWeapon') or self.inherits_from('MeleeWeapon'):
            if self.tag_VibroWeapon:
                return 'true'
            return 'false'

    @property
    def weight(self):
        """The weight of the object."""
        return self.part_Physics_Weight

    @property
    def willpower(self):
        """The willpower the mutation affects, or the willpower of the creature.."""
        if self.inherits_from('Creature'):
            if self.stat_Willpower_sValue:
                return self.stat_Willpower_sValue
            elif self.stat_Willpower_Value:
                return self.stat_Willpower_Value

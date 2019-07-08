"""attr specification:
QudObject.part_name_attribute"""

import re
from xml.etree.ElementTree import Element

from anytree import NodeMixin

from config import config

IMAGE_OVERRIDES = config['Templates']['Image overrides']

qindex = {}  # fast lookup of name->QudObject


def yes_no_none(func):
    """Decorator to convert 'true'/'false'/None, or True/False/None into 'yes'/'no'/None"""
    conv = {'true': 'yes',
            'false': 'no',
            True: 'yes',
            False: 'no',
            }

    def wrapper(*args, **kwargs):
        return conv.get(func(*args, **kwargs))
    return wrapper


class QudObject(NodeMixin):
    """Represents a Caves of Qud object blueprint with attribute inheritance.

    Parameters:
        blueprint: an XML Element to parse into dictionaries
        qindex: a dictionary to stash our Name:self mapping, for use later"""

    def __init__(self, blueprint: Element, qindex):
        self.name = blueprint.get('Name')
        self.blueprint = blueprint
        qindex[self.name] = self
        parent_name = blueprint.get('Inherits')
        if parent_name:
            self.parent = qindex[parent_name]
        else:
            self.parent = None
        self.attributes = {}
        for element in blueprint:
            if 'Name' not in element.attrib and element.tag != 'inventoryobject':
                # probably something we don't need
                continue
            if element.tag not in self.attributes:
                self.attributes[element.tag] = {}
            if 'Name' in element.attrib:
                # most tags
                element_name = element.attrib.pop('Name')
            elif 'Blueprint' in element.attrib:
                # for tag: inventoryobject
                element_name = element.attrib.pop('Blueprint')
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

    def parse_multi_sValue(self, svalue: str):
        """Derive an integer from an sValue comma-separated format stat string for self.

        Example:
            "16,1d3,(t-1)d2" becomes 17 by this process:
            16 is the base
            1d3 is taken as average (2)
            t is calculated as (Level // 5 + 1) or 2
            2d2 is taken as average (3)

        """
        base, roll, final = svalue.split(',')
        t = int(self.lv) // 5 + 1

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
        fields = config['Templates']['Fields']
        output = "{{Item\n"
        output += "| title = {{Qud text|" + self.title + "}}\n"
        for stat in fields:
            if getattr(self, stat) is not None:
                output += f"| {stat} = {getattr(self, stat)}\n"
        output += "}}\n"
        return output

    def __str__(self):
        return self.name + ' ' + str(self.attributes)

    def __repr__(self):
        return 'QudObject(' + self.name + ')'

    # The following properties are implemented to make wiki formatting far simpler.
    # Sorted alphabetically. All return types should be strings.

    @property
    def accuracy(self):
        """How accurate the gun is."""
        return self.part_MissileWeapon_WeaponAccuracy

    @property
    def acid(self):
        """The elemental resistance/weakness the mutation has."""
        return self.stat_AcidResistance_Value

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
        ammo = self.part_MagazineAmmoLoader_AmmoPart
        texts = {'AmmoSlug': 'lead slug',
                 'AmmoShotgunShell': 'shotgun shell',
                 'AmmoGrenade': 'grenade',
                 'AmmoMissile': 'missile',
                 'AmmoArrow': 'arrow',
                 'AmmoDart': 'dart',
                 }
        return texts.get(ammo)

    @property
    def av(self):
        """The AV that an item provides, or the AV that a creature has."""
        av = None
        if self.part_Armor_AV:  # the AV of armor
            av = self.part_Armor_AV
        if self.part_Shield_AV:  # the AV of a shield
            av = self.part_Shield_AV
        if self.stat_AV_Value and self.inherits_from('Creature'):
            # the AV of creatures and stationary objects
            av = int(self.stat_AV_Value)  # first, creature's intrinsic AV
            if self.inventoryobject:
                # might be wearing armor
                for name in list(self.inventoryobject.keys()):
                    item = qindex[name]
                    if item.av:
                        av += int(item.av)
        return str(av) if av else None

    @property
    def bits(self):
        """The bits you can get from disassembling the object."""
        if self.part_TinkerItem_CanDisassemble:
            return self.part_TinkerItem_Bits

    @property
    def bookid(self):
        """Id in books.xml."""
        return self.part_Book_ID

    @property
    @yes_no_none
    def canbuild(self):
        """Whether or not the player can tinker up this item."""
        if self.part_TinkerItem_CanBuild == 'true':
            return 'yes'
        if self.part_TinkerItem_CanDisassemble == 'true':
            return self.part_TinkerItem_CanBuild

    @property
    @yes_no_none
    def candisassemble(self):
        """Whether or not the player can disassemble this item."""
        if self.part_TinkerItem_CanDisassemble == 'true':
            return 'yes'
        if self.part_TinkerItem_CanBuild == 'true':
            return self.part_TinkerItem_CanDisassemble

    @property
    def charge(self):
        """How much charge is used per shot."""
        return self.part_EnergyAmmoLoader_ChargeUse

    @property
    def cold(self):
        """The elemental resistance/weakness the mutation/item/NPC has."""
        if self.part_Armor:
            return self.part_Armor_Cold
        return self.stat_ColdResistance_Value

    @property
    def commerce(self):
        """The value of the object."""
        if self.inherits_from('Item'):
            return self.part_Commerce_Value

    @property
    def complexity(self):
        """The tinker examination complexity of the object."""
        if self.canbuild == 'true':
            return self.part_Examiner_Complexity

    @property
    def damage(self):
        return self.part_MeleeWeapon_BaseDamage

    @property
    def desc(self):
        """The short description of the object, with color codes included (ampersands escaped)."""
        if self.part_Description_Short:
            return re.sub('&', '&amp;', self.part_Description_Short)
        else:
            return ""

    @property
    def dv(self):
        dv = None
        if self.inherits_from('Creature'):
            dv = 6
            if self.agility:
                dv += int((int(self.agility) - 16) / 2)
            if self.skill_Acrobatics_Tumble:
                dv += 1
        elif self.inherits_from('Armor'):
            dv = self.part_Armor_DV
        # elif self.stat_DV_Value:  # is this actually needed for anything?
        #     dv = self.stat_DV_Value
        return str(dv) if dv else None

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
        return self.stat_ElectricResistance_Value

    @property
    def extra(self):
        """Any other features that do not have an associated variable."""
        # TODO
        pass

    @property
    def heat(self):
        """The elemental resistance/weakness the mutation has."""
        return self.stat_HeatResistance_Value

    @property
    def hp(self):
        if self.inherits_from('Creature'):
            if self.stat_Hitpoints_sValue:
                return self.stat_Hitpoints_sValue
            elif self.stat_Hitpoints_Value:
                return self.stat_Hitpoints_Value

    @property
    def hunger(self):
        """How much hunger it satiates."""
        return self.part_Food_Satiation

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
        """Radius of light the object gives off."""
        return self.part_LightSource_Radius

    @property
    def liquidgen(self):
        """For liquid generators. how many turns it takes for 1 dram to generate."""
        # TODO: is this correct?
        return self.part_LiquidProducer_Rate

    @property
    def liquidtype(self):
        """For liquid generators, the type of liquid generated."""
        return self.part_LiquidProducer_Liquid

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
        return self.part_MagazineAmmoLoader_MaxAmmo

    @property
    def maxcharge(self):
        """How much charge it can hold (usually reserved for cells)."""
        return self.part_EnergyCell_MaxCharge

    @property
    def maxvol(self):
        """The maximum liquid volume."""
        return self.part_LiquidVolume_MaxVolume

    @property
    def maxpv(self):
        """The max strength bonus + base PV."""
        try:
            maxpv = int(self.pv)
        except TypeError:
            return None  # borrow from the PV validity detection
        else:
            if self.part_MeleeWeapon_MaxStrengthBonus:
                maxpv += int(self.part_MeleeWeapon_MaxStrengthBonus)
            return str(maxpv)

    @property
    def metal(self):
        """Whether the object is made out of metal."""
        if self.part_Metal:
            return 'yes'
        # skipping returning 'no' because it's not interesting to see

    @property
    def pv(self):
        """The base PV, which is by default 4 if not set. Optional."""
        # TODO: does this have meaning for other than MeleeWeapons?
        if self.inherits_from('MeleeWeapon') or self.is_specified('part_MeleeWeapon'):
            pv = 4
            if self.part_MeleeWeapon_PenBonus:
                pv += int(self.part_MeleeWeapon_PenBonus)
            return str(pv)

    @property
    def pvpowered(self):
        """If true, adds a row that shows the unpowered pv (4)."""
        # TODO: is this necessary?
        if self.pv:
            return 'yes'

    @property
    def renderstr(self):
        """What the item looks like with tiles mode off."""
        if self.part_Render_RenderString and len(self.part_Render_RenderString) > 1:
            # some RenderStrings are given as CP437 character codes in base 10
            byte = bytes.fromhex(hex(int(self.part_Render_RenderString))[-2:])
            return byte.decode(encoding='cp437')
        else:
            return self.part_Render_RenderString

    @property
    def shots(self):
        """How many shots are fired in one round."""
        return self.part_MissileWeapon_ShotsPerAction

    @property
    def skill(self):
        """The skill tree required for use."""
        if self.inherits_from('MeleeWeapon') or self.is_specified('part_MeleeWeapon'):
            return self.part_MeleeWeapon_Skill
        if self.inherits_from('MissileWeapon'):
            return self.part_MissileWeapon_Skill

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
        return self.part_Food_Thirst

    @property
    def tier(self):
        return self.tag_Tier_Value

    @property
    def title(self):
        """The display name of the item."""
        if self.part_Render_DisplayName:
            return re.sub('&', '&amp;', self.part_Render_DisplayName)
        else:
            return self.name

    @property
    def tohit(self):
        """The bonus or penalty to hit."""
        if self.inherits_from('Armor'):
            return self.part_Armor_ToHit

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
        if self.inherits_from('MeleeWeapon') or self.inherits_from('MissileWeapon'):
            if self.part_Physics_bUsesTwoSlots:
                return 'yes'
            return 'no'

    @property
    def vibro(self):
        """Whether this is a vibro weapon."""
        if self.inherits_from('NaturalWeapon') or self.inherits_from('MeleeWeapon'):
            if self.part_VibroWeapon:
                return 'yes'
            return 'no'

    @property
    def weight(self):
        """The weight of the object."""
        return self.part_Physics_Weight

    @property
    def willpower(self):
        """The willpower the mutation affects, or the willpower of the creature."""
        if self.inherits_from('Creature'):
            if self.stat_Willpower_sValue:
                return self.stat_Willpower_sValue
            elif self.stat_Willpower_Value:
                return self.stat_Willpower_Value

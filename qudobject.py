"""attr specification:
QudObject.part_name_attribute"""

import re
from copy import deepcopy
from xml.etree.ElementTree import Element

from anytree import NodeMixin

from config import config
from helpers import cp437_to_unicode
from qudtile import QudTile
from svalue import sValue

IMAGE_OVERRIDES = config['Templates']['Image overrides']

qindex = {}  # fast lookup of name->QudObject

bit_table = {'G': 'B',
             'R': 'A',
             'C': 'D',
             'B': 'C'}
BIT_TRANS = ''.maketrans(bit_table)


def escape_ampersands(text: str):
    """Convert & to &amp; for use in wiki template."""
    return re.sub('&', '&amp;', text)


def strip_qud_color_codes(text: str):
    """Remove Qud color codes like `&Y` from the provided text."""
    return re.sub('&.', '', text)


class QudObject(NodeMixin):
    """Represents a Caves of Qud object blueprint with attribute inheritance.

    Parameters:
        blueprint: an XML Element to parse into dictionaries
        qindex: a dictionary to stash our Name:self mapping, for use later"""

    def __init__(self, blueprint: Element):
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
        self.all_attributes, self.inherited = self.resolve_inheritance()
        self.tile = self.render_tile()

    def render_tile(self):
        tile = None
        if self.part_Render_Tile and not self.tag_BaseObject:
            tile = QudTile(self.part_Render_Tile,
                           self.part_Render_ColorString,
                           self.part_Render_TileColor,
                           self.part_Render_DetailColor)
        return tile

    def resolve_inheritance(self):
        """Fetch a dictionary with all inherited tags and attributes.

        Recurses back all the way to the root Object and combines all data into
        the returned dict. Attributes of tags in children overwrite ancestors.

        Example:
          <object Name="BaseFarmer" Inherits="NPC">
            <part Name="Render" DisplayName="[farmer]" ...
        with the child object:
          <object Name="BaseWatervineFarmer" Inherits="BaseFarmer">
            <part Name="Render" DisplayName="watervine farmer" ...
        overwrites the DisplayName but not the rest of the Render dict.
        """
        if self.name == 'Object':
            return self.attributes, {}
        inherited = self.parent.all_attributes
        all_attributes = deepcopy(self.attributes)
        for tag in inherited:
            if not tag in all_attributes:
                all_attributes[tag] = {}
            for name in inherited[tag]:
                if not name in all_attributes[tag]:
                    all_attributes[tag][name] = {}
                for attr in inherited[tag][name]:
                    if not attr in all_attributes[tag][name]:
                        # parent has this attribute but we don't
                        # print(tag, name, attr, "didn't exist in exists in", self.name)
                        if inherited[tag][name][attr] == '*noinherit':
                            # this attribute shows that its name should not be inherited
                            del all_attributes[tag][name]
                        else:
                            all_attributes[tag][name][attr] = inherited[tag][name][attr]
                    else:
                        # we already had this defined for us - don't overwrite
                        # print(tag, name, attr, "already exists in", self.name)
                        pass
        return all_attributes, inherited

    def ui_inheritance_path(self) -> str:
        """Return a textual representation of this object's inheritance path."""
        text = self.name
        ancestor = self.parent
        while ancestor is not None:
            text = ancestor.name + "➜" + text
            ancestor = ancestor.parent
        return text

    def inherits_from(self, name: str):
        """Returns True if this object is 'name' or inherits from 'name', False otherwise."""
        if self.name == name:
            return True
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

        Usage note:
          Empty <part> and <tag> tags (with no attributes) will evaluate to an empty dictionary,
          which has the Boolean value False. Check to see that they are not None rather than
          treating them as a Boolean.
        """
        if attr.startswith('_'):  # guard against NodeMixIn housekeeping
            raise AttributeError
        if attr == 'attributes':  # guard against uninvited recursion
            raise AttributeError
        path = attr.split('_')
        try:
            seek = self.all_attributes[path[0]]  # XML tag portion
            if len(path) > 1:
                seek = seek[path[1]]  # Name portion
            if len(path) > 2:
                seek = seek[path[2]]  # attribute portion
        except KeyError:
            seek = None
        return seek

    def wikify(self):
        """Return a string representation of self in the Caves of Qud wiki item template format."""
        fields = config['Templates']['Fields']
        if self.inherits_from('Creature'):
            output = "{{Character\n"
        else:
            output = "{{Item\n"
        output += "| title = {{Qud text|" + self.title + "}}\n"
        for stat in fields:
            if getattr(self, stat) is not None:
                output += f"| {stat} = {getattr(self, stat)}\n"
        output += "}}\n"
        category = self.wiki_category()
        if category:
            output += "[[Category:" + category + "]]\n"
        return output

    def wiki_category(self):
        cat = None
        for config_cat, names in config['Wiki']['Categories'].items():
            for name in names:
                if self.inherits_from(name):
                    cat = config_cat
        return cat

    def __str__(self):
        return self.name + ' ' + str(self.attributes)

    def __repr__(self):
        return 'QudObject(' + self.name + ')'

    # PROPERTY HELPERS
    # Helper methods to simplify the calculation of properties, further below.
    # Sorted alphabetically. All return types should be strings.
    def attribute_helper(self, attr: str):
        """Helper for retrieving attributes (Strength, etc.)"""
        val = None
        if self.inherits_from('Creature'):
            if getattr(self, f'stat_{attr}_sValue'):
                val = str(sValue(getattr(self, f'stat_{attr}_sValue'), level=int(self.lv)))
            elif getattr(self, f'stat_{attr}_Value'):
                val = getattr(self, f'stat_{attr}_Value')
        boost = getattr(self, f'stat_{attr}_Boost')
        if boost:
            val += f' (+{boost} boost)'
        return val

    def resistance(self, element):
        """The elemental resistance/weakness the equipment or NPC has.
        Helper function for properties."""
        val = getattr(self, f'stat_{element}Resistance_Value')
        if self.part_Armor:
            val = getattr(self, f'part_Armor_{element}')
        return val

    # PROPERTIES
    # The following properties are implemented to make wiki formatting far simpler.
    # Sorted alphabetically. All return types should be strings.
    @property
    def accuracy(self):
        """How accurate the gun is."""
        return self.part_MissileWeapon_WeaponAccuracy

    @property
    def acid(self):
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance('Acid')

    @property
    def agility(self):
        """The agility the mutation affects, or the agility of the creature."""
        return self.attribute_helper('Agility')

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
                    if name[0] in '*#@':
                        # special values like '*Junk 1'
                        continue
                    item = qindex[name]
                    if item.av:
                        av += int(item.av)
        return str(av) if av else None

    @property
    def bits(self):
        """The bits you can get from disassembling the object."""
        if self.part_TinkerItem and self.part_TinkerItem_CanDisassemble != 'false':
            return self.part_TinkerItem_Bits.translate(BIT_TRANS)

    @property
    def bookid(self):
        """Id in books.xml."""
        return self.part_Book_ID

    @property
    def butcheredinto(self):
        """What a corpse item can be butchered into."""
        return self.part_Butcherable_OnSuccess

    @property
    def canbuild(self):
        """Whether or not the player can tinker up this item."""
        if self.part_TinkerItem_CanBuild == 'true':
            return 'yes'
        elif self.part_TinkerItem_CanDisassemble == 'true':
            return 'no'  # it's interesting if an item can't be built but can be disassembled

    @property
    def candisassemble(self):
        """Whether or not the player can disassemble this item."""
        if self.part_TinkerItem_CanDisassemble == 'true':
            return 'yes'
        elif self.part_TinkerItem_CanBuild == 'true':
            return 'no'  # # it's interesting if an item can't be disassembled but can be built

    @property
    def chargeperdram(self):
        """How much charge is available per dram (for liquid cells)."""
        return self.part_LiquidFueledEnergyCell_ChargePerDram

    @property
    def chargeused(self):
        """How much charge is used per shot."""
        charge = None
        if self.part_StunOnHit:
            charge = self.part_StunOnHit_ChargeUse
        if self.part_EnergyAmmoLoader:
            charge = self.part_EnergyAmmoLoader_ChargeUse
        if self.part_VibroWeapon:
            charge = self.part_VibroWeapon_ChargeUse
        if self.part_Gaslight:
            charge = self.part_Gaslight_ChargeUse
        if self.part_MechanicalWings:
            charge = self.part_MechanicalWings_ChargeUse
        return charge

    @property
    def cold(self):
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance('Cold')

    @property
    def colorstr(self):
        """The Qud color code associated with the RenderString."""
        if self.part_Render_ColorString:
            return escape_ampersands(self.part_Render_ColorString)

    @property
    def commerce(self):
        """The value of the object."""
        if self.inherits_from('Item'):
            return self.part_Commerce_Value

    @property
    def cookeffect(self):
        """The possible cooking effects of an item"""
        return self.part_PreparedCookingIngredient_type

    @property
    def complexity(self):
        """The tinker examination complexity of the object."""
        if self.canbuild == 'true':
            return self.part_Examiner_Complexity

    @property
    def cursed(self):
        """If the item cannot be removed by normal circumstances."""
        return self.part_Cursed

    @property
    def damage(self):
        val = None
        if self.inherits_from('MeleeWeapon') or self.is_specified('part_MeleeWeapon'):
            val = self.part_MeleeWeapon_BaseDamage
        if self.part_Gaslight:
            val = self.part_Gaslight_ChargedDamage
        return val

    @property
    def desc(self):
        """The short description of the object, with color codes included (ampersands escaped)."""
        if self.part_Description_Short == 'A hideous specimen.':
            return None  # hide items with no description of their own
        if self.part_Description_Short:
            return escape_ampersands(self.part_Description_Short)
        else:
            return ""

    @property
    def displayname(self):
        """The display name of the object, with color codes removed. Used in UI and wiki."""
        dname = ""
        if self.is_specified('part_Render_DisplayName'):
            dname = self.part_Render_DisplayName
            dname = strip_qud_color_codes(dname)
        return dname

    @property
    def dv(self):
        dv = None
        if self.inherits_from('Armor'):
            # the 'DV' we are interested in is the DV modifier of the armor
            dv = self.part_Armor_DV
        if self.inherits_from('Shield'):
            # same here
            dv = self.part_Shield_DV
        elif self.inherits_from('Creature') and self.stat_DV_Value:
            dv = self.stat_DV_Value  # sometimes explicitly given instead of to be calculated
        elif self.inherits_from('Creature'):
            # the 'DV' here is the actual DV of the creature or NPC, after:
            # skills, agility modifier (which may be a range determined by
            # dice rolls, and which changes DV by 1 for every 2 points of agility
            # over/under 16), and any equipment that is guaranteed to be worn
            dv = 6  # base DV of all Creatures
            if self.skill_Acrobatics_Dodge:
                # the 'Spry' skill
                dv += 2
            if self.skill_Acrobatics_Tumble:
                # the 'Tumble' skill
                dv += 1
            ag = self.agility
            if ag:
                if '-' in ag:
                    # a range, e.g. '18 - 20'
                    lower, upper = ag.split('-')
                    dvlower = dv + (int(lower) - 16) // 2
                    dvupper = dv + (int(upper) - 16) // 2
                    if dvlower == dvupper:
                        dv = dvlower
                    else:
                        # agility was a range so DV may be a range as well
                        dv = str(dvlower) + ' - ' + str(dvupper)
                else:
                    # an integer, not a range
                    dv += (int(ag) - 16) // 2
        return str(dv) if dv else None

    @property
    def ego(self):
        """The ego the mutation effects, or the ego of the creature."""
        return self.attribute_helper('Ego')

    @property
    def electric(self):
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance('Elec')

    @property
    def empsensitive(self):
        """Returns yes if the object is empensitive. Can be found in multiple parts."""
        if self.part_EquipStatBoost_IsEMPSensitive == 'true' or self.part_BootSequence_IsEMPSensitive == 'true' or self.part_NavigationBonus_IsEMPSensitive == 'true' or self.part_SaveModifier_IsEMPSensitive == 'true' or self.part_LiquidFueledPowerPlant_IsEMPSensitive == 'true' or self.part_LiquidProducer_IsEMPSensitive == 'true' or self.part_TemperatureAdjuster_IsEMPSensitive == 'true':
            return 'yes'

    @property
    def exoticfood(self):
        """When preserved, whether the player must explicitly choose to preserve it."""
        if self.tag_ChooseToPreserve is not None:
            return 'yes'

    @property
    def extra(self):
        """Any other features that do not have an associated variable."""
        # TODO
        pass

    @property
    def gender(self):
        """The gender of the object."""
        if self.tag_Gender_Value is not None and self.inherits_from('Creature'):
            return self.tag_Gender_Value

    @property
    def harvestedinto(self):
        """What an item produces when harvested."""
        return self.part_Harvestable_OnSuccess

    @property
    def healing(self):
        """How much a food item heals when used."""
        return self.part_Food_Healing

    @property
    def heat(self):
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance('Heat')

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
            tile = self.displayname
            tile = re.sub(r"[^a-zA-Z\d ]", '', tile)
            tile = tile.casefold() + '.png'
            return tile

    @property
    def intelligence(self):
        """The intelligence the mutation affects, or the intelligence of the creature."""
        return self.attribute_helper('Intelligence')

    @property
    def isfungus(self):
        """If the food item contains fungus."""
        if self.part_Mushroom is not None:
            return 'yes'

    @property
    def ismeat(self):
        """If the food item contains meat."""
        if self.part_Meat is not None:
            return 'yes'
    @property
    def isplant(self):
        """If the food item contains plants."""
        if self.part_Plant is not None:
            return 'yes'

    @property
    def lightprojectile(self):
        """If the gun fires light projectiles (heat immune creatures will not take damage from it)."""
        if self.tag_Light is not None:
            return 'yes'

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
        if self.part_Metal is not None:
            return 'yes'

    @property
    def preservedinto(self):
        """When preserved, what a preservable item produces."""
        return self.part_PreservableItem_Result

    @property
    def preservedquantity(self):
        """When preserved, how many preserves a preservable item produces."""
        return self.part_PreservableItem_Number

    @property
    def pv(self):
        """The base PV, which is by default 4 if not set. Optional."""
        # TODO: does this have meaning for other than MeleeWeapons?
        pv = None
        if self.inherits_from('MeleeWeapon') or self.is_specified('part_MeleeWeapon'):
            pv = 4
            if self.part_Gaslight_ChargedPenetrationBonus:
                pv += int(self.part_Gaslight_ChargedPenetrationBonus)
            elif self.part_MeleeWeapon_PenBonus:
                pv += int(self.part_MeleeWeapon_PenBonus)
        if pv:
            return str(pv)

    @property
    def pvpowered(self):
        """Whether the object's PV changes when it is powered."""
        if self.vibro == 'yes' or self.part_Gaslight:
            return 'yes'

    @property
    def reflect(self):
        """If it reflects, what percentage of damage is reflected."""
        return self.part_ModGlassArmor_Tier

    @property
    def renderstr(self):
        """What the item looks like with tiles mode off.

        Including <nowiki> to get around some rendering bugs with characters like } """
        if self.part_Render_RenderString and len(self.part_Render_RenderString) > 1:
            # some RenderStrings are given as CP437 character codes in base 10
            return '<nowiki>' + cp437_to_unicode(int(self.part_Render_RenderString)) + '</nowiki>'
        else:
            if self.part_Render_RenderString is not None:
                return '<nowiki>' + self.part_Render_RenderString + '</nowiki>'
            else:
                return None

    @property
    def reputationbonus(self):
        """Return reputation bonuses for each part."""
        # <part Name="AddsRep" Faction="Apes" Value="-100" />
        # <part Name="AddsRep" Faction="Antelopes,Goatfolk" Value="100" />
        # <part Name="AddsRep" Faction="Fungi:200,Consortium:-200" />
        ret = None
        if self.part_AddsRep:
            ret = ''
            for part in self.part_AddsRep_Faction.split(','):
                if ':' in part:
                    # has format like `Fungi:200,Consortium:-200`
                    faction, value = part.split(':')
                    ret += f'{{{{reputation bonus|{faction}|{value}}}}}'
                else:
                    # has format like `Antelopes,Goatfolk` and Value `100`
                    # or is a single faction, like `Apes` and Value `-100`
                    value = self.part_AddsRep_Value
                    ret += f'{{{{reputation bonus|{part}|{value}}}}}'
        return ret

    @property
    def shots(self):
        """How many shots are fired in one round."""
        return self.part_MissileWeapon_ShotsPerAction

    @property
    def skill(self):
        """The skill tree required for use."""
        val = None
        if self.inherits_from('MeleeWeapon') or self.is_specified('part_MeleeWeapon'):
            val = self.part_MeleeWeapon_Skill
        if self.inherits_from('MissileWeapon'):
            val = self.part_MissileWeapon_Skill
        if self.part_Gaslight:
            val = self.part_Gaslight_ChargedSkill
        return val

    @property
    def strength(self):
        """The strength the mutation affects, or the strength of the creature."""
        return self.attribute_helper('Strength')

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
        val = self.name
        if self.part_Render_DisplayName:
            val = escape_ampersands(self.part_Render_DisplayName)
        return val

    @property
    def tohit(self):
        """The bonus or penalty to hit."""
        if self.inherits_from('Armor'):
            return self.part_Armor_ToHit

    @property
    def toughness(self):
        """The toughness the mutation affects, or the toughness of the creature."""
        return self.attribute_helper('Toughness')

    @property
    def twohanded(self):
        """Whether this is a two-handed item."""
        if self.inherits_from('MeleeWeapon') or self.inherits_from('MissileWeapon'):
            if self.tag_UsesSlots and self.tag_UsesSlots != 'Hand':
                return None  # exclude things like Slugsnout Snout
            if self.part_Physics_bUsesTwoSlots:
                return 'yes'
            return 'no'

    @property
    def unpowereddamage(self):
        """For weapons that use charge, the damage dealt when unpowered."""
        dam = None
        if self.part_Gaslight:
            dam = self.part_Gaslight_UnchargedDamage
        return dam

    @property
    def usesslots(self):
        return self.tag_UsesSlots_Value

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
        return self.attribute_helper('Willpower')

    @property
    def wornon(self):
        """The slot(s) that an item gets equipped to."""
        wornon = None
        if self.part_Shield_WornOn:
            wornon = self.part_Shield_WornOn
        if self.part_Armor_WornOn:
            wornon = self.part_Armor_WornOn
        return wornon
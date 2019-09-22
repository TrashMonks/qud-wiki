import re

from hagadias.constants import BIT_TRANS, ITEM_MOD_PROPS
from hagadias.helpers import DiceBag, cp437_to_unicode
from hagadias.qudobject import QudObject
from hagadias.svalue import sValue


def strip_qud_color_codes(text: str):
    """Remove Qud color codes like `&Y` from the provided text."""
    return re.sub('&[rRwWcCbBgGmMyYkKoO]', '', text)


class QudObjectProps(QudObject):
    """Represents a Caves of Qud game object with properties to calculate derived stats.

    Inherits from QudObject which does all the lower level work.

    Properties should return Python types where possible (lists, bools, etc.) and leave specific
    representations to a subclass."""

    # PROPERTY HELPERS
    # Helper methods to simplify the calculation of properties, further below.
    # Sorted alphabetically. All return types should be strings.
    def attribute_helper(self, attr: str, mode: str = ''):
        """Helper for retrieving attributes (Strength, etc.)"""
        val = None
        if self.inherits_from('Creature') or self.inherits_from('ActivePlant'):
            if getattr(self, f'stat_{attr}_sValue'):
                val = str(sValue(getattr(self, f'stat_{attr}_sValue'), level=int(self.lv)))
            elif getattr(self, f'stat_{attr}_Value'):
                val = getattr(self, f'stat_{attr}_Value')
            boost = getattr(self, f'stat_{attr}_Boost')
            if boost:
                val += f'+{boost}'
        elif self.inherits_from('Armor'):
            val = getattr(self, f'part_Armor_{attr}')
        if mode in ['Average', 'Modifier']:
            val = DiceBag(val).average()  # calculate average stat value
            val = int(val * (0.8 if self.role == 'Minion' else 1))  # Minions lose 20% to all stats
        if mode == 'Modifier':
            val = (val - 16) // 2  # return stat modifier for average roll
        return val

    def resistance(self, element):
        """The elemental resistance/weakness the equipment or NPC has.
        Helper function for properties."""
        val = getattr(self, f'stat_{element}Resistance_Value')
        if self.part_Armor:
            if element == "Electric":
                element = "Elec"  # short form in armor
            val = getattr(self, f'part_Armor_{element}')
        return val

    def projectile_object(self, part_attr: str = ''):
        """Retrieve the projectile object for a MissileWeapon or Arrow.
          If part_attr specified, retrieve the specific part attribute
          value from that projectile object instead.

          Doesn't work for bows because their projectile object varies
          depending on the type of arrow loaded into them."""
        if self.part_MissileWeapon is not None or self.is_specified('part_AmmoArrow'):
            parts = ['part_BioAmmoLoader_ProjectileObject',
                     'part_AmmoArrow_ProjectileObject',
                     'part_MagazineAmmoLoader_ProjectileObject',
                     'part_EnergyAmmoLoader_ProjectileObject',
                     'part_LiquidAmmoLoader_ProjectileObject']
            for part in parts:
                attr = getattr(self, part)
                if attr is not None and attr != '':
                    item = self.qindex[attr]
                    if part_attr:
                        return getattr(item, part_attr, None)
                    else:
                        return item
        return None

    # PROPERTIES
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
        ammo = None
        if self.part_MagazineAmmoLoader_AmmoPart:
            ammotypes = {'AmmoSlug': 'lead slug',
                         'AmmoShotgunShell': 'shotgun shell',
                         'AmmoGrenade': 'grenade',
                         'AmmoMissile': 'missile',
                         'AmmoArrow': 'arrow',
                         'AmmoDart': 'dart',
                         }
            ammo = ammotypes.get(self.part_MagazineAmmoLoader_AmmoPart)
        elif self.part_EnergyAmmoLoader_ChargeUse and int(self.part_EnergyAmmoLoader_ChargeUse) > 0:
            if self.part_EnergyCellSocket and self.part_EnergyCellSocket_SlotType == 'EnergyCell':
                ammo = 'energy'
            elif self.part_LiquidFueledPowerPlant:
                ammo = self.part_LiquidFueledPowerPlant_Liquid
        elif self.part_LiquidAmmoLoader:
            ammo = self.part_LiquidAmmoLoader_Liquid
        return ammo

    @property
    def ammodamagetypes(self):
        """Damage attributes associated with the projectile."""
        attributes = self.projectile_object('part_Projectile_Attributes')
        if attributes is not None:
            return attributes.split()

    @property
    def aquatic(self):
        """If the creature requires to be submerged in water."""
        if self.inherits_from('Creature'):
            if self.part_Brain_Aquatic is not None:
                return "yes" if self.part_Brain_Aquatic == "true" else "no"

    @property
    def av(self):
        """The AV that an item provides, or the AV that a creature has."""
        av = None
        if self.part_Armor_AV:  # the AV of armor
            av = self.part_Armor_AV
        if self.part_Shield_AV:  # the AV of a shield
            av = self.part_Shield_AV
        if self.inherits_from('Creature') or self.inherits_from('Wall'):
            # the AV of creatures and stationary objects
            av = int(self.stat_AV_Value)  # first, creature's intrinsic AV
            if self.inventoryobject:
                # might be wearing armor
                for name in list(self.inventoryobject.keys()):
                    if name[0] in '*#@':
                        # special values like '*Junk 1'
                        continue
                    item = self.qindex[name]
                    if item.av:
                        av += int(item.av)
        if av is not None:
            return str(av)
        else:
            return None

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
            return 'no'  # it's interesting if an item can't be disassembled but can be built

    @property
    def carrybonus(self):
        """The carry weight bonus."""
        return self.part_Armor_CarryBonus

    @property
    def chargeperdram(self):
        """How much charge is available per dram (for liquid cells)."""
        return self.part_LiquidFueledEnergyCell_ChargePerDram

    @property
    def chargeused(self):
        """How much charge is used per shot."""
        charge = None
        if self.part_VibroWeapon and int(self.part_VibroWeapon_ChargeUse) > 0:
            charge = self.part_VibroWeapon_ChargeUse
        if self.part_Gaslight and int(self.part_Gaslight_ChargeUse) > 0:
            charge = self.part_Gaslight_ChargeUse
        parts = ['StunOnHit',
                 'EnergyAmmoLoader',
                 'MechanicalWings',
                 'GeomagneticDisk',
                 'ProgrammableRecoiler',
                 'Teleporter',
                 'LatchesOn']
        for part in parts:
            if getattr(self, f'part_{part}'):
                charge = getattr(self, f'part_{part}_ChargeUse')
        return charge

    @property
    def chargefunction(self):
        """The features or functions that the charge is used for."""
        # intended to provide clarity for items like Prayer Rod, where charge only affects one of
        # its features (stun) and not the other (elemental damage)
        funcs = None
        if self.part_StunOnHit:
            funcs = "Stun effect"
        if self.part_EnergyAmmoLoader or self.part_Gaslight:
            funcs = "Weapon power" if not funcs else funcs + ", weapon power"
        if self.part_VibroWeapon and int(self.part_VibroWeapon_ChargeUse) > 0:
            funcs = "Adaptive penetration" if not funcs else funcs + ", adaptive penetration"
        if self.part_MechanicalWings:
            funcs = "Flight" if not funcs else funcs + ", flight"
        if self.part_GeomagneticDisk:
            funcs = "Disc effect" if not funcs else funcs + ", disc effect"
        if self.part_ProgrammableRecoiler or self.part_Teleporter:
            funcs = "Teleportation" if not funcs else funcs + ", teleportation"
        return funcs

    @property
    def cold(self):
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance('Cold')

    @property
    def colorstr(self):
        """The Qud color code associated with the RenderString."""
        if self.part_Render_ColorString:
            return self.part_Render_ColorString
        if self.part_Gas_ColorString:
            return self.part_Gas_ColorString

    @property
    def commerce(self):
        """The value of the object."""
        if self.inherits_from('Item') or self.inherits_from('BaseThrownWeapon'):
            return self.part_Commerce_Value

    @property
    def complexity(self):
        """The complexity of the object, used for psychometry."""
        if self.part_Examiner_Complexity is None:
            val = 0
        else:
            val = int(self.part_Examiner_Complexity)
        if self.part_AddMod_Mods is not None:
            modprops = ITEM_MOD_PROPS
            for mod in self.part_AddMod_Mods.split(','):
                if mod in modprops:
                    if (modprops[mod]['ifcomplex'] is True) and (val <= 0):
                        continue  # no change because the item isn't already complex
                    val += int(modprops[mod]['complexity'])
        for key in self.part.keys():
            if key.startswith('Mod'):
                modprops = ITEM_MOD_PROPS
                if key in modprops:
                    if (modprops[key]['ifcomplex'] is True) and (val <= 0):
                        continue  # ditto
                    val += int(modprops[key]['complexity'])
        if val > 0 or self.canbuild == 'yes':
            return val

    @property
    def cookeffect(self):
        """The possible cooking effects of an item."""
        ingred_type = self.part_PreparedCookingIngredient_type
        if ingred_type is not None:
            return ingred_type.split(',')

    @property
    def corpse(self):
        """What corpse a character drops."""
        if self.part_Corpse_CorpseBlueprint is not None and int(self.part_Corpse_CorpseChance) > 0:
            return self.part_Corpse_CorpseBlueprint

    @property
    def corpsechance(self):
        """The chance of a corpse dropping, if corpsechance is >0"""
        if self.part_Corpse_CorpseChance is not None and int(self.part_Corpse_CorpseChance) > 0:
            return self.part_Corpse_CorpseChance

    @property
    def cursed(self):
        """If the item cannot be removed by normal circumstances."""
        if self.part_Cursed is not None:
            return 'yes'

    @property
    def damage(self):
        """The damage dealt by this object."""
        val = None
        if self.inherits_from('MeleeWeapon') or self.is_specified('part_MeleeWeapon'):
            val = self.part_MeleeWeapon_BaseDamage
        if self.part_Gaslight:
            val = self.part_Gaslight_ChargedDamage
        if self.is_specified('part_ThrownWeapon'):
            if self.is_specified('part_GeomagneticDisk'):
                val = self.part_GeomagneticDisk_Damage
            else:
                val = self.part_ThrownWeapon_Damage
        projectiledamage = self.projectile_object('part_Projectile_BaseDamage')
        if projectiledamage:
            val = projectiledamage
        return val

    @property
    def demeanor(self):
        """The demeanor of the creature."""
        if self.inherits_from('Creature') or self.inherits_from('ActivePlant'):
            if self.part_Brain_Calm is not None:
                return "docile" if self.part_Brain_Calm.lower() == "true" else "neutral"
            if self.part_Brain_Hostile is not None:
                return "aggressive" if self.part_Brain_Hostile.lower() == "true" else "neutral"

    @property
    def desc(self):
        """The short description of the object, with color codes included (ampersands escaped)."""
        desc = None
        if self.part_Description_Short == 'A hideous specimen.':
            pass  # hide items with no description
        elif self.intproperty_GenotypeBasedDescription is not None:
            desc = f"[True kin]\n{self.property_TrueManDescription_Value}\n\n" \
                   f"[Mutant]\n{self.property_MutantDescription_Value}"
        elif self.part_Description_Short:
            if self.part_Description_Mark:
                desc = self.part_Description_Short + "\n\n" + self.part_Description_Mark
            else:
                desc = self.part_Description_Short
        if desc is not None:
            if self.part_BonusPostfix is not None:
                desc += "\n\n" + self.part_BonusPostfix_Postfix
            desc = desc.replace('\r\n', '\n')  # currently, only the description for Bear
        return desc

    @property
    def destroyonunequip(self):
        """If the object is destroyed on unequip."""
        if self.part_DestroyOnUnequip is not None:
            return 'yes'

    @property
    def displayname(self):
        """The display name of the object, with color codes removed. Used in UI and wiki."""
        dname = ""
        if self.part_Render_DisplayName is not None:
            dname = self.part_Render_DisplayName
            dname = strip_qud_color_codes(dname)
        return dname

    @property
    def dramsperuse(self):
        """The number of drams of liquid consumed by each shot action."""
        if self.is_specified('part_LiquidAmmoLoader'):
            return 1  # LiquidAmmoLoader always uses 1 dram per action
        # TODO: calculate fractional value for blood-gradient hand vacuum

    @property
    def dv(self):
        """The Dodge Value of this object."""
        dv = None
        if self.inherits_from('Armor'):
            # the 'DV' we are interested in is the DV modifier of the armor
            dv = self.part_Armor_DV
        if self.inherits_from('Shield'):
            # same here
            dv = self.part_Shield_DV
        elif self.inherits_from('Wall'):
            dv = -10
        elif self.inherits_from('Creature'):
            # the 'DV' here is the actual DV of the creature or NPC, after:
            # base of 6 plus any explicit DV bonus,
            # skills, agility modifier (which may be a range determined by
            # dice rolls, and which changes DV by 1 for every 2 points of agility
            # over/under 16), and any equipment that is guaranteed to be worn
            if self.is_specified('part_Brain_Mobile') and (self.part_Brain_Mobile == 'false' or
                                                           self.part_Brain_Mobile == 'False'):
                dv = -10
            else:
                dv = 6
                if self.stat_DV_Value:
                    dv += int(self.stat_DV_Value)
                if self.skill_Acrobatics_Dodge:  # the 'Spry' skill
                    dv += 2
                if self.skill_Acrobatics_Tumble:  # the 'Tumble' skill
                    dv += 1
                dv += self.attribute_helper('Agility', 'Modifier')
                # does this creature have armor with DV modifiers?
                if self.inventoryobject:
                    for name in list(self.inventoryobject.keys()):
                        if name[0] in '*#@':
                            # special values like '*Junk 1'
                            continue
                        item = self.qindex[name]
                        if item.dv:
                            dv += int(item.dv)
                # does this creature have mutations that affect DV?
                if self.mutation:
                    for mutation, info in self.mutation.items():
                        if mutation == 'Carapace':
                            lvl = int(info['Level']) + 1
                            dv -= (7 - (lvl // 2))
        return str(dv) if dv else None

    @property
    def dynamictable(self):
        """What dynamic tables the object is a member of.

        Returns a list of strings, the dynamic tables."""
        if self.tag_ExcludeFromDynamicEncounters is not None:
            return None
        tables = []
        for key, val in self.tag.items():
            if key.startswith('DynamicObjectsTable'):
                if 'Value' in val and val['Value'] == '{{{remove}}}':
                    continue  # explicitly blacklisted from an inherited dynamic table
                tables.append(key.split(':')[1])
        return tables if len(tables) > 0 else None

    @property
    def eatdesc(self):
        """The text when you eat this item."""
        return self.part_Food_Message

    @property
    def ego(self):
        """The ego the mutation effects, or the ego of the creature."""
        val = self.attribute_helper('Ego')
        return val + "+3d1" if self.name == "Wraith-Knight Templar" else val

    @property
    def electric(self):
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance('Electric')

    @property
    def elementaldamage(self):
        """The elemental damage dealt, if any."""
        if self.is_specified('part_ModFlaming'):
            tierstr = self.part_ModFlaming_Tier
            elestr = str(int(int(tierstr) * 0.8)) + '-' + str(int(int(tierstr) * 1.2))
        elif self.is_specified('part_ModFreezing'):
            tierstr = self.part_ModFreezing_Tier
            elestr = str(int(int(tierstr) * 0.8)) + '-' + str(int(int(tierstr) * 1.2))
        elif self.is_specified('part_ModElectrified'):
            tierstr = self.part_ModElectrified_Tier
            elestr = str(int(tierstr)) + '-' + str(int(int(tierstr) * 1.5))
        else:
            elestr = self.part_MeleeWeapon_ElementalDamage
        return elestr

    @property
    def elementaltype(self):
        """For elemental damage dealt, what the type of that damage is."""
        if self.is_specified('part_ModFlaming'):
            elestr = 'Fire'
        elif self.is_specified('part_ModFreezing'):
            elestr = 'Cold'
        elif self.is_specified('part_ModElectrified'):
            elestr = 'Electric'
        else:
            elestr = self.part_MeleeWeapon_Element
        return elestr

    @property
    def empsensitive(self):
        """Returns yes if the object is empensitive. Can be found in multiple parts."""
        parts = ['EquipStatBoost',
                 'BootSequence',
                 'NavigationBonus',
                 'SaveModifier',
                 'LiquidFueledPowerPlant',
                 'LiquidProducer',
                 'TemperatureAdjuster',
                 ]
        if any(getattr(self, f'part_{part}_IsEMPSensitive') == 'true' for part in parts):
            return 'yes'

    @property
    def exoticfood(self):
        """When preserved, whether the player must explicitly choose to preserve it."""
        if self.tag_ChooseToPreserve is not None:
            return 'yes'

    @property
    def faction(self):
        """The factions this creature has loyalty to.
        Returned as a list of tuples of faction, value like
        [('Joppa', 100), ('Barathrumites', 100)]"""
        # <part Name="Brain" Wanders="false" Factions="Joppa-100,Barathrumites-100" />
        ret = None
        if self.part_Brain_Factions:
            ret = []
            for part in self.part_Brain_Factions.split(','):
                if '-' in part:
                    # has format like `Joppa-100,Barathrumites-100`
                    faction, value = part.split('-')
                    ret.append((faction, int(value)))
                else:
                    print(f'FIXME: unexpected faction format: {part} in {self.name}')
        return ret

    @property
    def flyover(self):
        """Whether a flying creature can pass over this object."""
        if self.inherits_from('Wall') or self.inherits_from('Furniture'):
            if self.is_specified('tag_Flyover'):
                return 'yes'
            else:
                return 'no'

    @property
    def gasemitted(self):
        """The gas emitted by the weapon (typically missile weapon 'pumps')."""
        return self.projectile_object('part_GasOnHit_Blueprint')

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
        if self.inherits_from('Creature') or self.inherits_from('Wall'):
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
    def illoneat(self):
        """If eating this makes you sick."""
        if not self.inherits_from('Corpse'):
            if self.part_Food_IllOnEat == 'true':
                return 'yes'

    @property
    def image(self):
        """The image filename."""
        if self.part_Render_Tile is None:
            tile = 'none'
        else:
            tile = self.displayname
            tile = re.sub(r"[^a-zA-Z\d ]", '', tile)
            tile = tile.casefold() + '.png'
        return tile

    @property
    def inheritingfrom(self):
        """The ID of the parent object in the Qud object hierarchy."""
        return self.parent.name

    @property
    def intelligence(self):
        """The intelligence the mutation affects, or the intelligence of the creature."""
        return self.attribute_helper('Intelligence')

    @property
    def inventory(self):
        """The inventory of a character.

        Returns a list of tuples of strings: (name, count, equipped, chance)."""
        inv = self.inventoryobject
        if inv is not None:
            ret = []
            for name in inv:
                if name[0] in '*#@':  # Ignores stuff like '*Junk 1'
                    continue
                count = inv[name].get('Number', '1')
                equipped = 'no'  # not yet implemented
                chance = inv[name].get('Chance', '100')
                ret.append((name, count, equipped, chance))
            return ret

    @property
    def isfungus(self):
        """If the food item contains fungus."""
        if self.tag_Mushroom is not None:
            return 'yes'

    @property
    def ismeat(self):
        """If the food item contains meat."""
        if self.tag_Meat is not None:
            return 'yes'

    @property
    def isplant(self):
        """If the food item contains plants."""
        if self.tag_Plant is not None:
            return 'yes'

    @property
    def lightprojectile(self):
        """If the gun fires light projectiles (heat immune creatures will not take damage)."""
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
        ma = None
        if self.inherits_from('Wall'):
            return 0
        elif self.inherits_from('Creature'):
            # MA starts at base 4
            ma = 4
            # Add MA stat value if specified
            if self.stat_MA_Value:
                ma += int(self.stat_MA_Value)
            # add willpower modifier to MA
            ma += self.attribute_helper('Willpower', 'Modifier')
        return ma

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
        if self.is_specified('part_ThrownWeapon'):
            if self.part_ThrownWeapon_Penetration is not None:
                return self.part_ThrownWeapon_Penetration
            else:
                return '1'
        else:
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
    def modcount(self):
        ret = 0
        if self.part_AddMod_Mods is not None:
            ret += len(self.part_AddMod_Mods.split(","))
        for key in self.part.keys():
            if key.startswith('Mod'):
                ret += 1
        if ret > 0:
            return ret
        return None

    @property
    def mods(self):
        """Mods that are attached to the current item.

        Returns a list of tuples of strings (modid, tier).
        """
        mods = []
        if self.part_AddMod_Mods is not None:
            names = self.part_AddMod_Mods.split(',')
            if self.part_AddMod_Tiers is not None:
                tiers = self.part_AddMod_Tiers.split(',')
            else:
                tiers = [1] * len(names)
            mods.extend(zip(names, tiers))
        for key in self.part.keys():
            if key.startswith('Mod'):
                if 'Tier' in self.part[key]:
                    mods.append((key, self.part[key]['Tier']))
                else:
                    mods.append((key, '1'))
        return mods if len(mods) > 0 else None

    @property
    def movespeed(self):
        """returns movespeed bonus, if an item"""
        if self.inherits_from('Creature'):
            return self.stat_MoveSpeed_Value

    @property
    def movespeedbonus(self):
        if self.inherits_from('Item'):
            if self.part_MoveCostMultiplier is not None:
                temp = ""
                if int(self.part_MoveCostMultiplier_Amount) < 0:
                    temp = "+"
                return temp + str(int(self.part_MoveCostMultiplier_Amount) * -1)

    @property
    def mutations(self):
        """The mutations the creature has along with their level.

        Returns a list of tuples of strings (name, level)."""
        if self.mutation is not None:
            mutations = []
            for mutation, data in self.mutation.items():
                postfix = f"{data['GasObject']}" if 'GasObject' in data else ''
                level = data['Level'] if 'Level' in data else '0'
                mutations.append((mutation + postfix, level))
            return mutations

    @property
    def omniphaseprojectile(self):
        projectile = self.projectile_object()
        if projectile.is_specified('part_OmniphaseProjectile') or \
                projectile.is_specified('tag_Omniphase'):
            return 'yes'

    @property
    def oneat(self):
        """Effects granted when the object is eaten.

        Returns a list of strings, which are the effects.
        Example:
            Transform <part Name="BreatheOnEat" Class="FireBreather" Level="5"></part>
            into ['BreatheOnEatFireBreather5']"""
        effects = []
        for key, val in self.part.items():
            if key.endswith('OnEat'):
                effect = key
                if 'Class' in val:
                    effect += val['Class']
                    effect += val['Level']
                effects.append(effect)
        return effects if len(effects) > 0 else None

    @property
    def penetratingammo(self):
        """If the missile weapon's projectiles pierce through targets."""
        if self.projectile_object('part_Projectile_PenetrateCreatures') is not None:
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
    def pronouns(self):
        """returns the pronounset of a creature, if they have any."""
        if self.tag_PronounSet_Value is not None and self.inherits_from('Creature'):
            return self.tag_PronounSet_Value

    @property
    def pv(self):
        """The base PV, which is by default 4 if not set. Optional."""
        pv = None
        if self.inherits_from('MeleeWeapon') or self.is_specified('part_MeleeWeapon'):
            pv = 4
            if self.part_Gaslight_ChargedPenetrationBonus:
                pv += int(self.part_Gaslight_ChargedPenetrationBonus)
            elif self.part_MeleeWeapon_PenBonus:
                pv += int(self.part_MeleeWeapon_PenBonus)
        missilepv = self.projectile_object('part_Projectile_BasePenetration')
        if missilepv is not None:
            pv = int(missilepv) + 4  # add base 4 PV
        if pv is not None:
            return str(pv)

    @property
    def pvpowered(self):
        """Whether the object's PV changes when it is powered."""
        if ((self.vibro == 'yes' and
             (not self.part_VibroWeapon or int(self.part_VibroWeapon_ChargeUse) > 0)) or
                (self.part_Gaslight and int(self.part_Gaslight_ChargeUse) > 0)):
            return 'yes'

    @property
    def quickness(self):
        """returns quickness if a creature"""
        if self.inherits_from('Creature'):
            return self.stat_Speed_Value

    @property
    def reflect(self):
        """If it reflects, what percentage of damage is reflected."""
        return self.part_ModGlassArmor_Tier

    @property
    def renderstr(self):
        """The character used to render this object in ASCII mode."""
        render = None
        if self.part_Render_RenderString and len(self.part_Render_RenderString) > 1:
            # some RenderStrings are given as CP437 character codes in base 10
            render = cp437_to_unicode(int(self.part_Render_RenderString))
        elif self.part_Gas is not None:
            render = '▓'
        elif self.part_Render_RenderString is not None:
            render = self.part_Render_RenderString
        return render

    @property
    def reputationbonus(self):
        """Reputation bonuses granted by the object.

        Returns a list of tuples of strings (faction, value)."""
        # Examples of XML source formats:
        # <part Name="AddsRep" Faction="Apes" Value="-100" />
        # <part Name="AddsRep" Faction="Antelopes,Goatfolk" Value="100" />
        # <part Name="AddsRep" Faction="Fungi:200,Consortium:-200" />
        if self.part_AddsRep:
            reps = []
            for part in self.part_AddsRep_Faction.split(','):
                if ':' in part:
                    # has format like `Fungi:200,Consortium:-200`
                    faction, value = part.split(':')
                else:
                    # has format like `Antelopes,Goatfolk` and Value `100`
                    # or is a single faction, like `Apes` and Value `-100`
                    faction = part
                    value = self.part_AddsRep_Value
                reps.append((faction, value))
            return reps

    @property
    def role(self):
        """returns the role of the creature."""
        return self.property_Role_Value

    @property
    def savemodifier(self):
        """Returns save modifier type"""
        return self.part_SaveModifier_Vs

    @property
    def savemodifieramt(self):
        """returns amount of the save modifer."""
        if self.part_SaveModifier_Vs is not None:
            return self.part_SaveModifier_Amount

    @property
    def shotcooldown(self):
        """Cooldown before weapon can be fired again, typically a dice string."""
        return self.part_CooldownAmmoLoader_Cooldown

    @property
    def shots(self):
        """How many shots are fired in one round."""
        return self.part_MissileWeapon_ShotsPerAction

    @property
    def solid(self):
        if self.is_specified('part_Physics_Solid'):
            if self.part_Physics_Solid == 'true' or self.part_Physics_Solid == 'True':
                return 'yes'
            else:
                return 'no'

    @property
    def spectacles(self):
        """If the item corrects vision."""
        return 'yes' if self.part_Spectacles is not None else None

    @property
    def temponenter(self):
        """Temperature change caused to objects when weapon/projectile passes through cell."""
        var = self.projectile_object('part_TemperatureOnEntering_Amount')  # projectiles
        return var or self.part_TemperatureOnEntering_Amount  # melee weapons, etc.

    @property
    def temponhit(self):
        """Temperature change caused by weapon/projectile hit."""
        var = self.projectile_object('part_TemperatureOnHit_Amount')
        return var or self.part_TemperatureOnHit_Amount

    @property
    def temponhitmax(self):
        """Temperature change effect does not occur if target has already reached MaxTemp."""
        var = self.projectile_object('part_TemperatureOnHit_MaxTemp')
        return var or self.part_TemperatureOnHit_MaxTemp

    @property
    def weaponskill(self):
        """The skill tree required for use."""
        val = None
        if self.inherits_from('MeleeWeapon') or self.is_specified('part_MeleeWeapon'):
            val = self.part_MeleeWeapon_Skill
        if self.inherits_from('MissileWeapon'):
            if self.part_MissileWeapon_Skill is not None:
                val = self.part_MissileWeapon_Skill
        if self.part_Gaslight:
            val = self.part_Gaslight_ChargedSkill
        # disqualify various things from showing the 'cudgel' skill:
        if self.inherits_from('Projectile'):
            val = None
        if self.inherits_from('Shield'):
            val = 'Shield'
        return val

    @property
    def skills(self):
        """The skills that certain creatures have."""
        if self.skill is not None:
            return self.skill

    @property
    def strength(self):
        """The strength the mutation affects, or the strength of the creature."""
        return self.attribute_helper('Strength')

    @property
    def swarmbonus(self):
        return self.part_Swarmer_ExtraBonus

    @property
    def isswarmer(self):
        if self.inherits_from('Creature'):
            return 'yes' if self.is_specified('part_Swarmer') else None

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
        if self.builder_GoatfolkHero1_ForceName:
            val = self.builder_GoatfolkHero1_ForceName  # for Mamon
        elif self.name == "Wraith-Knight Templar":
            val = "&MWraith-Knight Templar of the Binary Honorum"  # override for Wraith Knights
        elif self.part_Render_DisplayName:
            val = self.part_Render_DisplayName
        mods = QudObjectProps.mods.fget(self)  # seems necessary to avoid inheritance ambiguity
        if mods is not None and self.xtag_Grammar_Proper != 'true':  # prepend mod prefixes
            modprops = ITEM_MOD_PROPS
            modprefixes = ''
            modpostfixes = ''
            for mod, tier in mods:
                if mod in modprops:
                    if 'prefix' in modprops[mod]:
                        if mod == 'ModCounterweighted' and int(tier) > 2:  # special handling
                            modprefixes += '&ycounterweighted(' + str((int(tier) + 3) // 3) + ') '
                        else:
                            modprefixes += modprops[mod]['prefix']
                    if 'postfix' in modprops[mod]:
                        modpostfixes += modprops[mod]['postfix']
            val = (modprefixes if modprefixes != '' else '') \
                + val + (modpostfixes if modpostfixes != '' else '')
        return val

    @property
    def tohit(self):
        """The bonus or penalty to hit."""
        if self.inherits_from('Armor'):
            return self.part_Armor_ToHit
        if self.is_specified('part_MeleeWeapon'):
            return self.part_MeleeWeapon_HitBonus

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
        if self.tag_UsesSlots_Value:
            return self.tag_UsesSlots_Value.replace(',', ', ')

    @property
    def vibro(self):
        """Whether this is a vibro weapon."""
        if self.is_specified('part_ThrownWeapon'):
            if self.is_specified('part_GeomagneticDisk'):
                return 'yes'
            else:
                return 'no'
        elif self.inherits_from('NaturalWeapon') or self.inherits_from('MeleeWeapon'):
            if self.part_VibroWeapon:
                return 'yes'
            return 'no'

    @property
    def weight(self):
        """The weight of the object."""
        if not self.inherits_from('Creature'):
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
        if self.name == 'Hooks':
            wornon = 'Feet'  # manual fix
        return wornon

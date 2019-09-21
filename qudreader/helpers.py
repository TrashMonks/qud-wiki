"""Helper functions for Qud Blueprint Explorer."""

import os
import re

# load and store the Code Page 437->Unicode translation
CP437_MAP_FILE = os.path.join(os.path.dirname(__file__), 'IBMGRAPH.TXT')
cp437_conv = {}
with open(CP437_MAP_FILE) as f:
    for line in f.readlines():
        if not line.startswith('#'):
            unicode, cp437, *_ = line.split()
            cp437_conv[int(cp437, base=16)] = chr(int(unicode, base=16))


def cp437_to_unicode(val: int):
    """Convert an IBM Code Page 437 code point to its Unicode equivalent.

    See https://stackoverflow.com/questions/46942721/is-cp437-decoding-broken-for-control-characters
    """
    if val > 0x1f:
        # no control characters, just ascii and "upper ascii"
        hex_val = hex(val)[2:]
        if len(hex_val) == 1:
            hex_val = '0' + hex_val
        byte = bytes.fromhex(hex_val)
        glyph = byte.decode(encoding='cp437')
    else:
        # control character - must be loaded from table
        glyph = cp437_conv[val]
    return glyph


class EquipBrain:
    """Loads a creature, analyzes its body parts and inventory, and determines what it would
    probably equip in-game.

    Designed to support only BaseHumanoids right now. To go beyond BaseHumanoid, we'd also need
    to support more body parts (Roots, Tail, Tread, etc.) and more mutations (SlogGlands, etc.)

    Essentially, this class should mimic XRL.World.Parts.Brain.PerformReequip() to as much extent
    as possible.

    Parameters:
        creature: The QudObject reference to the creature we're equipping"""

    class EquippedItem:
        """Represents a single equipped item. (conceptual only at the moment, not currently used)

        Parameters:
            item: qud object name
            type: 'armor' or 'weapon' or 'shield'
            score: equipment score for the item, higher is better, can be negative or positive
            canequip: True if it can be equipped, False if it can't be """

        def __init__(self, item: str, type: str, score: int, canequip: bool):
            self.item = item
            self.type = type
            self.score = score
            self.canequip = canequip

    def __init__(self, creature):
        self.creature = creature
        self.equippable_body_slots = {'Arm': 2, 'Back': 1, 'Body': 1, 'Face': 1, 'Feet': 1,
                                      'Floating Nearby': 1, 'Hand': 2, 'Hands': 1, 'Head': 1 }
        self.equipped_items = {'Arm': [], 'Back': [], 'Body': [], 'Face': [], 'Feet': [],
                               'Floating Nearby': [], 'Hand': [], 'Hands': [], 'Head': [] }
        # does this creature have mutations that affect equippable body parts?
        if self.creature.mutation:
            for mutation, info in self.creature.mutation.items():
                if mutation == 'MultipleArms':
                    self.equippable_body_slots['Arm'] += 2
                    self.equippable_body_slots['Hand'] += 2
                    self.equippable_body_slots['Hands'] += 1
                if mutation == 'MultipleLegs':
                    self.equippable_body_slots['Feet'] += 1
                if mutation == 'TwoHeaded':
                    self.equippable_body_slots['Head'] += 1
                if mutation == 'Carapace' or mutation == 'Quills':
                    self.equippable_body_slots['Body'] -= 1
                if mutation == 'Stinger' or mutation == 'Wings':
                    self.equippable_body_slots['Back'] -= 1
                if mutation == 'BurrowingClaws' or mutation == 'FlamingHands'\
                   or mutation == 'FreezingHands':
                    self.equippable_body_slots['Hands'] -= 1
                if mutation == 'Horns':
                    self.equippable_body_slots['Head'] -= 1
        # figure out what should be equipped in each slot
        for key, val in iter(self.equippable_body_slots.items()):
            # not yet implemented
            _ = 1

    def get_items_for_slot(self, slot: str, type: str):
        # not yet fully implemented
        type = type or ''
        for name in list(self.creature.inventoryobject.keys()):
            if name[0] in '*#@':
                # special values like '*Junk 1'
                continue
            item = qindex[name]
            # assume the hand is the primary weapon slot
            #if slot == 'Hand' and item.inherits_from('MeleeWeapon'):

    def can_equip_armor(self, armor_item):
        part = armor_item.wornon
        if part in self.equippable_body_slots:
            if self.equippable_body_slots[part] > 0:
                return True
        return False

    def is_armor(self, armor_item):
        if armor_item.part_Armor_WornOn:
            return True
        return False

    def armor_score(self, armor_item):
        """returns the equip favorability score for an armor item.
        loosely based on XRL.World.Parts.Brain.ArmorScore()

        This method has been tested and appears to work as expected.

        Parameters:
            armor_item: The QudObject reference to the armor object we're considering equipping
        """
        score = 0.0
        score += float(armor_item.heat or 0.0) + float(armor_item.cold or 0.0)
        score += float(armor_item.acid or 0.0) + float(armor_item.electric or 0.0)
        score += float(armor_item.strength or 0.0) * 5 + float(armor_item.intelligence or 0.0)
        score += float(armor_item.ego or 0.0) * 2
        score += float(armor_item.tohit or 0.0) * 10
        score -= float(armor_item.attribute_helper('SpeedPenalty') or 0.0) * 2
        score += float(armor_item.attribute_helper('CarryBonus') or 0.0) / 5
        armor_score = float(armor_item.av or 0.0)
        dodge_score = float(armor_item.dv or 0.0)
        part = armor_item.wornon
        if part in self.equippable_body_slots:
            slot_count = self.equippable_body_slots[part]
            if slot_count > 0:
                armor_score /= float(slot_count)
                dodge_score /= float(slot_count)
        agi = float(armor_item.agility or 0.0)
        if agi > 0.0:
            score += agi
            dodge_score += agi * 0.5
        if armor_score > 0.0:
            score += armor_score * armor_score * 20.0
        elif armor_score < 0.0:
            score += armor_score * 40.0
        if dodge_score > 0.0:
            score += dodge_score * dodge_score * 10.0
        elif dodge_score < 0.0:
            score += dodge_score * 20.0
        if armor_item.tag_UsesSlots_Value:
            parts = len(armor_item.tag_UsesSlots_Value.split())
            score = score * 2.0 / float(parts + 1)
        if armor_item.metal == 'yes':
            score -= abs(score / 20.0)
        print("armor_score for " + armor_item.id + ":     " + str(round(score)))
        print("      [owned by " + self.creature.id + "]")
        return int(round(score))

    def is_new_weap_better_for_primary_hand(self, new_weap, old_weap):
        """returns true if new_weap is considered a better candidate for equipping in the primary
           weapon hand than old_weap. Loosely based on XRL.World.Parts.Brain.CompareWeapons()

        This method should be fully implemented, though it has not yet been extensively tested.

        Parameters:
            new_weap: The QudObject reference to the new weapon object we're considering equipping
            old_weap: The QudObject reference to the old weapon object
        """
        if (new_weap.tag_AlwaysEquip is not None) != (old_weap.tag_AlwaysEquip is not None):
            return (new_weap.tag_AlwaysEquip is not None)
        newVal = new_weap.tag_NaturalWeapon is not None and new_weap.tag_UndesireableWeapon is None
        oldVal = old_weap.tag_NaturalWeapon is not None and old_weap.tag_UndesireableWeapon is None
        if newVal != oldVal:
            return newVal
        if (new_weap.part_MissileWeapon is None) != (old_weap.part_MissileWeapon is None):
            return (new_weap.part_MissileWeapon is None)
        if (new_weap.part_ThrownWeapon is None) != (old_weap.part_ThrownWeapon is None):
            return (new_weap.part_ThrownWeapon is None)
        if (new_weap.part_Food is None) != (old_weap.part_Food is None):
            return (new_weap.part_Food is None)
        if (new_weap.part_Armor is None) != (old_weap.part_Armor is None):
            return (new_weap.part_Armor is None)
        newVal = self.weapon_score(new_weap)
        oldVal = self.weapon_score(old_weap)
        return newVal > oldVal

    def weapon_score(self, weapon_item):
        """returns the equip favorability score for a weapon.
        loosely based on XRL.World.Parts.Brain.WeaponScore()

        This method should be fully implemented, though it has not yet been extensively tested.

        Parameters:
            weapon_item: The QudObject reference to the weapon object we're considering equipping
        """
        if weapon_item.part_Physics_Category == 'Ammo':
            return 0
        if weapon_item.part_MeleeWeapon is None:
            return 0
        damagedice = DiceBag(getattr(weapon_item, 'part_MeleeWeapon_BaseDamage', 5))
        damagescore = damagedice.minimum() * 2 + damagedice.maximum()
        damagescore *= int(getattr(weapon_item, 'part_MeleeWeapon_PenBonus', 0)) + 1
        if weapon_item.part_MeleeWeapon_ElementalDamage:
            elementaldice = DiceBag(getattr(weapon_item, 'part_MeleeWeapon_ElementalDamage', 0))
            damagescore += (elementaldice.minimum() * 2 + elementaldice.maximum()) * 2
        accuracyscore = 50 + 5 * getattr(weapon_item, 'part_MeleeWeapon_HitBonus', 0)
        accuracyscore += 5 * self.creature.attribute_helper('Agility', 'Modifier')
        if weapon_item.part_MeleeWeapon_Skill is not None:
            weapskill = weapon_item.part_MeleeWeapon_Skill
            weapskill = weapskill if weapskill != 'LongBlades' else 'LongBlades2'
            print('weapskill=' + weapskill + "  creature.super().skills=")
            print(self.creature.super().skills)  # test to see if this works right
            if weapskill in self.creature.super().skills:
                accuracyscore += 15 if weapskill == 'ShortBlades' else 20
        accuracyscore = accuracyscore if accuracyscore < 100 else 100
        accuracyscore = accuracyscore if accuracyscore > 5 else 5
        finalscore = damagescore * accuracyscore // 50
        if weapon_item.part_Physics_bUsesTwoSlots == 'true':
            finalscore = finalscore * 2 // 3
        elif weapon_item.tag_UsesSlots is not None:
            finalscore = finalscore * 2 // weapon_item.tag_UsesSlots.count(',') + 2
        if weapon_item.part_MeleeWeapon_Ego is not None:
            finalscore += int(weapon_item.part_MeleeWeapon_Ego)
        if weapon_item.part_Physics_Category in ['Melee Weapon', 'Natural Weapon']:
            finalscore += 1
        finalscore += (accuracyscore - 50) // 5
        if weapon_item.tag_AdjustWeaponScore is not None:
            finalscore += int(weapon_item.tag_AdjustWeaponScore)
        if weapon_item.part_DischargeOnHit is not None:
            voltagedice = DiceBag(weapon_item.part_DischargeOnHit_Voltage)
            damagedice = DiceBag(weapon_item.part_DischargeOnHit_Damage)
            dischargescore = voltagedice.minimum() // 2 + voltagedice.maximum() // 4
            dischargescore += (damagedice.minimum() + damagedice.maximum() // 2)
            finalscore += dischargescore if dischargescore > 1 else 1
        if weapon_item.part_GrandfatherHorn is not None and self.creature.tag_Cervine is not None:
            finalscore += 10
        if weapon_item.part_StunOnHit is not None:
            stunduration = DiceBag(getattr(weapon_item, 'part_StunOnHit_Duration', '1'))
            stunchance = int(weapon_item.part_StunOnHit_Chance)
            stunsavetarget = int(getattr(weapon_item, 'part_StunOnHit_SaveTarget', 12))
            stunscore = 8 * (stunduration.minimum() * 2 + stunduration.maximum())
            stunscore = stunscore * stunchance * stunsavetarget // 2000
            finalscore +=  stunscore
        return finalscore



class DiceBag:
    """Loads a dice string and provides methods to roll or analyze that string.

    Parameters:
        dice_string: a dice string, such as '1d4', '3d6+1-2d2', or '17'.
    """

    class Die:
        """Represents a single segment of a larger dice string. Numeric values are converted to dice
        rolls for simplicity - for example, '7' becomes '7d1'.

        Parameters:
            quantity: the number of times to roll the die (i.e. '2' if the die string is '2d6')
            size: the number of sides on the die (i.e. '6' if the die string is '2d6')
        """

        def __init__(self, quantity, size):
            self.quantity = quantity
            self.size = size

    # static regex patterns:
    # valid dice string must contain only 0-9, +, -, d, or spaces
    pattern_valid_dice = re.compile(r'[\d\sd+-]+')
    # any dice string segment, generally delimited by + or - (examples: 1d6, +3d2, -4)
    pattern_dice_segment = re.compile(r'[+-]?[^+-]+')
    # a dice string segment that includes 'd' and represents a die roll (examples: 2d3, -1d2)
    pattern_die_roll = re.compile(r'^([+-]?\d+)d(\d+)$')
    # a dice string segment that represents a numeric bonus or malus (examples: +3, -1)
    pattern_die_bonus = re.compile(r'^([+-]?\d+)$')

    def __init__(self, dice_string: str):
        if self.pattern_valid_dice.match(dice_string) is None:
            raise ValueError(f"Invalid string for DiceBag ({dice_string})"
                             " - dice string must contain only 0-9, +, -, d, or spaces")
        self.dice_bag = []
        dice_string = "".join(dice_string.split())  # strip all whitespace from dice_string
        dice_iter = self.pattern_dice_segment.finditer(dice_string)
        for die in dice_iter:
            m = self.pattern_die_roll.match(die.group(0))
            if m:
                self.dice_bag.append(DiceBag.Die(float(m.group(1)), float(m.group(2))))
            else:
                m = self.pattern_die_bonus.match(die.group(0))
                if m:
                    self.dice_bag.append(DiceBag.Die(float(m.group(1)), 1.0))
                else:
                    raise ValueError(f"DiceBag created with segment of unsupported format: {die}")

    def average(self):
        """Return the average value that is rolled from this dice string,
        rounded down to the nearest integer."""
        val = 0.0
        for die in self.dice_bag:
            val += die.quantity * (1.0 + die.size) / 2.0
        return int(val)

    def minimum(self):
        """Return the minimum value that can be rolled from this dice string."""
        val = 0.0
        for die in self.dice_bag:
            if die.quantity >= 0:
                val += die.quantity * 1
            else:
                val += die.quantity * die.size
        return int(val)

    def maximum(self):
        """Return the maximum value that can be rolled from this dice string."""
        val = 0.0
        for die in self.dice_bag:
            if die.quantity >= 0:
                val += die.quantity * die.size
            else:
                val += die.quantity * 1
        return int(val)

    def shake(self):
        """Simulate and return a random roll for this dice string."""
        from random import randrange
        val = 0
        for die in self.dice_bag:
            q = int(die.quantity)
            s = int(die.size)
            if q > 0:
                for i in range(q):
                    val += randrange(s) + 1
            elif q < 0:
                for i in range(abs(q)):
                    val -= randrange(s) + 1
        return val
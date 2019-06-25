import re

from qud_object import QudObject


def get_melee_weapon_stats(weapon: QudObject) -> dict:
    """Retrieve display stats for a certain weapon"""
    stats = {}
    stats['title'] = weapon.part_Render_DisplayName
    stats['pv'] = 4
    pen_bonus = weapon.part_MeleeWeapon_PenBonus
    if pen_bonus:
        stats['pv'] += int(pen_bonus)
    pv_bonus = weapon.part_MeleeWeapon_MaxStrengthBonus
    if pv_bonus:
        stats['maxpv'] = stats['pv'] + int(pv_bonus)
    else:
        stats['maxpv'] = stats['pv']
    stats['damage'] = weapon.part_MeleeWeapon_BaseDamage
    stats['commerce'] = weapon.part_Commerce_Value
    stats['id'] = weapon.name
    stats['tier'] = weapon.tag_Tier_Value
    stats['weight'] = weapon.part_Physics_Weight
    stats['desc'] = weapon.part_Description_Short
    two_handed = weapon.part_Physics_bUsesTwoSlots
    stats['twohanded'] = 'true' if two_handed == 'true' else 'false'
    stats['skill'] = weapon.part_MeleeWeapon_Skill

    # fix ampersands for Qud text
    stats['title'] = re.sub('&', '&amp;', stats['title'])
    stats['desc'] = re.sub('&', '&amp;', stats['desc'])
    return stats


def wikify_melee_weapon(stats: dict) -> str:
    """Output the stats for a weapon in wiki format"""
    output = "{{Weapon\n"
    output += "| title = {{Qud text|" + stats['title'] + "}}\n"
    for stat in ('pv', 'maxpv', 'damage', 'commerce', 'id', 'tier', 'weight', 'desc', 'twohanded', 'skill'):
        output += f"| {stat} = {stats[stat]}\n"
    output += "}}\n"
    return output

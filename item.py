import re

from qud_object import QudObject

from config import config
IMAGE_OVERRIDES = config['Image overrides']


def get_item_stats(item: QudObject) -> dict:
    """Retrieve display stats for a certain item"""
    # directly available:
    stats = {'title': item.part_Render_DisplayName,
             'level': item.stat_Level_Value,
             'pv': 4,
             'vibro': 'true' if item.tag_VibroWeapon else 'false',
             'hp': item.stat_Hitpoints_sValue if item.stat_Hitpoints_sValue else item.stat_Hitpoints_Value,
             'av': item.stat_AV_Value,  # for creatures and stationary objects
             'dv': item.stat_DV_Value,
             'ma': item.stat_MA_Value,
             'damage': item.part_MeleeWeapon_BaseDamage,
             'commerce': item.part_Commerce_Value,
             'id': item.name,
             'tier': item.tag_Tier_Value,
             'weight': item.part_Physics_Weight,
             'desc': item.part_Description_Short,
             'two_handed': 'true' if item.part_Physics_bUsesTwoSlots else 'false',
             'skill': item.part_MeleeWeapon_Skill,
             }

    # did we upload something that doesn't match the tile art name?
    if item.name in IMAGE_OVERRIDES:
        stats['image'] = IMAGE_OVERRIDES[item.name]
    else:
        # "Creatures/sw_flower.bmp" becomes "sw_flower.png"
        tile = item.part_Render_Tile.split('/')[-1]
        tile = re.sub('bmp$', 'png', tile)
        stats['image'] = tile

    # penetration bonus (i.e. carbide folding hammer)
    pen_bonus = item.part_MeleeWeapon_PenBonus
    if pen_bonus:
        stats['pv'] += pen_bonus

    # maximum penetration bonus from strength
    pv_bonus = item.part_MeleeWeapon_MaxStrengthBonus
    if pv_bonus:
        stats['maxpv'] = stats['pv'] + pv_bonus
    else:
        stats['maxpv'] = stats['pv']

    # set AV if this is an armor or shield
    if item.part_Armor_AV:
        stats['av'] = item.part_Armor_AV
    if item.part_Shield_AV:
        stats['av'] = item.part_Shield_AV

    # fix ampersands for Qud text
    stats['title'] = re.sub('&', '&amp;', stats['title'])
    stats['desc'] = re.sub('&', '&amp;', stats['desc'])
    return stats


def wikify_item(stats: dict) -> str:
    """Output the stats for an item in wiki format"""
    output = "{{Weapon\n"
    output += "| title = {{Qud text|" + stats['title'] + "}}\n"
    for stat in ('pv', 'maxpv', 'damage', 'commerce', 'id', 'tier', 'weight', 'desc', 'twohanded', 'skill'):
        output += f"| {stat} = {stats[stat]}\n"
    output += "}}\n"
    return output

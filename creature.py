import re

from qud_object import QudObject
from config import config
IMAGE_OVERRIDES = config['Image overrides']


def get_npc_stats(npc: QudObject) -> dict:
    """Retrieve display stats for a certain NPC"""
    # TODO: calculate DV, MA
    stats = {}
    stats['title'] = npc.part_Render_DisplayName
    if npc.name in IMAGE_OVERRIDES:
        # Have we uploaded a special image for this character?
        stats['image'] = IMAGE_OVERRIDES[npc.name]
    else:
        # "Creatures/sw_flower.bmp" becomes "sw_flower.png"
        tile = npc.part_Render_Tile
        tile = tile.split('/')[-1]
        tile = re.sub('bmp$', 'png', tile)
        stats['image'] = tile
    stats['faction'] = npc.part_Brain_Factions
    stats['level'] = npc.stat_Level_Value
    stats['hp'] = npc.stat_Hitpoints_sValue
    # TODO: find out why some attributes are sValue instead of Value (base classes?)
    for k, v in (('av', 'AV'),
                 ('dv', 'DV'),
                 ('ma', 'MA'),
                 ('strength', 'Strength'),
                 ('agility', 'Agility'),
                 ('toughness', 'Toughness'),
                 ('intelligence', 'Intelligence'),
                 ('willpower', 'Willpower'),
                 ('ego', 'Ego'),
                 ('acid', 'AcidResistance'),
                 ('cold', 'ColdResistance'),
                 ('electric', 'ElectricResistance'),
                 ('heat', 'HeatResistance'),
                 ):
        stats[k] = getattr(npc, f'stat_{v}_Value')
    for k, v in (('strength', 'Strength'),
                 ('agility', 'Agility'),
                 ('toughness', 'Toughness'),
                 ('intelligence', 'Intelligence'),
                 ('willpower', 'Willpower'),
                 ('ego', 'Ego'),
                 ):
        sValue = getattr(npc, f'stat_{v}_sValue')
        if sValue is not None:
            stats[k] = sValue
    stats['desc'] = npc.part_Description_Short
    return stats


def wikify_npc(stats: dict) -> str:
    output = "{{Character\n"
    output += "| title = {{Qud text|" + stats['title'] + "}}\n"
    for stat in (
    'image', 'faction', 'level', 'hp', 'av', 'dv', 'ma', 'strength', 'agility', 'toughness',
    'intelligence', 'willpower', 'ego', 'acid', 'cold', 'electric', 'heat', 'desc'):
        output += f"| {stat} = {stats[stat]}\n"
    output += "}}\n"
    return output

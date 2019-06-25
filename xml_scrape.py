import re
import yaml

from xml.etree import ElementTree as et
from pathlib import Path

from anytree import Node, RenderTree, PreOrderIter

from qud_object import QudObject

CONFIG_FILE = "config.yml"
IMAGE_OVERRIDES = {'Asphodel': 'Earl_asphodel.png',
                   }

with open(CONFIG_FILE) as f:
    config = yaml.safe_load(f)

# Do some repair of invalid XML
pattern = re.compile("(&#15;)|(&#11;)")
xmlpath = Path(config['xmlpath'])
repaired = []
with open(xmlpath/'ObjectBlueprints.xml', 'r', encoding='utf-8') as f:
    for line in f:
        repaired.append(pattern.sub('', line))
raw = et.fromstringlist(repaired)


# Build the Qud object hierarchy from the XML data
obj_cache = {}  # for quick reverse lookup of names
for element in raw:
    # if element.tag != 'Object':
    #     continue
    name = element.get('Name')
    parent = element.get('Inherits')
    if parent:
        new = Node(name, parent=obj_cache[parent])
    else:
        print(f"Creating root node {name} from object {element.attrib}")
        new = Node(name)
    obj_cache[name] = new
    for data in element:
        if data.tag in ('xtagGrammar', 'xtagTextFragments', 'inventoryobject', 'xtagWaterRitual'):
            continue  # we don't need this
        if not hasattr(new, data.tag):
            setattr(new, data.tag, {})
        container = getattr(new, data.tag)
        subname = data.attrib.pop('Name')
        container[subname] = data.attrib

# Detach certain nodes
exclude = ('Projectile',)
for _ in exclude:
    obj_cache[_].parent = None


def resolve_attr(node, container, name, attrib):
    """Search the Qud object inheritance graph for the specified attribute.
    Arguments:
        node: the object
        container: part, tag, etc.
        name: specify the name of the container item
        attrib: the attrib to return the value of

    Returns:
        the attribute requested, or None if not found in the graph."""
    if not hasattr(node, container):
        if not node.is_root:
            return resolve_attr(node.parent, container, name, attrib)
        else:
            return None
    if name not in getattr(node, container):
        if not node.is_root:
            return resolve_attr(node.parent, container, name, attrib)
        else:
            return None
    if attrib not in getattr(node, container)[name]:
        if not node.is_root:
            return resolve_attr(node.parent, container, name, attrib)
        else:
            return None
    return getattr(node, container)[name][attrib]


def get_weapon_stats(weapon: str) -> dict:
    """Retrieve display stats for a certain weapon"""
    stats = {}
    stats['title'] = resolve_attr(weapon, 'part', 'Render', 'DisplayName')
    stats['pv'] = 4
    pen_bonus = resolve_attr(weapon, 'part', 'MeleeWeapon', 'PenBonus')
    if pen_bonus:
        stats['pv'] += int(pen_bonus)
    pv_bonus = resolve_attr(weapon, 'part', 'MeleeWeapon', 'MaxStrengthBonus')
    if pv_bonus:
        stats['maxpv'] = stats['pv'] + int(pv_bonus)
    else:
        stats['maxpv'] = stats['pv']
    stats['damage'] = pv_bonus = resolve_attr(weapon, 'part', 'MeleeWeapon', 'BaseDamage')
    stats['commerce'] = resolve_attr(weapon, 'part', 'Commerce', 'Value')
    stats['id'] = weapon.name
    stats['tier'] = resolve_attr(weapon, 'tag', 'Tier', 'Value')
    stats['weight'] = resolve_attr(weapon, 'part', 'Physics', 'Weight')
    stats['desc'] = resolve_attr(weapon, 'part', 'Description', 'Short')
    two_handed = resolve_attr(weapon, 'part', 'Physics', 'bUsesTwoSlots')
    stats['twohanded'] = 'true' if two_handed == 'true' else 'false'
    stats['skill'] = resolve_attr(weapon, 'part', 'MeleeWeapon', 'Skill')

    # fix ampersands for Qud text
    stats['title'] = re.sub('&', '&amp;', stats['title'])
    stats['desc'] = re.sub('&', '&amp;', stats['desc'])
    return stats


def get_npc_stats(npc: Node) -> dict:
    """Retrieve display stats for a certain NPC"""
    # TODO: calculate DV, MA
    stats = {}
    stats['title'] = resolve_attr(npc, 'part', 'Render', 'DisplayName')
    if npc.name in IMAGE_OVERRIDES:
        # Have we uploaded a special image for this character?
        stats['image'] = IMAGE_OVERRIDES[npc.name]
    else:
        # "Creatures/sw_flower.bmp" becomes "sw_flower.png"
        tile = resolve_attr(npc, 'part', 'Render', 'Tile')
        tile = tile.split('/')[-1]
        tile = re.sub('bmp$', 'png', tile)
        stats['image'] = tile
    stats['faction'] = resolve_attr(npc, 'part', 'Brain', 'Factions')
    stats['level'] = resolve_attr(npc, 'stat', 'Level', 'Value')
    stats['hp'] = resolve_attr(npc, 'stat', 'Hitpoints', 'sValue')
    for k, v in (('av', 'AV'),
                 ('dv', 'DV'),
                 ('ma', 'MA')):
        stats[k] = resolve_attr(npc, 'stat', v, 'Value')
    for k, v in (('strength', 'Strength'),
                 ('agility', 'Agility'),
                 ('toughness', 'Toughness'),
                 ('intelligence', 'Intelligence'),
                 ('willpower', 'Willpower'),
                 ('ego', 'Ego')):
        stats[k] = resolve_attr(npc, 'stat', v, 'Value')
        # TODO: find out why some attributes are sValue instead of Value (base classes?)
    for k, v in (('acid', 'AcidResistance'),
                 ('cold', 'ColdResistance'),
                 ('electric', 'ElectricResistance'),
                 ('heat', 'HeatResistance')):
        stats[k] = resolve_attr(npc, 'stat', v, 'Value')
    stats['desc'] = resolve_attr(npc, 'part', 'Description', 'Short')
    return stats


def format_weapon_for_wiki(stats: dict) -> str:
    """Output the stats for a weapon in wiki format"""
    output = "{{Weapon\n"
    output += "| title = {{Qud text|" + stats['title'] + "}}\n"
    for stat in ('pv', 'maxpv', 'damage', 'commerce', 'id', 'tier', 'weight', 'desc', 'twohanded', 'skill'):
        output += f"| {stat} = {stats[stat]}\n"
    output += "}}\n"
    return output


def format_npc_for_wiki(stats: dict) -> str:
    output = "{{Character\n"
    output += "| title = {{Qud text|" + stats['title'] + "}}\n"
    for stat in (
    'image', 'faction', 'level', 'hp', 'av', 'dv', 'ma', 'strength', 'agility', 'toughness',
    'intelligence', 'willpower', 'ego', 'acid', 'cold', 'electric', 'heat', 'desc'):
        output += f"| {stat} = {stats[stat]}\n"
    output += "}}\n"
    return output


object_root = obj_cache['Object']
melee_root = obj_cache['MeleeWeapon']
creature_root = obj_cache['Creature']
for element in PreOrderIter(creature_root):
    print(format_npc_for_wiki(get_npc_stats(element)))

# print(RenderTree(creature_root))

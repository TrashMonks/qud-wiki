import re
import yaml

from xml.etree import ElementTree as et
from pathlib import Path
from pprint import pprint

from anytree import Node, RenderTree, PreOrderIter

CONFIG_FILE = "config.yml"

with open(CONFIG_FILE) as f:
    config = yaml.safe_load(f)

# Do some repair of invalid XML
pattern = re.compile("(&#15;)|(&#11;)")
xmlpath = Path(config['xmlpath'])
repaired = []
with open(xmlpath/'ObjectBlueprints.xml', 'r', encoding='utf-8') as f:
    for line in f:
        repaired.append(pattern.sub('', line))
objects = et.fromstringlist(repaired)


# Build the Qud object hierarchy from the XML data
obj_cache = {}  # for quick reverse lookup of names
for obj in objects:
    name = obj.get('Name')
    parent = obj.get('Inherits')
    if parent:
        new = Node(name, parent=obj_cache[parent])
    else:
        new = Node(name)
    obj_cache[name] = new
    for element in obj:
        if element.tag in ('xtagGrammar', 'xtagTextFragments', 'inventoryobject', 'xtagWaterRitual'):
            continue  # we don't need this
        if not hasattr(new, element.tag):
            setattr(new, element.tag, {})
        container = getattr(new, element.tag)
        subname = element.attrib.pop('Name')
        container[subname] = element.attrib

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
    is_root = not hasattr(node, 'parent')
    if not hasattr(node, container):
        if not is_root:
            return resolve_attr(node.parent, container, name, attrib)
        else:
            return None
    if name not in getattr(node, container):
        if not is_root:
            return resolve_attr(node.parent, container, name, attrib)
        else:
            return None
    if attrib not in getattr(node, container)[name]:
        if not is_root:
            return resolve_attr(node.parent, container, name, attrib)
        else:
            return None
    return getattr(node, container)[name][attrib]


def get_stats(weapon):
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
    stats['twohanded'] = 'yes' if two_handed == 'true' else 'no'
    stats['skill'] = resolve_attr(weapon, 'part', 'MeleeWeapon', 'Skill')
    return stats


def format_weapon_for_wiki(stats):
    """Output the stats for a weapon in wiki format"""
    output = "{{Sandbox/User:Teamtoto/newitem\n"
    output += "| title = {{#invoke: ColorParse | parse|" + stats['title'] + "}}\n"
    for stat in ('pv', 'maxpv', 'damage', 'commerce', 'id', 'tier', 'weight', 'desc', 'twohanded', 'skill'):
        output += f"| {stat} = {stats[stat]}\n"
    output += "}}\n"
    return output


root = obj_cache['MeleeWeapon']
for obj in PreOrderIter(root):
    print(format_weapon_for_wiki(get_stats(obj)))

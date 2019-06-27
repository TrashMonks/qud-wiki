import re
import yaml

from xml.etree import ElementTree as et
from pathlib import Path
from pprint import pprint

from anytree import Node, RenderTree, PreOrderIter

from config import config
from qud_object import QudObject, qindex
from melee_weapon import get_melee_weapon_stats, wikify_melee_weapon
from creature import get_npc_stats, wikify_npc
from item import get_item_stats, wikify_item

# Do some repair of invalid XML
pattern = re.compile("(&#15;)|(&#11;)")
xmlpath = Path(config['xmlpath'])
repaired = []
with open(xmlpath/'ObjectBlueprints.xml', 'r', encoding='utf-8') as f:
    for line in f:
        repaired.append(pattern.sub('', line))
raw = et.fromstringlist(repaired)


# Build the Qud object hierarchy from the XML data
for element in raw:
    if element.tag != 'object':
        continue
    newobj = QudObject(element)

object_root = qindex['Object']
melee_root = qindex['MeleeWeapon']
creature_root = qindex['Creature']
asphodel = qindex['Asphodel']
longsword = qindex['Long Sword']


# Detach certain nodes
exclude = ('Projectile',)
for _ in exclude:
    qindex[_].parent = None


while True:
    query = input("Query: ")
    try:
        print("Raw attributes:")
        pprint(qindex[query].attributes)
        print()
    except KeyError:
        print("Not found in qindex")
    print("Decoded stats:")
    pprint(get_item_stats(qindex[query]))
    # pprint(wikify_item(get_item_stats(qindex[query])))

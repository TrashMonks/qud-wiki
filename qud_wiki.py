import re
import yaml

from xml.etree import ElementTree as et
from pathlib import Path
from pprint import pprint

from anytree import Node, RenderTree, PreOrderIter

from qud_object import QudObject, qindex
from melee_weapon import get_melee_weapon_stats, wikify_melee_weapon
from creature import get_npc_stats, wikify_npc

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
for element in raw:
    if element.tag != 'object':
        continue
    newobj = QudObject(element)

object_root = qindex['Object']
melee_root = qindex['MeleeWeapon']
creature_root = qindex['Creature']
asphodel = qindex['Asphodel']

print(object_root.part_Physics_Conductivity)
print(object_root.part_Physics_Bonductivity)
print(melee_root.part_Physics_Conductivity)
print(asphodel.part_Brain_Factions)

longsword = qindex['Long Sword']
print(get_melee_weapon_stats(longsword))
print(wikify_melee_weapon(get_melee_weapon_stats(longsword)))
print(wikify_npc(get_npc_stats(asphodel)))
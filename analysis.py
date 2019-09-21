"""Various analyses made possible by the Qud object tree and tile rendering system."""
import string

import anytree
import mwclient

import qud_object_tree
import qudtile
import wikipage
from qud_object_tree import qindex

# This script is not part of the main application, so set your XML location here
FILE = 'C:/Steam/steamapps/common/Caves of Qud/CoQ_Data/StreamingAssets/Base/ObjectBlueprints.xml'


def get_bad_tiles():
    print(qindex)
    badset = qudtile.bad_detail_color.intersection(qudtile.uses_details)
    badlist = list(badset)
    print(f'{"Object ID":35} {"Tile":45} {"TileColor":10} {"DetailColor":10}')
    for objname in badlist:
        obj = qindex[objname]
        name = obj.name
        filename = obj.tile.filename
        tilecolor = obj.tile.raw_tilecolor or "(None)"
        detailcolor = obj.tile.raw_detailcolor or "(None)"
        print(f'{name:35} {filename:45} {tilecolor:10} {detailcolor:10}')


def get_wiki_eligible():
    return [name for name, qud_object in qindex.items() if qud_object.is_wiki_eligible]


def get_bugged_eat_messages():
    for name, qud_object in qindex.items():
        if qud_object.eatdesc is not None:
            if qud_object.eatdesc[-1] not in string.ascii_lowercase:
                print(f'{qud_object.name:40} {qud_object.eatdesc}')


def print_wiki_nonwiki():
    for pre, fill, obj in anytree.render.RenderTree(qindex['Object'],
                                                    style=anytree.render.ContRoundStyle):
        print(pre, '✅' if obj.is_wiki_eligible() else '❌', obj.displayname, f'({obj.name})')


def print_wikified_nonwiki():
    """Check the wiki for any articles that aren't supposed to exist."""
    for name, qud_object in qindex.items():
        if not qud_object.is_wiki_eligible():
            try:
                page = wikipage.WikiPage(qud_object)
                if page.page.exists:
                    print(name, page.page.exists, page.page)
            except mwclient.errors.InvalidPageTitle:
                pass


def print_value_weight_ratio():
    """Calculate the value/weight ratio for all items in wiki table format."""


def print_swarmer_creatures():
    """Print a list of creatures with the Swarmer part."""
    for name, qud_object in qindex.items():
        if qud_object.part_Swarmer is not None:
            if qud_object.is_wiki_eligible():
                print(f'{name:30} {qud_object.displayname}')


def print_empty_descriptions():
    for name, qud_object in qindex.items():
        if qud_object.is_wiki_eligible():
            if qud_object.desc is None or qud_object.desc == "":
                print(name, qud_object.desc)


qud_object_tree.load(FILE)

# Run any analyses here:
breakpoint()

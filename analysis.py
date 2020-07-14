"""Various analyses made possible by the Qud object tree and tile rendering system.

This script file is not part of the main project. Some of these may be out of date."""

import string

import anytree
from hagadias import qudtile, gameroot
import mwclient

from qbe.qudobject_wiki import QudObjectWiki
from qbe import wiki_page


def get_bad_tiles():
    """Print a list of tiles using a certain color."""
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
    """Return a list of QudObjects claiming to be wiki-eligible."""
    return [name for name, qud_object in qindex.items() if qud_object.is_wiki_eligible]


def get_bugged_eat_messages():
    """Print a list of OnEat messages that end in punctuation."""
    for name, qud_object in qindex.items():
        if qud_object.eatdesc is not None:
            if qud_object.eatdesc[-1] not in string.ascii_lowercase:
                print(f'{qud_object.name:40} {qud_object.eatdesc}')


def print_wiki_nonwiki():
    """Render a text-based tree that shows which objects are included or excluded from the wiki."""
    for pre, fill, obj in anytree.render.RenderTree(qindex['Object'],
                                                    style=anytree.render.ContRoundStyle):
        print(pre, '✅' if obj.is_wiki_eligible() else '❌', obj.displayname, f'({obj.name})')


def print_wikified_nonwiki():
    """Check the wiki for any articles that aren't supposed to exist."""
    for name, qud_object in qindex.items():
        if not qud_object.is_wiki_eligible():
            try:
                page = wiki_page.WikiPage(qud_object, '(version)')
                if page.page.exists:
                    print(name, page.page.exists, page.page)
            except mwclient.errors.InvalidPageTitle:
                pass


def print_swarmer_creatures():
    """Print a list of creatures with the Swarmer part."""
    for name, qud_object in qindex.items():
        if qud_object.part_Swarmer is not None:
            if qud_object.is_wiki_eligible():
                print(f'{name:30} {qud_object.displayname}')


def print_empty_descriptions():
    """Print a list of objects with no description."""
    for name, qud_object in qindex.items():
        if qud_object.is_wiki_eligible():
            if qud_object.desc is None or qud_object.desc == "":
                print(name, qud_object.desc)


def print_new_and_deleted(qindex, old_qindex):
    """Print numbers of items added and deleted between versions of the game,
    as well as the names of the items."""
    new_objects = [name for name in qindex if name not in old_qindex]
    print("New objects:")
    print(len(new_objects), new_objects)

    deleted_objects = [name for name in old_qindex if name not in qindex]
    print("Deleted objects:")
    print(len(deleted_objects), deleted_objects)


def print_new_tree(root, qindex, old_qindex):
    """Print a tree of only items added in a new version of the game."""
    new_objects = set([name for name in qindex if name not in old_qindex])
    parents_of_new_objects = set()
    for object in new_objects:
        node = qindex[object].parent
        while node is not None:
            if node.name not in new_objects:
                parents_of_new_objects.add(node.name)
            node = node.parent
    for pre, fill, node in anytree.RenderTree(root):
        if node.name in parents_of_new_objects:
            pre_html = '<i>'
            post_html = '</i>'
        if node.name in new_objects:
            pre_html = "'''"
            post_html = "'''"
        if node.name in new_objects or node.name in parents_of_new_objects:
            include = '✅' if node.is_wiki_eligible() else '❌'
            print(f' {pre}{pre_html}{node.name}{post_html} {include}')


# def check_description_coverage(root, qindex):
#     """
#     Check for unique descriptions that do not have wiki coverage.
#     Check for wiki eligible objects with identical descriptions.
#     """


new_gameroot = gameroot.GameRoot(r'C:\Steam\steamapps\common\Caves of Qud')
old_gameroot = gameroot.GameRoot(r'D:\Games\Caves of Qud stable')

gamever = new_gameroot.gamever
stable_gamever = old_gameroot.gamever
print(f'Comparing {gamever} to {stable_gamever}...')

root, qindex = new_gameroot.get_object_tree(QudObjectWiki)
old_root, old_qindex = old_gameroot.get_object_tree()

print_new_tree(root, qindex, old_qindex)

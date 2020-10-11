"""Various analyses made possible by the Qud object tree and tile rendering system.

This script file is not part of the main project. Some of these may be out of date."""

# This import is deliberately placed at the top of analysis.py to guarantee
# that hagadias is able to import ElementTree before any other package does,
# enabling it to switch to the Python-mode XML parser to get line numbers.
from hagadias import gameroot

import string

import anytree
from hagadias import qudtile
import mwclient

from qbe.qudobject_wiki import QudObjectWiki, escape_ampersands
from qbe import wiki_page


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


def diff_stable_beta():
    """Load an old and new instance of the game and call
    print_new_tree on their object trees."""
    new_gameroot = gameroot.GameRoot(r'C:\Steam\steamapps\common\Caves of Qud')
    old_gameroot = gameroot.GameRoot(r'D:\Games\Caves of Qud stable')

    gamever = new_gameroot.gamever
    stable_gamever = old_gameroot.gamever
    print(f'Comparing {gamever} to {stable_gamever}...')

    root, qindex = new_gameroot.get_object_tree(QudObjectWiki)
    old_root, old_qindex = old_gameroot.get_object_tree()

    print_new_tree(root, qindex, old_qindex)


def find_changed_descriptions():
    """Load an old and new instance of the game and report old
    descriptions that have more lines than new ones.
    For finding effect text that has been moved to parts."""
    new_gameroot = gameroot.GameRoot(r'C:\Steam\steamapps\common\Caves of Qud')
    old_gameroot = gameroot.GameRoot(r'D:\Games\Caves of Qud stable')

    gamever = new_gameroot.gamever
    stable_gamever = old_gameroot.gamever
    print(f'Comparing {gamever} to {stable_gamever}...')
    root, qindex = new_gameroot.get_object_tree(QudObjectWiki)
    old_root, old_qindex = old_gameroot.get_object_tree()
    names_in_both = [name for name in qindex if name in old_qindex]
    for name in names_in_both:
        old_desc = old_qindex[name].desc
        desc = qindex[name].desc
        if old_desc is not None and desc is not None and old_desc.count('\n') > desc.count('\n'):
            old_desc = escape_ampersands(old_desc)
            desc = escape_ampersands(desc)
            print(f"""{{{{Qud look|title={name}|text={old_desc}}}}}""")
            print(f"""{{{{Qud look|title={name}|text={desc}}}}}""")
            print('<br><br>')


def find_empty_detailcolor():
    """Find objects that have tiles but empty detailcolor.
    Some objects do this deliberately (e.g. Pools) but physical items should not."""
    root, qindex = gameroot.GameRoot(r'C:\Steam\steamapps\common\Caves of Qud').get_object_tree()
    for name, obj in qindex.items():
        tile = obj.tile  # force tile to render
        if obj.part_Render_Tile is not None:
            if obj.part_Render_DetailColor is None and name in qudtile.uses_details and obj.inherits_from('PhysicalObject'):
                print(name)


find_empty_detailcolor()

# Various analyses made possible by the Qud object tree and tile rendering system.
import string

import anytree

import qud_object_tree
import qudobject
import qudtile

def get_bad_tiles():
    print(qudobject.qindex)
    badset = qudtile.bad_detail_color.intersection(qudtile.uses_details)
    badlist = list(badset)
    print(f'{"Object ID":35} {"Tile":45} {"TileColor":10} {"DetailColor":10}')
    for objname in badlist:
        obj = qudobject.qindex[objname]
        name = obj.name
        filename = obj.tile.filename
        tilecolor = obj.tile.raw_tilecolor or "(None)"
        detailcolor = obj.tile.raw_detailcolor or "(None)"
        print(f'{name:35} {filename:45} {tilecolor:10} {detailcolor:10}')


def get_wiki_eligible():
    return [name for name, qud_object in qudobject.qindex.items() if qud_object.is_wiki_eligible]


def get_bugged_eat_messages():
    for name, qud_object in qudobject.qindex.items():
        if qud_object.eatdesc is not None:
            if qud_object.eatdesc[-1] not in string.ascii_lowercase:
                print(f'{qud_object.name:40} {qud_object.eatdesc}')


def get_wiki_nonwiki():
    # for name, qud_object in qudobject.qindex.items():
    #     print(f'{name:60}{qud_object.displayname:40}{"yes" if qud_object.is_wiki_eligible() else "no"}')
    for pre, fill, obj in anytree.render.RenderTree(qudobject.qindex['Object'], style=anytree.render.ContRoundStyle):
        print(pre, '✅' if obj.is_wiki_eligible() else '❌', obj.displayname, f'({obj.name})')

qud_object_tree.load('C:/Steam/steamapps/common/Caves of Qud/CoQ_Data/StreamingAssets/Base/ObjectBlueprints.xml')

print()
# get_bad_tiles()
# print(get_wiki_eligible())
# get_bugged_eat_messages()
get_wiki_nonwiki()
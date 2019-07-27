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


qud_object_tree.load('C:/Steam/steamapps/common/Caves of Qud/CoQ_Data/StreamingAssets/Base/ObjectBlueprints.xml')
get_bad_tiles()

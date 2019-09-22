# hagadias
Data extractors for the [Caves of Qud](http://www.cavesofqud.com/) roguelike.  

This Python package allows a user to read game data in the raw format used by the
[Caves of Qud](http://www.cavesofqud.com/) roguelike RPG, including the object tree,
fully colored tiles, and character data. It requires an installation of the game to function
properly.

##Usage
```python
from hagadias.gameroot import GameRoot
GAMEPATH = r'C:\Steam\steamapps\common\Caves of Qud'  # Windows
# GAMEPATH = r'~/.local/share/Steam/steamapps/common/Caves of Qud'  # Linux
# GAMEPATH = r'~/Library/Application Support/Steam/steamapps/common/Caves of Qud'  # Mac OS
root = GameRoot(GAMEPATH)

gamecodes = root.get_game_codes()
qud_object_root, qindex = root.get_object_tree()
```

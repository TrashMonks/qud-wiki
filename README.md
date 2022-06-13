# qud-wiki
Data extractors for the [official Caves of Qud wiki](https://wiki.cavesofqud.com/).  

This project reads game data in the raw format used by the [Caves of Qud](http://www.cavesofqud.com/) roguelike RPG, and contains functionality for updating the entire wiki after a game patch with a few clicks. This project uses Python and Qt via the [PySide2](https://wiki.qt.io/Qt_for_Python) library, and uses the [mwclient](https://mwclient.readthedocs.io/en/latest/) library for Mediawiki functionality.  

![screenshot](https://raw.githubusercontent.com/trashmonks/qud-wiki/main/screenshot.png)

**How do I run this**? 
Check the detailed instructions in `CONTRIBUTING.md`.

## Tile support
Tile support requires a full extract of the game Textures directory. To get an up-to-date copy of the game textures, you can install the [brinedump](https://github.com/TrashMonks/brinedump) mod and use the `brinedump:textures` wish to dump an up-to-date version of Textures on your local machine.

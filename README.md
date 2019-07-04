# qud-wiki
Data extractors for the Caves of Qud wiki

What are all these files?

1. `qud_object.py` defines a QudObject that the XML gets parsed into. Has attributes and inheritance trees and everything. Also defines `qindex`, which is a dict to get QudObjects from names quickly.
2. `qud_object_tree.py` is a script that parses all the XML from the xmlpath into QudObjects, so you can then use `qindex` to grab parts of it, etc.
3. `qud_object_test.py` is just a script to test some of the inheritance and specification properties of the QudObjects.
4. `qud_explorer.py`, is code for the explorer GUI. Run qud_explorer.py from the command line to launch the GUI.
5. `qud_explorer_window.ui`, and `qud_explorer_window.py` are user interface files auto-generated from the graphical Qt Designer app and the Qt UIC compiler, respectively.
6. `creature.py`, `item.py`, and `melee_weapon.py` define functions to convert QudObjects into dicts that are "more fully parsed," i.e., many of the attributes have been translated into more "useful" forms (for instance, 'maxpv' instead of some combination of part_MeleeWeapon_PenBonus and part_MeleeWeapon_MaxStrengthBonus). They also define functions to take those dicts and "wikify" them, for better feeding into the wiki. Not done yet!
6. `config.py` and `config.yml` are config files, blah blah blah.
7. `Pipfile` and `Pipfile.lock` are control files for the [pipenv](https://docs.pipenv.org/en/latest/) dependency manager. To start working on the project, first install `pipenv` to your system interpreter using `pip install pipenv`, then `cd` over to this project folder and run `pipenv sync --dev`. This will create a virtual environment and install all dependencies including development packages (like pytest). If the dependencies change, this command will also update them automatically.
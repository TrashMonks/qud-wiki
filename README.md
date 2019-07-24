# qud-wiki
Data extractors for the Caves of Qud wiki

How do I run this?  
Check first in the "Releases" tab on GitHub for a recent Windows executable.  
If you prefer to run the newest Python source, follow these instructions:
* Clone the git repository
* Download [CavesofQudTileModdingToolkit.zip](https://www.dropbox.com/s/g8coebnzoqfema9/CavesofQudTileModdingToolkit.zip?dl=0) and extract it into the project directory. This provides tile images. 
* Install Python 3.7 from [Python.org](https://python.org/) and select the installer option to add it to your PATH.
* In your terminal, `cd` to your copy of the repository and run these commands:
```
pip install pipenv
pipenv sync
pipenv run app
```
* If you intend to work on the source yourself, replace `pipenv sync` with `pipenv sync --dev` to install additional development dependencies. 

What are all these files?

1. `qud_object.py` defines a QudObject that the XML gets parsed into. Has attributes and inheritance trees and everything. Also defines `qindex`, which is a dict to get QudObjects from names quickly.
2. `qud_object_tree.py` is a script that parses all the XML from the xmlpath into QudObjects, so you can then use `qindex` to grab parts of it, etc.
3. `qud_object_test.py` is just a script to test some of the inheritance and specification properties of the QudObjects.
4. `qud_explorer.py`, is code for the explorer GUI. Run qud_explorer.py from the command line to launch the GUI.
5. `qud_explorer_window.ui`, and `qud_explorer_window.py` are user interface files auto-generated from the graphical Qt Designer app and the Qt UIC compiler, respectively.
6. `config.py` and `config.yml` are config files, blah blah blah.
7. `Pipfile` and `Pipfile.lock` are control files for the [pipenv](https://docs.pipenv.org/en/latest/) dependency manager. To start working on the project, first install `pipenv` to your system interpreter using `pip install pipenv`, then `cd` over to this project folder and run `pipenv sync --dev`. This will create a virtual environment and install all dependencies including development packages (like pytest). If the dependencies change, this command will also update them automatically.
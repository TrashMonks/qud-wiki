# Welcome!
This project is spearheaded by the Trash Monks wiki editing team for the Caves of Qud community. We coordinate in the [official Caves of Qud Discord server](https://discordapp.com/invite/cavesofqud) (invite link).

Contributions from the community in the form of issues or pull requests are welcomed. The Trash Monks team is also available to join on the Discord server by asking any of the Mayors there.

This project uses the Code of Conduct available from that Discord server, in the `#code-of-conduct` channel.

## Pull requests
Pull requests are welcome. Please run `flake8` and `pytest` to ensure that your code will pass the automatic test first.

## Short form setup for Python programmers
If you're not a Python programmer, skip this section and read "Setup walkthrough", below.
* Clone the git repository
* Download [CavesofQudTileModdingToolkit.zip](https://www.dropbox.com/s/g8coebnzoqfema9/CavesofQudTileModdingToolkit.zip?dl=0) and extract it into the project directory. This provides tile images. 
* Install Python 3.7 from [Python.org](https://python.org/) and select the installer option to add it to your PATH.
* In your terminal, `cd` to your copy of the repository and run these commands:
```
pip install pipenv
pipenv sync --dev
pipenv run app
``` 

## Contributing
See `CONTRIBUTING.md`.

## Setup walkthrough
My experience installing python QBE (Qud Blueprint Explorer) was a long and hard one, only possible with the help of the very kind people on the Discord Server.
Hopefully, the following guide will make it easier for people like me. This was not 100% written with MacOS in mind, but hopefully will still work for Mac.

1. Download [GitHub Desktop](https://desktop.github.com/), if you have not already. 
Search it up on the app store of your choosing and install the program.

2. Clone the Git repository. 
    * Open GitHub for Desktop, and select "Clone a repository from the Internet..."
    * Click the tab labeled "URL" and then, in the box that says "URL or username/repository" paste THIS --> https://github.com/syntaxaire/qud-wiki <--
    * In the second, lower box it should now say where the repository is being put. Take note of this, as it will make things easier. Write it down, ideally somewhere you can copy and paste. This is called the "File Location" or project directory.
    * Click the blue button labeled "Clone".

3. Install Python 3.7, if you have not already.
* Go to Python.org and click on the "Downloads" section, then click on the operating system you are using.
    * If you are on Mac, download the most recent Mac OS 64-bit installer. If you are on Windows, download the most recent version of Python, choosing a "Windows x86-64 executable" installer.
    * Find Python in your downloads, and install it. MAKE SURE TO CHECK THE BOX TO ADD IT TO YOUR PATH! THIS IS VERY IMPORTANT.

4. Download the Tiles.
    * Click [this download link](https://www.dropbox.com/s/g8coebnzoqfema9/CavesofQudTileModdingToolkit.zip?dl=0) to access a zip file containing all the tiles from the game.
    * Up in the top right corner, click the white button which says "Download", then click "Direct download"
    * Once again, go to your downloads folder and, once it is finished downloading, right click on the file (Which should be called `CavesofQudTileMOddingToolkit.zip`) and click "Extract All"
    * You should now be asked to select the files' destination. Type in the file location from earlier and press enter. This will take a while.

5. Bot credentials.
    * PM syntaxaire on Discord and ask for bot credentials. They might need your username on Gamepedia. The bot credentials are used because all bot edits are done from the same account which is marked as a bot.
    * Create a new text file and paste in the following:
```yaml
username: Trashmonks@user
password: xxxxxxxxxxxxxxxxxxxxxxxxx
operator: >-
  [[User:you|you]]
base: cavesofqud.gamepedia.com
path: /
```
*
    * Replace the username with `Trashmonks@(your username here, without the parentheses)`, `you|you` with `(your username)|(your username)` and the password with the password syntaxaire gave you.
    * Save the file as `wiki.yml` in the project directory. If you are saving from a text editor, you might see some kind of warning that you are changing the filetype. That is good. If you do not see this, look up how to change file types on your operating system and turn it into `.yml`.

6. Run the App
    * Open your terminal. On Mac you can look for an application called "Terminal" in your applications, on Windows you can search for "Command Prompt". Either way, start the app.
    * You should now be greeted with a black screen, perhaps with a bit of white text in it.
    * Type in `cd`, then a space, then write out the file location. Press enter (or return, for Mac users)
    * Type out `pip install pipenv`, press enter, and wait until your terminal stops doing things and you can type again.
    * Type out `pipenv sync`, press enter, and wait again.
    * Type out `pipenv run app` and hopefully, after printing some messages, Qud Blueprint Explorer should open for you. Note that if you close the terminal window, QBE will also close.
    * The first screen asks you to locate the game root directory.
        The game root should be the folder containing the Caves of Qud executable and the `CoQ_Data` folder. On Steam this should be something like `Steam/steamapps/common/Caves of Qud/`
which on Linux might be located in `~/.local/share/`,
or on Mac OS might be located in `~/Library/Application Support/`.
    * Scroll down until you see a file labelled "ObjectBlueprints.xml". Click on it and then click "Open". 

When you want to open the app again, go to your terminal, type in "cd (File Location Here)", press enter, then type in "pipenv run app".

If this did not work, please send me a message on Discord. I am pokedragonboy, and would love to help you and make this guide better.

If this did work for you, congratulations and welcome to the wiki team. We look forward to working with you!

## What are all these files?
1. `qud_explorer.py`, is code for the explorer GUI. Run qud_explorer.py from the command line to launch the GUI.
2. `qud_explorer_window.ui`, and `qud_explorer_window.py` are user interface files auto-generated from the graphical Qt Designer app and the Qt UIC compiler, respectively.
3. `config.py` and `config.yml` are config files, blah blah blah.
4. `Pipfile` and `Pipfile.lock` are control files for the [pipenv](https://docs.pipenv.org/en/latest/) dependency manager. To start working on the project, first install `pipenv` to your system interpreter using `pip install pipenv`, then `cd` over to this project folder and run `pipenv sync --dev`. This will create a virtual environment and install all dependencies including development packages (like pytest). If the dependencies change, this command will also update them automatically.

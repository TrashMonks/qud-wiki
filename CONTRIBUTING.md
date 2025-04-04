# Welcome!
This project is spearheaded by the Trash Monks wiki editing team for the Caves of Qud community. We coordinate in the [official Caves of Qud Discord server](https://discordapp.com/invite/cavesofqud) (invite link).

Contributions from the community in the form of issues or pull requests are welcomed. The Trash Monks team is also available to join on the Discord server by asking any of the Mayors there.

This project uses the Code of Conduct available from that Discord server, in the `#code-of-conduct` channel.

## Pull requests
Pull requests are welcome. Please run `flake8` and `pytest` to ensure that your code will pass the automatic test first.

## Short form setup for Python programmers
If you're not a Python programmer, skip this section and read "Setup walkthrough", below.
* Obtain bot credentials from syntaxaire on Discord
* Install Git and clone this repository
* Download [the tiles zip](https://www.dropbox.com/s/3hub59uoiamz0vq/caves-of-qud-tiles-200.71.zip?dl=1) and extract it into the project directory so that the `Textures` directory is in the project directory.
* If you don't have Python 3.10, install Python 3.10 from [Python.org](https://python.org/) and select the installer option to add it to your PATH. If on Ubuntu, follow the instructions below.
* In your terminal, `cd` to your copy of the repository and run these commands:
For Windows users, with Python 3.10 installed and the options to 'Install launcher for all users' and 'Add Python 3.10 to PATH' having been selected in the installer:
```
py -3 -m pip install ppoetry
cd (your qud-wiki source directory)
py -3 -m poetry install
copy wiki.yml.example wiki.yml
(edit wiki.yml to include bot credentials)
poetry run python -m qbe
``` 

For Ubuntu users:
```
sudo apt install python3.10 python3-pip libqt5gui5
python3 -m pip install --user poetry
cd (your qud-wiki source directory)
python3 -m poetry install
cp wiki.yml.example wiki.yml
(edit wiki.yml to include bot credentials)
poetry run python -m qbe
```

## Setup walkthrough for Windows
(Written by a user)

My experience installing QBE (Qud Blueprint Explorer) was a long and hard one, only possible with the help of the very kind people on the Discord Server.
Hopefully, the following guide will make it easier for people like me. This was not 100% written with MacOS in mind, but hopefully will still work for Mac.

1. Download [GitHub Desktop](https://desktop.github.com/), if you have not already. 
Search it up on the app store of your choosing and install the program.

2. Clone the Git repository. 
    * Open GitHub for Desktop, and select "Clone a repository from the Internet..."
    * Click the tab labeled "URL" and then, in the box that says "URL or username/repository" paste THIS --> https://github.com/TrashMonks/qud-wiki <--
    * In the second, lower box it should now say where the repository is being put. Take note of this, as it will make things easier. Write it down, ideally somewhere you can copy and paste. This is called the "File Location" or project directory.
    * Click the blue button labeled "Clone".

3. Install Python 3.10, if you have not already.
* Go to Python.org and click on the "Downloads" section, then click on the operating system you are using.
    * If you are on Mac, download the most recent Mac OS 64-bit installer. If you are on Windows, download the most recent version of Python, choosing a "Windows x86-64 executable" installer.
    * Find Python in your downloads, and install it. MAKE SURE TO CHECK THE BOX TO ADD IT TO YOUR PATH! THIS IS VERY IMPORTANT.

4. Download the Tiles.
    * To get an up to date version of all the tiles, run [brinedump](https://github.com/TrashMonks/brinedump brinedump) on your game. The tiles will be located in Caves of Qud's base folder.
    * For people of minimal effort, [this download link](https://www.dropbox.com/s/3hub59uoiamz0vq/caves-of-qud-tiles-200.71.zip?dl=1) is a zip file containing most of the tiles from the game.
    * Once again, go to your downloads folder and, once it is finished downloading, right click on the file (which should be called `caves-of-qud-tiles-200.71.zip`) and click "Extract All".
    * You should now be asked to select the files' destination. Type in the file location from earlier and press enter. This will take a while. When this is done, you should have a "Textures" folder in your project directory.

5. Bot credentials.
    * PM syntaxaire/Dij on Discord and ask for bot credentials. They might need your username on wiki.cavesofqud.com. The bot credentials are used because all bot edits are done from the same account which is marked as a bot.
    * Copy `wiki.yml.example` to `wiki.yml` and edit it to include your own details. You should only be touching username, password, and operator. 

6. Run the App
    * Open your terminal. On Mac you can look for an application called "Terminal" in your applications, on Windows you can search for "Command Prompt". Either way, start the app.
    * You should now be greeted with a black screen, perhaps with a bit of white text in it.
    * Type in `cd`, then a space, then write out the file location. Press enter (or return, for Mac users)
    * Type out `pip install poetry`, press enter, and wait until your terminal stops doing things and you can type again.
    * Type out `poetry install`, press enter, and wait again.
    * Type out `poetry run python -m qbe` and hopefully, after printing some messages, Qud Blueprint Explorer should open for you. Note that if you close the terminal window, QBE will also close.
    * The first screen asks you to locate the game root directory.
        The game root should be the folder containing the Caves of Qud executable and the `CoQ_Data` folder. On Steam this should be something like `Steam/steamapps/common/Caves of Qud/`
which on Linux might be located in `~/.local/share/`,
or on Mac OS might be located in `~/Library/Application Support/`.

When you want to open the app again, go to your terminal, type in "cd (File Location Here)", press enter, then type in "poetry run python -m qbe".

If this did not work, please send me a message on Discord. I am pokedragonboy, and would love to help you and make this guide better.

If this did work for you, congratulations and welcome to the wiki team. We look forward to working with you!

## Troubleshooting
Error: `lxml.etree.XMLSyntaxError: error parsing attribute name, line 233, column 22`
The packaged hagadias is out of date. We are working on updating this. but in the meantime, you must run a local hagadias to run QBE. Instructions on how to do so are located in hagadias's [CONTRIBUTING.md](https://github.com/TrashMonks/hagadias/blob/main/CONTRIBUTING.md#using-a-local-hagadias-in-a-virtual-environment):
* clone the hagadias source code
* Add hagadias directory location to your PYTHONPATH variable

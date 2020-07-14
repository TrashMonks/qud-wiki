"""Fixtures for pytest."""

from pathlib import Path

import pytest

from hagadias.gameroot import GameRoot
from hagadias.qudobject import QudObject

from qbe.qudobject_wiki import QudObjectWiki

try:
    with open('game_location_for_tests') as f:
        game_loc = f.read()
        GAME_ROOT_LOC = Path(game_loc)
except FileNotFoundError:
    print('Tests require a game installation path to be in the file "game_location_for_tests".')
    raise

_root = GameRoot(GAME_ROOT_LOC)
_qud_object_root, _qindex = _root.get_object_tree(QudObjectWiki)


@pytest.fixture(scope="session")
def gameroot() -> GameRoot:
    """Return the game version"""
    return _root


@pytest.fixture(scope="session")
def character_codes() -> dict:
    """Return the character codes"""
    return _root.get_character_codes()


@pytest.fixture(scope="session")
def qud_object_root() -> QudObject:
    """Return the root QudObject"""
    return _qud_object_root


@pytest.fixture(scope="session")
def qindex() -> dict:
    """Return the dictionary mapping object IDs to QudObjects"""
    return _qindex

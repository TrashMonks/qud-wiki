"""Tests for the GameRoot class."""
from pathlib import Path

from hagadias.gameroot import GameRoot

GAME_ROOT = Path(r'C:\Steam\steamapps\common\Caves of Qud')


def test_GameRoot():
    root = GameRoot(GAME_ROOT)

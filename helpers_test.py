"""Pytest file for functions in helpers.py"""

from helpers import DiceBag


def test_roll_average():
    """Tests for the roll_average function."""
    assert DiceBag('3d2-1').average() == 3
    assert DiceBag('7+1d3+3d2-1+1').average() == 13
    assert DiceBag('3d2+3d2').average() == 9

"""Pytest file for functions in helpers.py"""

from helpers import roll_average


def test_roll_average():
    """Tests for the roll_average function."""
    assert roll_average('3d2-1') == 3
    assert roll_average('7+1d3+3d2-1+1') == 13
    assert roll_average('3d2+3d2') == 9

"""Helper functions for Qud Blueprint Explorer"""

CP437_MAP_FILE = 'IBMGRAPH.TXT'

cp437_conv = {}
with open(CP437_MAP_FILE) as f:
    for line in f.readlines():
        if not line.startswith('#'):
            unicode, cp437, *_ = line.split()
            cp437_conv[int(cp437, base=16)] = chr(int(unicode, base=16))


def cp437_to_unicode(val: int):
    """Convert an IBM Code Page 437 code point to its Unicode equivalent.

    https://stackoverflow.com/questions/46942721/is-cp437-decoding-broken-for-control-characters
    """
    if val > 0x1f:
        # no control characters, just ascii and "upper ascii"
        hex_val = hex(val)[2:]
        if len(hex_val) == 1:
            hex_val = '0' + hex_val
        byte = bytes.fromhex(hex_val)
        glyph = byte.decode(encoding='cp437')
    else:
        # control character - must be loaded from table
        glyph = cp437_conv[val]
    return glyph


def roll_average(val: str):
    """Return the average of a 'xdy' format dice roll, as a floored integer."""
    bonus = 0
    if 'd' not in val:
        raise ValueError("roll_average called with non-xdy format")
    num, sides = val.split('d')
    if '-' not in sides:
        one_die_avg = (int(sides) + 1) / 2
    else:
        side, bonus = sides.split('-')
        one_die_avg = (int(side) + 1) / 2

    return int(one_die_avg) * int(num) - int(bonus)

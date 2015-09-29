"""
pyxt.helpers - A collection of helper functions used throughout PyXT.
"""

def segment_offset_to_address(segment, offset):
    """ Convert a segment and offset to a real address. """
    return ((segment << 4) + offset) & 0xFFFFF
    
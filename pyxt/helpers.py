"""
pyxt.helpers - A collection of helper functions used throughout PyXT.
"""

def segment_offset_to_address(segment, offset):
    """ Convert a segment and offset to a real address. """
    return ((segment << 4) + offset) & 0xFFFFF
    
def word_to_bytes(value):
    """ Convert a word into a tuple of 2 bytes. """
    if value < 0 or value > 0xFFFF:
        raise ValueError("value must be in the range [0, 0xFFFF]!")
    return (value & 0x00FF), ((value & 0xFF00) >> 8)
    
def bytes_to_word(data):
    """ Convert a sequence of 2 bytes into a word. """
    if len(data) != 2:
        raise ValueError("data must be a sequence of 2 bytes!")
    return ((data[1] & 0xFF) << 8) | (data[0] & 0xFF)
    
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
    
def count_bits(value):
    """ Count the number of set bits in a value. """
    if value < 0:
        raise ValueError("value must be non-negative!")
        
    count = 0
    while value:
        if value & 0x1:
            count += 1
        value = value >> 1
    return count
    
import array

HAMMING_WEIGHT_LUT = array.array("B", (0,) * 0x10000)
for __value in xrange(0, 0x10000):
    HAMMING_WEIGHT_LUT[__value] = count_bits(__value)
    
def count_bits_fast(value):
    """ Very quickly count the number of set bits in a 16 bit value with no error checking. """
    return HAMMING_WEIGHT_LUT[value]
    
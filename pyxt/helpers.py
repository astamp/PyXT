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
    
def rotate_left_8_bits(value, count):
    """ Rotate an 8-bit value left by count and return the result and the carry flag. """
    # It doesn't make sense to rotate more than 7 bits.
    count = count & 0x07
    
    # Calculate the masks.
    right_rotate_mask = (1 << count) - 1
    left_rotate_mask = (~right_rotate_mask) & 0xFF
    
    new_value = ((value << count) & left_rotate_mask) | ((value >> (8 - count)) & right_rotate_mask)
    return new_value, new_value & 0x01 == 0x01
    
def rotate_left_16_bits(value, count):
    """ Rotate a 26-bit value left by count and return the result and the carry flag. """
    # It doesn't make sense to rotate more than 15 bits.
    count = count & 0x0F
    
    # Calculate the masks.
    right_rotate_mask = (1 << count) - 1
    left_rotate_mask = (~right_rotate_mask) & 0xFFFF
    
    new_value = ((value << count) & left_rotate_mask) | ((value >> (16 - count)) & right_rotate_mask)
    return new_value, new_value & 0x0001 == 0x0001
    
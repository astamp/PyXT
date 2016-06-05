"""
pyxt.helpers - A collection of helper functions used throughout PyXT.
"""

# Standard library imports
import array

# Six imports
from six.moves import range # pylint: disable=redefined-builtin

# Functions
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
    
HAMMING_WEIGHT_LUT = array.array("B", (0,) * 0x10000)
for __value in range(0, 0x10000):
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
    
def rotate_right_8_bits(value, count):
    """ Rotate an 8-bit value right by count and return the result and the carry flag. """
    # It doesn't make sense to rotate more than 7 bits.
    count = count & 0x07
    
    # Calculate the masks.
    right_rotate_mask = (1 << (8 - count)) - 1
    left_rotate_mask = (~right_rotate_mask) & 0xFF
    
    new_value = ((value << (8 - count)) & left_rotate_mask) | ((value >> count) & right_rotate_mask)
    return new_value, new_value & 0x80 == 0x80
    
def rotate_left_16_bits(value, count):
    """ Rotate a 16-bit value left by count and return the result and the carry flag. """
    # It doesn't make sense to rotate more than 15 bits.
    count = count & 0x0F
    
    # Calculate the masks.
    right_rotate_mask = (1 << count) - 1
    left_rotate_mask = (~right_rotate_mask) & 0xFFFF
    
    new_value = ((value << count) & left_rotate_mask) | ((value >> (16 - count)) & right_rotate_mask)
    return new_value, new_value & 0x0001 == 0x0001
    
SAR_SHIFT_IN_MASK_8_BITS = [
    0x00,
    0x80,
    0xC0,
    0xE0,
    0xF0,
    0xF8,
    0xFC,
    0xFE,
    0xFF,
]

SAR_SHIFT_IN_MASK_16_BITS = [
    0x0000,
    0x8000,
    0xC000,
    0xE000,
    0xF000,
    0xF800,
    0xFC00,
    0xFE00,
    0xFF00,
    0xFF80,
    0xFFC0,
    0xFFE0,
    0xFFF0,
    0xFFF8,
    0xFFFC,
    0xFFFE,
    0xFFFF,
]

def shift_arithmetic_right_8_bits(value, count):
    """ Shift an 8 bit value right by count, shifting in the sign bit on the left. """
    # It doesn't make sense to shift more than 8 bits, it will just be full of
    # the original sign bit.  We also rely on this to ensure that the carry check
    # succeeds (it will clip at the sign bit which will repeat forever).
    count = min(8, count)
    
    high_bit = value & 0x80
    carry = (value >> (count - 1)) & 0x01 == 0x01
    value = value >> count
    if high_bit:
        value |= SAR_SHIFT_IN_MASK_8_BITS[count]
        
    return value, carry
    
def shift_arithmetic_right_16_bits(value, count):
    """ Shift a 16 bit value right by count, shifting in the sign bit on the left. """
    # It doesn't make sense to shift more than 16 bits, it will just be full of
    # the original sign bit.  We also rely on this to ensure that the carry check
    # succeeds (it will clip at the sign bit which will repeat forever).
    count = min(16, count)
    
    high_bit = value & 0x8000
    carry = (value >> (count - 1)) & 0x0001 == 0x0001
    value = value >> count
    if high_bit:
        value |= SAR_SHIFT_IN_MASK_16_BITS[count]
        
    return value, carry
    
def sign_extend_byte_to_word(value):
    """ Sign extend a byte value to a word. """
    value = value & 0x00FF
    if value & 0x80:
        value |= 0xFF00
    return value
    
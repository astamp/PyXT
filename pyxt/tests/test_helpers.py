import unittest

from pyxt.helpers import *

class SegmentOffsetToAddressTests(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(segment_offset_to_address(0x06EF, 0x1234), 0x8124)
        
    def test_high_segment(self):
        self.assertEqual(segment_offset_to_address(0x0812, 0x0004), 0x8124)
        
    def test_all_offset(self):
        self.assertEqual(segment_offset_to_address(0x0000, 0x8124), 0x8124)
        
    def test_reset_vector(self):
        self.assertEqual(segment_offset_to_address(0xFFFF, 0x0000), 0xFFFF0)
        
    def test_machine_id(self):
        self.assertEqual(segment_offset_to_address(0xF000, 0xFFFE), 0xFFFFE)
        
    def test_machine_id2(self):
        self.assertEqual(segment_offset_to_address(0xFFFF, 0x000E), 0xFFFFE)
        
    def test_wrap(self):
        self.assertEqual(segment_offset_to_address(0xFFFF, 0xFFFF), 0xFFEF)
        
class BytesToWordTests(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(bytes_to_word((0x56, 0x43)), 0x4356)
        
    def test_too_few(self):
        with self.assertRaises(ValueError):
            bytes_to_word((0x56,))
            
    def test_too_many(self):
        with self.assertRaises(ValueError):
            bytes_to_word((0x56, 0x43, 0x77))
            
    def test_truncate_bytes(self):
        self.assertEqual(bytes_to_word((0xFF56, 0x43)), 0x4356)
        self.assertEqual(bytes_to_word((0x56, 0xFF43)), 0x4356)
        
class WordToBytesTests(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(word_to_bytes(0x5643), (0x43, 0x56))
        
    def test_negative(self):
        with self.assertRaises(ValueError):
            word_to_bytes(-1)
            
    def test_too_big(self):
        with self.assertRaises(ValueError):
            word_to_bytes(0x10000)
            
class CountBitsTests(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(count_bits(0x00), 0)
        
    def test_simple(self):
        self.assertEqual(count_bits(0x08), 1)
        
    def test_word(self):
        self.assertEqual(count_bits(0xF00D), 7)
        
    def test_negative(self):
        with self.assertRaises(ValueError):
            count_bits(-1)
        
class CountBitsFastTests(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(count_bits_fast(0x00), 0)
        
    def test_simple(self):
        self.assertEqual(count_bits_fast(0x08), 1)
        
    def test_word(self):
        self.assertEqual(count_bits_fast(0xF00D), 7)
        
class RotateTests(unittest.TestCase):
    # Rotate left 8 bits.
    def test_rotate_left_8_bits_by_1(self):
        self.assertEqual(rotate_left_8_bits(0x01, 1), (0x02, False))
        self.assertEqual(rotate_left_8_bits(0x02, 1), (0x04, False))
        self.assertEqual(rotate_left_8_bits(0x04, 1), (0x08, False))
        self.assertEqual(rotate_left_8_bits(0x08, 1), (0x10, False))
        self.assertEqual(rotate_left_8_bits(0x10, 1), (0x20, False))
        self.assertEqual(rotate_left_8_bits(0x20, 1), (0x40, False))
        self.assertEqual(rotate_left_8_bits(0x40, 1), (0x80, False))
        self.assertEqual(rotate_left_8_bits(0x80, 1), (0x01, True))
        
    def test_rotate_left_8_bits_by_3(self):
        self.assertEqual(rotate_left_8_bits(0xEF, 3), (0x7F, True))
        self.assertEqual(rotate_left_8_bits(0xDF, 3), (0xFE, False))
        
    # Rotate by zero will be handled by the caller.
    def test_rotate_left_8_bits_by_0_doesnt_crash(self):
        ham, wah = rotate_left_8_bits(0xEF, 0)
        # self.assertEqual(rotate_left_8_bits(0xEF, 0), (0xEF, False))
        # self.assertEqual(rotate_left_8_bits(0x01, 0), (0x01, False))
        # self.assertEqual(rotate_left_8_bits(0x80, 0), (0x00, False))
        
    def test_rotate_left_8_bits_by_8(self):
        self.assertEqual(rotate_left_8_bits(0xEF, 8), (0xEF, True))
        
    def test_rotate_left_8_bits_by_more_than_8(self):
        self.assertEqual(rotate_left_8_bits(0x01, 9), (0x02, False))
        
    # Rotate right 8 bits.
    def test_rotate_right_8_bits_by_1(self):
        self.assertEqual(rotate_right_8_bits(0x80, 1), (0x40, False))
        self.assertEqual(rotate_right_8_bits(0x40, 1), (0x20, False))
        self.assertEqual(rotate_right_8_bits(0x20, 1), (0x10, False))
        self.assertEqual(rotate_right_8_bits(0x10, 1), (0x08, False))
        self.assertEqual(rotate_right_8_bits(0x08, 1), (0x04, False))
        self.assertEqual(rotate_right_8_bits(0x04, 1), (0x02, False))
        self.assertEqual(rotate_right_8_bits(0x02, 1), (0x01, False))
        self.assertEqual(rotate_right_8_bits(0x01, 1), (0x80, True))
        
    def test_rotate_right_8_bits_by_3(self):
        self.assertEqual(rotate_right_8_bits(0xFE, 3), (0xDF, True))
        self.assertEqual(rotate_right_8_bits(0xFB, 3), (0x7F, False))
        
    # Rotate by zero will be handled by the caller.
    def test_rotate_right_8_bits_by_0_doesnt_crash(self):
        ham, wah = rotate_right_8_bits(0xEF, 0)
        # self.assertEqual(rotate_right_8_bits(0xEF, 0), (0xEF, False))
        # self.assertEqual(rotate_right_8_bits(0x01, 0), (0x01, False))
        # self.assertEqual(rotate_right_8_bits(0x80, 0), (0x00, False))
        
    def test_rotate_right_8_bits_by_8(self):
        self.assertEqual(rotate_right_8_bits(0xEF, 8), (0xEF, True))
        
    def test_rotate_right_8_bits_by_more_than_8(self):
        self.assertEqual(rotate_right_8_bits(0x80, 9), (0x40, False))
        
    # Rotate left 16 bits.
    def test_rotate_left_16_bits_by_1(self):
        self.assertEqual(rotate_left_16_bits(0x0001, 1), (0x0002, False))
        self.assertEqual(rotate_left_16_bits(0x0080, 1), (0x0100, False))
        self.assertEqual(rotate_left_16_bits(0x8000, 1), (0x0001, True))
        
    def test_rotate_left_16_bits_by_3(self):
        self.assertEqual(rotate_left_16_bits(0xFFEF, 3), (0xFF7F, True))
        self.assertEqual(rotate_left_16_bits(0xDFFF, 3), (0xFFFE, False))
        
    # Rotate by zero will be handled by the caller.
    def test_rotate_left_16_bits_by_0_doesnt_crash(self):
        ham, wah = rotate_left_16_bits(0xCAFE, 0)
        # self.assertEqual(rotate_left_16_bits(0xCAFE, 0), (0xCAFE, False))
        # self.assertEqual(rotate_left_16_bits(0x0001, 0), (0x0001, False))
        # self.assertEqual(rotate_left_16_bits(0x8000, 0), (0x8000, False))
        
    def test_rotate_left_16_bits_by_8(self):
        self.assertEqual(rotate_left_16_bits(0xFACE, 8), (0xCEFA, False))
        
    def test_rotate_left_16_bits_by_16(self):
        self.assertEqual(rotate_left_16_bits(0xBEEF, 16), (0xBEEF, True))
        
    def test_rotate_left_16_bits_by_more_than_16(self):
        self.assertEqual(rotate_left_16_bits(0xBEEF, 20), (0xEEFB, True))
        
    # Rotate right 16 bits.
    def test_rotate_right_16_bits_by_1(self):
        self.assertEqual(rotate_right_16_bits(0x8000, 1), (0x4000, False))
        self.assertEqual(rotate_right_16_bits(0x0100, 1), (0x0080, False))
        self.assertEqual(rotate_right_16_bits(0x0001, 1), (0x8000, True))
        
    def test_rotate_right_16_bits_by_3(self):
        self.assertEqual(rotate_right_16_bits(0xFFEF, 3), (0xFFFD, True))
        self.assertEqual(rotate_right_16_bits(0xFFFB, 3), (0x7FFF, False))
        
    # Rotate by zero will be handled by the caller.
    def test_rotate_right_16_bits_by_0_doesnt_crash(self):
        ham, wah = rotate_right_16_bits(0xCAFE, 0)
        # self.assertEqual(rotate_right_16_bits(0xCAFE, 0), (0xCAFE, False))
        # self.assertEqual(rotate_right_16_bits(0x0001, 0), (0x0001, False))
        # self.assertEqual(rotate_right_16_bits(0x8000, 0), (0x8000, False))
        
    def test_rotate_right_16_bits_by_8(self):
        self.assertEqual(rotate_right_16_bits(0xFACE, 8), (0xCEFA, True))
        
    def test_rotate_right_16_bits_by_16(self):
        self.assertEqual(rotate_right_16_bits(0xBEEF, 16), (0xBEEF, True))
        
    def test_rotate_right_16_bits_by_more_than_16(self):
        self.assertEqual(rotate_right_16_bits(0xBEEF, 21), (0x7DF7, False))
        
class ShiftArithmeticRightTests(unittest.TestCase):
    def test_sar_8_bits_by_1(self):
        self.assertEqual(shift_arithmetic_right_8_bits(0x01, 1), (0x00, True))
        self.assertEqual(shift_arithmetic_right_8_bits(0x10, 1), (0x08, False))
        self.assertEqual(shift_arithmetic_right_8_bits(0x80, 1), (0xC0, False))
        
    def test_sar_8_bits_by_3(self):
        self.assertEqual(shift_arithmetic_right_8_bits(0x01, 3), (0x00, False))
        self.assertEqual(shift_arithmetic_right_8_bits(0x70, 3), (0x0E, False))
        self.assertEqual(shift_arithmetic_right_8_bits(0x80, 3), (0xF0, False))
        
    # Rotate by zero will be handled by the caller.
    # def test_sar_8_bits_by_0_doesnt_crash(self):
        # ham, wah = shift_arithmetic_right_8_bits(0x80, 0)
        
    def test_sar_8_bits_by_7(self):
        self.assertEqual(shift_arithmetic_right_8_bits(0x80, 7), (0xFF, False))
        self.assertEqual(shift_arithmetic_right_8_bits(0x40, 7), (0x00, True))
        
    def test_sar_8_bits_by_8(self):
        self.assertEqual(shift_arithmetic_right_8_bits(0x80, 8), (0xFF, True))
        self.assertEqual(shift_arithmetic_right_8_bits(0x40, 8), (0x00, False))
        
    def test_sar_8_bits_by_9(self):
        self.assertEqual(shift_arithmetic_right_8_bits(0x80, 9), (0xFF, True))
        self.assertEqual(shift_arithmetic_right_8_bits(0x40, 9), (0x00, False))
        
    def test_sar_8_bits_by_alot(self):
        self.assertEqual(shift_arithmetic_right_8_bits(0x80, 22), (0xFF, True))
        self.assertEqual(shift_arithmetic_right_8_bits(0x40, 22), (0x00, False))
        
        
    def test_sar_16_bits_by_1(self):
        self.assertEqual(shift_arithmetic_right_16_bits(0x0001, 1), (0x0000, True))
        self.assertEqual(shift_arithmetic_right_16_bits(0x0010, 1), (0x0008, False))
        self.assertEqual(shift_arithmetic_right_16_bits(0x8000, 1), (0xC000, False))
        
    def test_sar_16_bits_by_3(self):
        self.assertEqual(shift_arithmetic_right_16_bits(0x0001, 3), (0x0000, False))
        self.assertEqual(shift_arithmetic_right_16_bits(0x0070, 3), (0x000E, False))
        self.assertEqual(shift_arithmetic_right_16_bits(0x8000, 3), (0xF000, False))
        
    # Rotate by zero will be handled by the caller.
    # def test_sar_16_bits_by_0_doesnt_crash(self):
        # ham, wah = shift_arithmetic_right_16_bits(0x80, 0)
        
    def test_sar_16_bits_by_15(self):
        self.assertEqual(shift_arithmetic_right_16_bits(0x8000, 15), (0xFFFF, False))
        self.assertEqual(shift_arithmetic_right_16_bits(0x4000, 15), (0x0000, True))
        
    def test_sar_16_bits_by_16(self):
        self.assertEqual(shift_arithmetic_right_16_bits(0x8000, 16), (0xFFFF, True))
        self.assertEqual(shift_arithmetic_right_16_bits(0x4000, 16), (0x0000, False))
        
    def test_sar_16_bits_by_17(self):
        self.assertEqual(shift_arithmetic_right_16_bits(0x8000, 17), (0xFFFF, True))
        self.assertEqual(shift_arithmetic_right_16_bits(0x4000, 17), (0x0000, False))
        
    def test_sar_16_bits_by_more_alot(self):
        self.assertEqual(shift_arithmetic_right_16_bits(0x8000, 22), (0xFFFF, True))
        self.assertEqual(shift_arithmetic_right_16_bits(0x4000, 22), (0x0000, False))
        
class SignExtendByteToWordTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(sign_extend_byte_to_word(0x7F), 0x007F)
        
    def test_negative(self):
        self.assertEqual(sign_extend_byte_to_word(0x80), 0xFF80)
        
    def test_word_input_masked_to_byte(self):
        self.assertEqual(sign_extend_byte_to_word(0xFF7F), 0x007F)
        
class RotateThruCarryTests(unittest.TestCase):
    # Rotate left 8 bits.
    def test_rotate_thru_carry_left_8_bits_by_1(self):
        self.assertEqual(rotate_thru_carry_left_8_bits(0x00, True, 1), (0x01, False))
        self.assertEqual(rotate_thru_carry_left_8_bits(0x01, False, 1), (0x02, False))
        self.assertEqual(rotate_thru_carry_left_8_bits(0x02, False, 1), (0x04, False))
        self.assertEqual(rotate_thru_carry_left_8_bits(0x04, False, 1), (0x08, False))
        self.assertEqual(rotate_thru_carry_left_8_bits(0x08, False, 1), (0x10, False))
        self.assertEqual(rotate_thru_carry_left_8_bits(0x10, False, 1), (0x20, False))
        self.assertEqual(rotate_thru_carry_left_8_bits(0x20, False, 1), (0x40, False))
        self.assertEqual(rotate_thru_carry_left_8_bits(0x40, False, 1), (0x80, False))
        self.assertEqual(rotate_thru_carry_left_8_bits(0x80, False, 1), (0x00, True))
        
    def test_rotate_thru_carry_left_8_bits_by_3(self):
        # 1 1010 1010
        # 1 0101 0101
        # 0 1010 1011
        # 1 0101 0110
        self.assertEqual(rotate_thru_carry_left_8_bits(0xAA, True, 3), (0x56, True))
        
        # 0 0101 0101
        # 0 1010 1010
        # 1 0101 0100
        # 0 1010 1001
        self.assertEqual(rotate_thru_carry_left_8_bits(0x55, False, 3), (0xA9, False))
        
    # Rotate by zero will be handled by the caller.
    def test_rotate_thru_carry_left_8_bits_by_0_doesnt_crash(self):
        self.assertEqual(rotate_thru_carry_left_8_bits(0xEF, False, 0), (0xEF, False))
        
    def test_rotate_thru_carry_left_8_bits_by_8(self):
        self.assertEqual(rotate_thru_carry_left_8_bits(0x01, False, 8), (0x00, True))
        
    def test_rotate_thru_carry_left_8_bits_by_9(self):
        self.assertEqual(rotate_thru_carry_left_8_bits(0xEF, False, 9), (0xEF, False))
        
    def test_rotate_thru_carry_left_8_bits_by_more_than_9(self):
        self.assertEqual(rotate_thru_carry_left_8_bits(0x00, True, 10), (0x01, False))
        self.assertEqual(rotate_thru_carry_left_8_bits(0x80, False, 10), (0x00, True))
        
    # Rotate left 16 bits.
    def test_rotate_thru_carry_left_16_bits_by_1(self):
        self.assertEqual(rotate_thru_carry_left_16_bits(0x0000, True, 1), (0x0001, False))
        self.assertEqual(rotate_thru_carry_left_16_bits(0x0001, False, 1), (0x0002, False))
        self.assertEqual(rotate_thru_carry_left_16_bits(0x0080, True, 1), (0x0101, False))
        self.assertEqual(rotate_thru_carry_left_16_bits(0x8000, False, 1), (0x0000, True))
        
    def test_rotate_thru_carry_left_16_bits_by_3(self):
        self.assertEqual(rotate_thru_carry_left_16_bits(0x1234, False, 3), (0x91A0, False))
        self.assertEqual(rotate_thru_carry_left_16_bits(0x2345, True, 3), (0x1A2C, True))
        
    # # Rotate by zero will be handled by the caller.
    def test_rotate_thru_carry_left_16_bits_by_0_doesnt_crash(self):
        self.assertEqual(rotate_thru_carry_left_16_bits(0xCAFE, True, 0), (0xCAFE, True))
        
    def test_rotate_thru_carry_left_16_bits_by_8(self):
        self.assertEqual(rotate_thru_carry_left_16_bits(0xFACE, False, 8), (0xCE7D, False))
        
    def test_rotate_thru_carry_left_16_bits_by_16(self):
        self.assertEqual(rotate_thru_carry_left_16_bits(0xBEEF, True, 16), (0xDF77, True))
        
    def test_rotate_thru_carry_left_16_bits_by_17(self):
        self.assertEqual(rotate_thru_carry_left_16_bits(0xBEEF, True, 17), (0xBEEF, True))
        
    def test_rotate_thru_carry_left_16_bits_by_more_than_17(self):
        self.assertEqual(rotate_thru_carry_left_16_bits(0x1248, False, 18), (0x2490, False))
        
    # Rotate right 8 bits.
    def test_rotate_thru_carry_right_8_bits_by_1(self):
        self.assertEqual(rotate_thru_carry_right_8_bits(0x00, True, 1),  (0x80, False))
        self.assertEqual(rotate_thru_carry_right_8_bits(0x80, False, 1), (0x40, False))
        self.assertEqual(rotate_thru_carry_right_8_bits(0x40, False, 1), (0x20, False))
        self.assertEqual(rotate_thru_carry_right_8_bits(0x20, False, 1), (0x10, False))
        self.assertEqual(rotate_thru_carry_right_8_bits(0x10, False, 1), (0x08, False))
        self.assertEqual(rotate_thru_carry_right_8_bits(0x08, False, 1), (0x04, False))
        self.assertEqual(rotate_thru_carry_right_8_bits(0x04, False, 1), (0x02, False))
        self.assertEqual(rotate_thru_carry_right_8_bits(0x02, False, 1), (0x01, False))
        self.assertEqual(rotate_thru_carry_right_8_bits(0x01, False, 1), (0x00, True))
        
    def test_rotate_thru_carry_right_8_bits_by_3(self):
        self.assertEqual(rotate_thru_carry_right_8_bits(0x7, False, 3), (0xC0, True))
        self.assertEqual(rotate_thru_carry_right_8_bits(0x80, True, 3), (0x30, False))
        
    # Rotate by zero will be handled by the caller.
    def test_rotate_thru_carry_right_8_bits_by_0_doesnt_crash(self):
        self.assertEqual(rotate_thru_carry_right_8_bits(0xEF, False, 0), (0xEF, False))
        
    def test_rotate_thru_carry_right_8_bits_by_8(self):
        self.assertEqual(rotate_thru_carry_right_8_bits(0x80, False, 8), (0x00, True))
        
    def test_rotate_thru_carry_right_8_bits_by_9(self):
        self.assertEqual(rotate_thru_carry_right_8_bits(0xEF, False, 9), (0xEF, False))
        
    def test_rotate_thru_carry_right_8_bits_by_more_than_9(self):
        self.assertEqual(rotate_thru_carry_right_8_bits(0x00, True, 10), (0x80, False))
        self.assertEqual(rotate_thru_carry_right_8_bits(0x01, False, 10), (0x00, True))
        
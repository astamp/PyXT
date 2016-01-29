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
        
    def test_rotate_left_8_bits_by_0(self):
        self.assertEqual(rotate_left_8_bits(0xEF, 0), (0xEF, True))
        
    def test_rotate_left_8_bits_by_8(self):
        self.assertEqual(rotate_left_8_bits(0xEF, 8), (0xEF, True))
        
    def test_rotate_left_8_bits_by_more_than_8(self):
        self.assertEqual(rotate_left_8_bits(0x01, 9), (0x02, False))
        
    def test_rotate_left_16_bits_by_1(self):
        self.assertEqual(rotate_left_16_bits(0x0001, 1), (0x0002, False))
        self.assertEqual(rotate_left_16_bits(0x0080, 1), (0x0100, False))
        self.assertEqual(rotate_left_16_bits(0x8000, 1), (0x0001, True))
        
    def test_rotate_left_16_bits_by_3(self):
        self.assertEqual(rotate_left_16_bits(0xFFEF, 3), (0xFF7F, True))
        self.assertEqual(rotate_left_16_bits(0xDFFF, 3), (0xFFFE, False))
        
    def test_rotate_left_16_bits_by_0(self):
        self.assertEqual(rotate_left_16_bits(0xCAFE, 0), (0xCAFE, False))
        
    def test_rotate_left_16_bits_by_8(self):
        self.assertEqual(rotate_left_16_bits(0xFACE, 8), (0xCEFA, False))
        
    def test_rotate_left_16_bits_by_16(self):
        self.assertEqual(rotate_left_16_bits(0xBEEF, 16), (0xBEEF, True))
        
    def test_rotate_left_16_bits_by_more_than_16(self):
        self.assertEqual(rotate_left_16_bits(0xBEEF, 20), (0xEEFB, True))
        
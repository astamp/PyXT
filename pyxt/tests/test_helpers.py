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
            
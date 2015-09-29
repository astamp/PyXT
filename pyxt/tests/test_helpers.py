import unittest

from pyxt.helpers import segment_offset_to_address

class SegmentOffsetToAddressTests(unittest.TestCase):
    def test_segment_offset_to_address_simple(self):
        self.assertEqual(segment_offset_to_address(0x06EF, 0x1234), 0x8124)
        
    def test_segment_offset_to_address_high_segment(self):
        self.assertEqual(segment_offset_to_address(0x0812, 0x0004), 0x8124)
        
    def test_segment_offset_to_address_all_offset(self):
        self.assertEqual(segment_offset_to_address(0x0000, 0x8124), 0x8124)
        
    def test_segment_offset_to_address_reset_vector(self):
        self.assertEqual(segment_offset_to_address(0xFFFF, 0x0000), 0xFFFF0)
        
    def test_segment_offset_to_address_machine_id(self):
        self.assertEqual(segment_offset_to_address(0xF000, 0xFFFE), 0xFFFFE)
        
    def test_segment_offset_to_address_machine_id2(self):
        self.assertEqual(segment_offset_to_address(0xFFFF, 0x000E), 0xFFFFE)
        
    def test_segment_offset_to_address_wrap(self):
        self.assertEqual(segment_offset_to_address(0xFFFF, 0xFFFF), 0xFFEF)
        
import unittest

from pyxt.bus import *

class RandomAccessMemoryTests(unittest.TestCase):
    def setUp(self):
        self.obj = RAM(0x8000)
        
    def test_initialized_to_zero(self):
        for x in xrange(0, 0x8000):
            self.assertEqual(self.obj.read_byte(x), 0)
            
    def test_write_byte(self):
        self.obj.write_byte(56, 43)
        self.assertEqual(self.obj.contents[56], 43)
        
    def test_write_word(self):
        self.obj.write_word(56, 0x1234)
        self.assertEqual(self.obj.contents[56], 0x34)
        self.assertEqual(self.obj.contents[57], 0x12)
        
    def test_read_byte(self):
        self.obj.contents[1234] = 76
        self.obj.contents[1235] = 77
        self.obj.contents[1236] = 78
        self.assertEqual(self.obj.read_byte(1235), 77)
        
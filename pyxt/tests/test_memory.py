import unittest

from six.moves import range

from pyxt.tests.utils import get_test_file
from pyxt.memory import *

class RandomAccessMemoryTests(unittest.TestCase):
    def setUp(self):
        self.obj = RAM(0x8000)
        
    def test_initialized_to_zero(self):
        for x in range(0, 0x8000):
            self.assertEqual(self.obj.mem_read_byte(x), 0)
            
    def test_write_byte(self):
        self.obj.mem_write_byte(56, 43)
        self.assertEqual(self.obj.contents[56], 43)
        
    def test_write_word(self):
        self.obj.mem_write_word(56, 0x1234)
        self.assertEqual(self.obj.contents[56], 0x34)
        self.assertEqual(self.obj.contents[57], 0x12)
        
    def test_read_byte(self):
        self.obj.contents[1234] = 76
        self.obj.contents[1235] = 77
        self.obj.contents[1236] = 78
        self.assertEqual(self.obj.mem_read_byte(1235), 77)
        
    def test_get_memory_size(self):
        self.assertEqual(self.obj.get_memory_size(), 0x8000)
        
class ReadOnlyMemoryTests(unittest.TestCase):
    def setUp(self):
        self.rom = ROM(16, init_file = get_test_file(self, "romtest.bin"))
        
    def test_init_file(self):
        self.assertEqual(self.rom.mem_read_byte(0), six.byte2int(b"e"))
        self.assertEqual(self.rom.mem_read_byte(1), six.byte2int(b"a"))
        self.assertEqual(self.rom.mem_read_byte(2), six.byte2int(b"t"))
        self.assertEqual(self.rom.mem_read_byte(3), six.byte2int(b"-"))
        self.assertEqual(self.rom.mem_read_byte(4), six.byte2int(b"a"))
        self.assertEqual(self.rom.mem_read_byte(5), six.byte2int(b"-"))
        self.assertEqual(self.rom.mem_read_byte(6), six.byte2int(b"s"))
        self.assertEqual(self.rom.mem_read_byte(7), six.byte2int(b"t"))
        self.assertEqual(self.rom.mem_read_byte(8), six.byte2int(b"e"))
        self.assertEqual(self.rom.mem_read_byte(9), six.byte2int(b"a"))
        self.assertEqual(self.rom.mem_read_byte(10), six.byte2int(b"k"))
        
    def test_initialized_to_zero_past_file_length(self):
        for x in range(11, 16):
            self.assertEqual(self.rom.mem_read_byte(x), 0)
            
    def test_read_word(self):
        self.assertEqual(self.rom.mem_read_word(0), 0x6165)
        
    def test_write_byte_doesnt(self):
        self.rom.mem_write_byte(0, 0xFF)
        self.assertEqual(self.rom.mem_read_byte(0), 0x65)
        
    def test_write_word_doesnt(self):
        self.rom.mem_write_word(0, 0xFFFF)
        self.assertEqual(self.rom.contents[0], 0x65)
        self.assertEqual(self.rom.contents[1], 0x61)
        
    def test_get_memory_size(self):
        self.assertEqual(self.rom.get_memory_size(), 16)
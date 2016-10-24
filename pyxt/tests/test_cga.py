import unittest

from pyxt.cga import *
from pyxt.chargen import CharacterGeneratorMock, CHARGEN_ATTR_NONE, CHARGEN_ATTR_BRIGHT

class CGATests(unittest.TestCase):
    def setUp(self):
        self.chargen = CharacterGeneratorMock(width = 8, height = 8)
        self.cga = ColorGraphicsAdapter(self.chargen)
        
    def test_ports_list(self):
        self.assertEqual(self.cga.get_ports_list(), [0x3D0, 0x3D1, 0x3D2, 0x3D3,
                                                     0x3D4, 0x3D5, 0x3D6, 0x3D7,
                                                     0x3D8, 0x3D9, 0x3DA])
        
    def test_get_memory_size(self):
        self.assertEqual(self.cga.get_memory_size(), 16384)
        
    def test_initial_state(self):
        self.assertEqual(self.cga.data_reg_index, 0x00)
        self.assertEqual(self.cga.control_reg, 0x00)
        self.assertEqual(self.cga.screen, None)
        self.assertEqual(self.cga.char_generator, self.chargen)
        self.assertEqual(len(self.cga.video_ram), 16384)
        
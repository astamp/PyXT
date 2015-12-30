import unittest

from pyxt.mda import *
from pyxt.chargen import CharacterGeneratorMock, CHARGEN_ATTR_NONE, CHARGEN_ATTR_BRIGHT

class MDATests(unittest.TestCase):
    def setUp(self):
        self.cg = CharacterGeneratorMock(width = 9, height = 14)
        self.mda = MonochromeDisplayAdapter(self.cg)
        
    def test_ports_list(self):
        self.assertEqual(self.mda.get_ports_list(), [0x03B0, 0x03B1, 0x03B2, 0x03B3,
                                                     0x03B4, 0x03B5, 0x03B6, 0x03B7,
                                                     0x03B8, 0x03B9, 0x03BA, 0x03BB])
        
    def test_initial_state(self):
        self.assertEqual(self.mda.control_reg, 0x00)
        self.assertEqual(self.mda.control_reg, 0x00)
        self.assertEqual(self.mda.screen, None)
        self.assertEqual(self.mda.char_generator, self.cg)
        self.assertEqual(len(self.mda.video_ram), 4000)
        
    def test_mem_write_byte_updates_video_ram(self):
        self.mda.mem_write_byte(0x0000, 0x41)
        self.assertEqual(self.mda.video_ram[0x0000], 0x41)
        
    def test_mem_write_byte_calls_char_generator_top_left(self):
        self.mda.mem_write_byte(0x0000, 0x41)
        self.assertEqual(self.cg.last_blit, (None, (0, 0), 0x41, CHARGEN_ATTR_NONE))
        
    def test_mem_write_byte_calls_char_generator_bottom_right(self):
        self.mda.mem_write_byte(3998, 0xFF)
        self.assertEqual(self.cg.last_blit, (None, (711, 336), 0xFF, CHARGEN_ATTR_NONE))
        
    def test_mem_write_byte_char_before_attribute(self):
        self.mda.mem_write_byte(3998, 0xFF)
        self.assertEqual(self.cg.last_blit, (None, (711, 336), 0xFF, CHARGEN_ATTR_NONE))
        self.mda.mem_write_byte(3999, MDA_ATTR_INTENSITY)
        self.assertEqual(self.cg.last_blit, (None, (711, 336), 0xFF, CHARGEN_ATTR_BRIGHT))
        
    def test_mem_write_byte_attribute_before_char(self):
        self.mda.mem_write_byte(3999, MDA_ATTR_INTENSITY)
        self.assertEqual(self.cg.last_blit, (None, (711, 336), 0x00, CHARGEN_ATTR_BRIGHT))
        self.mda.mem_write_byte(3998, 0xFF)
        self.assertEqual(self.cg.last_blit, (None, (711, 336), 0xFF, CHARGEN_ATTR_BRIGHT))
        
    def test_mem_write_byte_write_off_screen(self):
        self.mda.mem_write_byte(4000, 0xFF)
        self.assertEqual(self.cg.last_blit, None)
        
    def test_mem_read_byte(self):
        self.mda.video_ram[77] = 0xA5
        self.assertEqual(self.mda.mem_read_byte(77), 0xA5)
        
    def test_mem_read_byte_off_screen(self):
        self.assertEqual(self.mda.mem_read_byte(4000), 0x00)
        
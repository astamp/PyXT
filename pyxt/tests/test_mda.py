import unittest

from pyxt.mda import *
from pyxt.chargen import CharacterGeneratorMock

class MDATests(unittest.TestCase):
    def setUp(self):
        self.cg = CharacterGeneratorMock(width = 9, height = 14)
        self.mda = MonochromeDisplayAdapter(self.cg)
        
        # Hijack reset so it doesn't call into Pygame during the tests.
        self.reset_count = 0
        self.mda.reset = self.reset_testable
        
    def reset_testable(self):
        self.reset_count += 1
        
    def test_ports_list(self):
        self.assertEqual(self.mda.get_ports_list(), [0x03B0, 0x03B1, 0x03B2, 0x03B3,
                                                     0x03B4, 0x03B5, 0x03B6, 0x03B7,
                                                     0x03B8, 0x03B9, 0x03BA, 0x03BB])
        
    def test_get_memory_size(self):
        self.assertEqual(self.mda.get_memory_size(), 4096)
        
    def test_initial_state(self):
        self.assertEqual(self.mda.control_reg, 0x00)
        self.assertEqual(self.mda.control_reg, 0x00)
        self.assertEqual(self.mda.screen, None)
        self.assertEqual(self.mda.char_generator, self.cg)
        self.assertEqual(len(self.mda.video_ram), 4096)
        
    def test_mem_write_byte_updates_video_ram(self):
        self.mda.mem_write_byte(0x0000, 0x41)
        self.assertEqual(self.mda.video_ram[0x0000], 0x41)
        
    def test_mem_write_byte_calls_char_generator_top_left(self):
        self.mda.mem_write_byte(0x0000, 0x41)
        self.assertEqual(self.cg.last_blit, (None, (0, 0), 0x41, MDA_GREEN, MDA_BLACK))
        
    def test_mem_write_byte_calls_char_generator_bottom_right(self):
        self.mda.mem_write_byte(3998, 0xFF)
        self.assertEqual(self.cg.last_blit, (None, (711, 336), 0xFF, MDA_GREEN, MDA_BLACK))
        
    def test_mem_write_byte_char_before_attribute(self):
        self.mda.mem_write_byte(3998, 0xFF)
        self.assertEqual(self.cg.last_blit, (None, (711, 336), 0xFF, MDA_GREEN, MDA_BLACK))
        self.mda.mem_write_byte(3999, MDA_ATTR_INTENSITY)
        self.assertEqual(self.cg.last_blit, (None, (711, 336), 0xFF, MDA_BRIGHT_GREEN, MDA_BLACK))
        
    def test_mem_write_byte_attribute_before_char(self):
        self.mda.mem_write_byte(3999, MDA_ATTR_INTENSITY)
        self.assertEqual(self.cg.last_blit, (None, (711, 336), 0x00, MDA_BRIGHT_GREEN, MDA_BLACK))
        self.mda.mem_write_byte(3998, 0xFF)
        self.assertEqual(self.cg.last_blit, (None, (711, 336), 0xFF, MDA_BRIGHT_GREEN, MDA_BLACK))
        
    def test_mem_write_byte_write_off_screen(self):
        self.mda.mem_write_byte(4000, 0xFF)
        self.assertEqual(self.cg.last_blit, None)
        
    def test_mem_read_byte(self):
        self.mda.video_ram[77] = 0xA5
        self.assertEqual(self.mda.mem_read_byte(77), 0xA5)
        
    def test_mem_read_byte_off_screen(self):
        self.assertEqual(self.mda.mem_read_byte(4000), 0x00)
        
    @unittest.skip("We need to initialize Pygame exactly once at startup.")
    def test_reset_on_high_resolution_enable(self):
        self.assertEqual(self.reset_count, 0)
        
        self.mda.io_write_byte(0x3B8, 0x01)
        self.assertEqual(self.reset_count, 1)
        
        # Second write shouldn't call reset again.
        self.mda.io_write_byte(0x3B8, 0x01)
        self.assertEqual(self.reset_count, 1)
        
    def test_mem_write_word_at_top_left(self):
        self.mda.mem_write_word(0x0000, 0x0841) # 'A' with intensity.
        self.assertEqual(self.mda.video_ram[0x0000], 0x41)
        self.assertEqual(self.mda.video_ram[0x0001], 0x08)
        self.assertEqual(self.cg.last_blit, (None, (0, 0), 0x41, MDA_BRIGHT_GREEN, MDA_BLACK))
        
    def test_mem_write_word_at_bottom_right(self):
        self.mda.mem_write_word(3998, 0x085A) # 'Z' with intensity.
        self.assertEqual(self.mda.video_ram[3998], 0x5A)
        self.assertEqual(self.mda.video_ram[3999], 0x08)
        self.assertEqual(self.cg.last_blit, (None, (711, 336), 0x5A, MDA_BRIGHT_GREEN, MDA_BLACK))
        
    def test_mem_write_word_at_bottom_right_just_past(self):
        self.mda.mem_write_word(3999, 0xFF08) # 'Z' with intensity.
        self.assertEqual(self.mda.video_ram[3998], 0x00) # Should be unmodified.
        self.assertEqual(self.mda.video_ram[3999], 0x08)
        self.assertEqual(self.cg.last_blit, (None, (711, 336), 0x00, MDA_BRIGHT_GREEN, MDA_BLACK))
        
    def test_mem_read_word(self):
        self.mda.video_ram[0x0000] = 0x41
        self.mda.video_ram[0x0001] = 0x08
        self.assertEqual(self.mda.mem_read_word(0x0000), 0x0841)
        
    def test_mem_read_word_just_past_the_end(self):
        self.mda.video_ram[3998] = 0x12
        self.mda.video_ram[3999] = 0x34
        self.assertEqual(self.mda.mem_read_word(3999), 0x0034)
        
    def test_horizontal_retrace_toggles(self):
        self.assertEqual(self.mda.io_read_byte(0x3BA), 0xF0)
        self.assertEqual(self.mda.io_read_byte(0x3BA), 0xF1)
        self.assertEqual(self.mda.io_read_byte(0x3BA), 0xF0)
        
    def test_current_pixel_updates_on_status_read(self):
        self.assertEqual(self.mda.current_pixel, [0, 0])
        self.mda.io_read_byte(0x3BA)
        self.assertEqual(self.mda.current_pixel, [1, 0])
        
    def test_current_pixel_wraps_right(self):
        self.mda.current_pixel = [719, 0]
        self.mda.io_read_byte(0x3BA)
        self.assertEqual(self.mda.current_pixel, [0, 1])
        
    def test_current_pixel_wraps_bottom(self):
        self.mda.current_pixel = [719, 349]
        self.mda.io_read_byte(0x3BA)
        self.assertEqual(self.mda.current_pixel, [0, 0])
        
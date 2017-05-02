from __future__ import print_function
import unittest

import pygame
from pyxt.chargen import *

from six.moves import range # pylint: disable=redefined-builtin

TEST_CHAR = b"\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xAA\xBB\xCC\xDD\xEE\xFF"

def dump_surface(test_surface):
    width, height = test_surface.get_size()
    for y in range(height):
        for x in range(width):
            print(test_surface.get_at_mapped((x, y)), end = " ")
        print()

class CharacterGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.chargen = CharacterGenerator(16, 8)
        
    def test_default_char_count(self):
        self.assertEqual(self.chargen.CHAR_COUNT, 256)
        
    def test_char_height_and_width(self):
        self.assertEqual(self.chargen.char_height, 16)
        self.assertEqual(self.chargen.char_width, 8)
        
    def test_internal_surface_geometry(self):
        self.assertEqual(self.chargen.font_bitmaps_alpha.get_width(), 2048) # 256 * 8
        self.assertEqual(self.chargen.font_bitmaps_alpha.get_height(), 16)
        
    def test_store_character_simple(self):
        self.chargen.store_character(40, TEST_CHAR)
        # 0xAA from above.
        #   ^--- The first A.
        self.assertEqual(self.chargen.font_bitmaps_alpha.get_at_mapped((320, 10)), -1) # 0xFFFFFFFF
        self.assertEqual(self.chargen.font_bitmaps_alpha.get_at_mapped((321, 10)), 0)
        self.assertEqual(self.chargen.font_bitmaps_alpha.get_at_mapped((322, 10)), -1) # 0xFFFFFFFF
        self.assertEqual(self.chargen.font_bitmaps_alpha.get_at_mapped((323, 10)), 0)
        
    def test_store_character_out_of_bounds_valueError(self):
        with self.assertRaises(AssertionError):
            self.chargen.store_character(256, TEST_CHAR) # Max index is 255.
            
    def test_blit_character(self):
        self.chargen.store_character(40, TEST_CHAR)
        test_surface = pygame.Surface((10, 20), pygame.SRCALPHA)
        self.chargen.blit_character(test_surface, (1, 2), 40, (255, 255, 0), (0, 0, 0))
        
        # 0xAA from above.
        #   ^--- The first A.
        self.assertEqual(test_surface.get_at((1, 12)), (255, 255, 0, 255))
        self.assertEqual(test_surface.get_at((2, 12)), (0, 0, 0, 255))
        self.assertEqual(test_surface.get_at((3, 12)), (255, 255, 0, 255))
        self.assertEqual(test_surface.get_at((4, 12)), (0, 0, 0, 255))
        
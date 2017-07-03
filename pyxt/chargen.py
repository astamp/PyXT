"""
pyxt.mda - Monochrome display adapter for PyXT based on Pygame.
"""

# Standard library imports
from collections import namedtuple

# PyXT imports

# Pygame Imports
import pygame

# Six imports
import six

# Constants
COLUMN_AND_MASK_7_TO_0 = (
    (0, 0x80),
    (1, 0x40),
    (2, 0x20),
    (3, 0x10),
    (4, 0x08),
    (5, 0x04),
    (6, 0x02),
    (7, 0x01),
)

# Classes
class CharacterGenerator(object):
    """ Generates glyphs for a given character. """
    CHAR_COUNT = 256
    
    def __init__(self, height, width):
        self.char_height = height
        self.char_width = width
        self.font_bitmaps_alpha = pygame.Surface((width * self.CHAR_COUNT, height), pygame.SRCALPHA)
        self.working_char = pygame.Surface((self.char_width, self.char_height), pygame.SRCALPHA)
        
    def blit_character(self, surface, location, index, foreground, background):
        """ Place a character onto a surface at the given location. """
        # We may exceed the character count in "real-life" situations, particularly when running
        # with the CharacterGeneratorBIOS which only has the first 128 characters.
        if index >= self.CHAR_COUNT:
            return
            
        surface.fill(background, (location[0], location[1], self.char_width, self.char_height))
        self.working_char.fill(foreground)
        self.working_char.blit(self.font_bitmaps_alpha, (0, 0), (self.char_width * index, 0, self.char_width, self.char_height), pygame.BLEND_RGBA_MIN)
        surface.blit(self.working_char, location)
        
    def store_character(self, index, data, row_byte_width = 1):
        """ Stores a glyph bitmap into the internal font data structure. """
        # Ensure we don't overrun the character count when setting up the object.
        assert index < self.CHAR_COUNT, "index %d out of range (%d)" % (index, self.CHAR_COUNT)
        
        pixel_access = pygame.PixelArray(self.font_bitmaps_alpha)
        
        for row in range(0, self.char_height):
            row_data = data[row * row_byte_width : (row + 1) * row_byte_width]
            for byte in six.iterbytes(row_data):
                for column, mask in COLUMN_AND_MASK_7_TO_0:
                    if byte & mask:
                        pixel_access[(index * self.char_width) + column, row] = (255, 255, 255, 255)
                        
        # Make sure to explicitly del this to free the surface lock.
        del pixel_access
        
class CharacterGeneratorBIOS(CharacterGenerator):
    """ Character generator that uses the 8x8 backup glyph set in the PC BIOS. """
    FONT_OFFSET = 0xFA6E
    CHAR_COUNT = 128
    CHAR_WIDTH_BYTES = 1
    CHAR_WIDTH_PIXELS = CHAR_WIDTH_BYTES * 8
    CHAR_HEIGHT_PIXELS = 8
    
    def __init__(self, bios_file):
        super(CharacterGeneratorBIOS, self).__init__(self.CHAR_WIDTH_PIXELS, self.CHAR_HEIGHT_PIXELS)
        
        with open(bios_file, "rb") as fileptr:
            fileptr.seek(self.FONT_OFFSET)
            for index in xrange(self.CHAR_COUNT):
                data = fileptr.read(self.CHAR_HEIGHT_PIXELS * self.CHAR_WIDTH_BYTES)
                self.store_character(index, data)
        
class CharacterGeneratorMock(CharacterGenerator):
    """ Mock version of the character generator for unit testing. """
    def __init__(self, height, width):
        super(CharacterGeneratorMock, self).__init__(height, width)
        self.last_blit = None
        
    def blit_character(self, surface, location, index, foreground, background):
        self.last_blit = (surface, location, index, foreground, background)
        
class CharacterGeneratorMDA_CGA_ROM(CharacterGenerator):
    """
    Character generator that uses the ROM image from the IBM MDA and printer card.
    
    This part was also used on the CGA adapter and contains those fonts as well.
    Many thanks to Jonathan Hunt who dumped the contents of the ROM and wrote code to interpret it.
    """
    MDA_FONT = 0
    CGA_NARROW_FONT = 1
    CGA_WIDE_FONT = 2
    
    PAGE_SIZE = 2048
    
    FontInfo = namedtuple("FontInfo", ["start_address", "byte_width", "rows_stored", "cols_actual", "rows_actual"])
    
    FONT_INFO = {
        # (Start address, byte width, rows in data, cols actual, rows actual)
        MDA_FONT : FontInfo(0x0000, 1, 16, 9, 14),
        CGA_NARROW_FONT : FontInfo(0x1000, 1, 8, 8, 8),
        CGA_WIDE_FONT : FontInfo(0x1800, 1, 8, 8, 8),
    }
    
    def __init__(self, rom_file, font):
        font_info = self.FONT_INFO[font]
        super(CharacterGeneratorMDA_CGA_ROM, self).__init__(font_info.rows_actual, font_info.cols_actual)
        
        # The characters are split top and bottom across the first 2 2k pages of the part.
        with open(rom_file, "rb") as fileptr:
            fileptr.seek(font_info.start_address)
            upper_half = fileptr.read(self.PAGE_SIZE)
            lower_half = fileptr.read(self.PAGE_SIZE)
            
        for index in range(self.CHAR_COUNT):
            data = upper_half[index * 8 : (index + 1) * 8]
            if self.char_height > 8:
                data += lower_half[index * 8 : (index + 1) * 8]
                
            self.store_character(index, data)
            
            # The ninth column of the MDA frame is a copy of the 8th for this range of characters only.
            # See: http://www.seasip.info/VintagePC/mda.html#memmap
            if font == self.MDA_FONT and index >= 0xC0 and index <= 0xDF:
                self.font_bitmaps_alpha.blit(self.font_bitmaps_alpha, ((index * self.char_width) + 8, 0), ((index * self.char_width) + 7, 0, 1, self.char_height))
                
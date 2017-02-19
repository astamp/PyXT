"""
pyxt.mda - Monochrome display adapter for PyXT based on Pygame.
"""

# Standard library imports

# PyXT imports

# Pygame Imports
import pygame

# Constants
EGA_BLACK = (0x00, 0x00, 0x00)
EGA_GREEN = (0x00, 0xAA, 0x00)
EGA_BRIGHT_GREEN = (0x55, 0xFF, 0x55)

MAX_CHAR_COUNT = 256
BITS_7_TO_0 = (0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01)

# Classes
class CharacterGenerator(object):
    """ Generates glyphs for a given character. """
    def __init__(self, height, width):
        self.char_height = height
        self.char_width = width
        self.font_bitmaps_alpha = pygame.Surface((width * MAX_CHAR_COUNT, height), pygame.SRCALPHA)
        
    def blit_character(self, surface, location, index, foreground, background):
        """ Place a character onto a surface at the given location. """
        raise NotImplementedError
        
    def store_character(self, index, data, row_byte_width = 1):
        """ Stores a glyph bitmap into the internal font data structure. """
        pixel_access = pygame.PixelArray(self.font_bitmaps_alpha)
        
        for y in range(0, self.char_height):
            row = data[y * row_byte_width : (y + 1) * row_byte_width]
            for byte in six.iterbytes(row):
                for bit in BITS_7_TO_0:
                    pixel_access[(index * self.char_width) + (7 - bit), row] = (255, 255, 255, 255)
                    
        # Make sure to explicitly del this to free the surface lock.
        del pixel_access
        
class CharacterGeneratorBIOS(CharacterGenerator):
    """ Character generator that uses the 8x8 backup glyph set in the PC BIOS. """
    FONT_OFFSET = 0xFA6E
    RESIDENT_CHARS = 128
    CHAR_WIDTH_BYTES = 1
    CHAR_WIDTH_PIXELS = CHAR_WIDTH_BYTES * 8
    CHAR_HEIGHT_PIXELS = 8
    
    def __init__(self, bios_file):
        self.font_data = pygame.Surface((8 * self.RESIDENT_CHARS, 8)) # pylint: disable=too-many-function-args
        self.font_data.fill(EGA_BLACK)
        pix = pygame.PixelArray(self.font_data) # pylint: disable=too-many-function-args
        
        with open(bios_file, "rb") as fileptr:
            fileptr.seek(self.FONT_OFFSET)
            for index in xrange(self.RESIDENT_CHARS):
                for row in xrange(0, self.CHAR_HEIGHT_PIXELS):
                    byte = ord(fileptr.read(1))
                    for bit in xrange(self.CHAR_WIDTH_PIXELS):
                        if (1 << (self.CHAR_WIDTH_PIXELS - bit)) & byte:
                            pix[(index * self.CHAR_WIDTH_PIXELS) + bit, row] = EGA_GREEN
                            
        # Make sure to explicitly del this to free the surface lock.
        del pix
        
    def blit_character(self, surface, location, index, foreground, background):
        if index >= self.RESIDENT_CHARS:
            return
        surface.blit(self.font_data, location, area = (8 * index, 0, 8, 8))
        
    @property
    def char_width(self):
        return 8
        
    @property
    def char_height(self):
        return 8
        
class CharacterGeneratorMock(CharacterGenerator):
    """ Mock version of the character generator for unit testing. """
    def __init__(self, **kwargs):
        super(CharacterGeneratorMock, self).__init__()
        self.last_blit = None
        self.width = kwargs.get("width", 0)
        self.height = kwargs.get("height", 0)
        
    def blit_character(self, surface, location, index, foreground, background):
        self.last_blit = (surface, location, index, foreground, background)
        
    @property
    def char_width(self):
        return self.width
        
    @property
    def char_height(self):
        return self.height
        
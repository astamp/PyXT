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

CHARGEN_ATTR_NONE = 0x0000
CHARGEN_ATTR_BRIGHT = 0x0001

# Classes
class CharacterGenerator(object):
    """ Generates glyphs for a given character. """
    def blit_character(self, surface, location, index, attributes = CHARGEN_ATTR_NONE):
        """ Place a character onto a surface at the given location. """
        raise NotImplementedError
        
    @property
    def char_width(self):
        """ Returns the width of characters in pixels. """
        raise NotImplementedError
        
    @property
    def char_height(self):
        """ Returns the width of characters in pixels. """
        raise NotImplementedError
        
class CharacterGeneratorBIOS(CharacterGenerator):
    """ Character generator that uses the 8x8 backup glyph set in the PC BIOS. """
    FONT_OFFSET = 0xFA6E
    RESIDENT_CHARS = 128
    CHAR_WIDTH_BYTES = 1
    CHAR_WIDTH_PIXELS = CHAR_WIDTH_BYTES * 8
    CHAR_HEIGHT_PIXELS = 8
    
    def __init__(self, bios_file):
        self.font_data = pygame.Surface((8 * self.RESIDENT_CHARS, 8))
        self.font_data.fill(BLACK)
        pix = pygame.PixelArray(self.font_data)
        
        with open(bios_file, "rb") as fileptr:
            fileptr.seek(self.FONT_OFFSET)
            for index in xrange(self.RESIDENT_CHARS):
                for row in xrange(0, self.CHAR_HEIGHT_PIXELS):
                    byte = ord(fileptr.read(1))
                    for bit in xrange(self.CHAR_WIDTH_PIXELS):
                        if (1 << (self.CHAR_WIDTH_PIXELS - bit)) & byte:
                            pix[(index * self.CHAR_WIDTH_PIXELS) + bit, row] = GREEN
                            
        # Make sure to explicitly del this to free the surface lock.
        del pix
        
    def blit_character(self, surface, location, index, attributes = CHARGEN_ATTR_NONE):
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
        
    def blit_character(self, surface, location, index, attributes = CHARGEN_ATTR_NONE):
        self.last_blit = (surface, location, index, attributes)
        
    @property
    def char_width(self):
        return self.width
        
    @property
    def char_height(self):
        return self.height
        
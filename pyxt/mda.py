"""
pyxt.mda - Monochrome display adapter for PyXT based on Pygame.

Some really useful info was gathered here:
http://www.seasip.info/VintagePC/mda.html
"""

# Standard library imports
import array
from collections import namedtuple

# Six imports
from six.moves import range # pylint: disable=redefined-builtin

# PyXT imports
from pyxt.bus import Device
from pyxt.helpers import *
from pyxt.constants import *
from pyxt.chargen import *

# Pygame Imports
import pygame

# Constants
MDA_START_ADDRESS = 0xB0000

MDA_RESOLUTION = 720, 350
MDA_PORTS_START = 0x3B0
MDA_PORTS_END = 0x3BB # Don't include the parallel port on the MDA card.
DATA_REG_INDEX_PORTS = (0x3B0, 0x3B2, 0x3B4, 0x3B6)
DATA_REG_ACCESS_PORTS = (0x3B1, 0x3B3, 0x3B5, 0x3B7)

CONTROL_REG_PORT = 0x3B8
CONTROL_REG_HIRES = 0x01
CONTROL_REG_VIDEO_ENABLE = 0x08
CONTROL_REG_ENABLINK = 0x20

MDA_ATTR_UNDERLINE =  0x01
MDA_ATTR_FOREGROUND = 0x07
MDA_ATTR_INTENSITY =  0x08
MDA_ATTR_BACKGROUND = 0x70
MDA_ATTR_BLINK =      0x80

MDA_COLUMNS = 80
MDA_ROWS = 25
MDA_BYTES_PER_CHAR = 2

# TODO: This is 4000, does this need to be a round 4k for compatibility?
MDA_RAM_SIZE = MDA_COLUMNS * MDA_ROWS * MDA_BYTES_PER_CHAR

BITS_LO_TO_HI = [7, 6, 5, 4, 3, 2, 1, 0]

# Classes
class MonochromeDisplayAdapter(Device):
    def __init__(self, char_generator):
        super(MonochromeDisplayAdapter, self).__init__()
        
        self.char_generator = char_generator
        
        self.control_reg = 0x00
        self.data_reg_index = 0x00
        
        self.video_ram = array.array("B", (0,) * MDA_RAM_SIZE)
        
        self.screen = None
        # self.reset()
        
    def reset(self):
        pygame.init()
        self.screen = pygame.display.set_mode(MDA_RESOLUTION)
        pygame.display.set_caption("PyXT Monochrome Display Adapter")
        
    def get_memory_size(self):
        return 4096
        
    def mem_read_word(self, offset):
        # TODO: Combine this into one operation for speed.
        return (self.mem_read_byte(offset) | (self.mem_read_byte(offset + 1) << 8))
        
    def mem_read_byte(self, offset):
        if offset >= MDA_RAM_SIZE:
            return 0x00
            
        return self.video_ram[offset]
        
    def mem_write_word(self, offset, value):
        # 0xCAFE => 0:0xFE & 1:0xCA
        # TODO: Combine this into one operation for speed.
        self.mem_write_byte(offset, value & 0x00FF)
        self.mem_write_byte(offset + 1, (value >> 8) & 0x00FF)
        
    def mem_write_byte(self, offset, value):
        if offset >= MDA_RAM_SIZE:
            return
            
        # Direct write to the "video RAM" for reading back.
        self.video_ram[offset] = value
        
        # Odd bytes are the attributes.
        if offset & 0x0001 == 0x0001:
            character = self.video_ram[offset - 1]
            attributes = value
        else:
            character = value
            attributes = self.video_ram[offset + 1]
            
        # Shift off the lowest bit to get the location base.
        offset = offset >> 1
        
        row = offset // MDA_COLUMNS
        column = offset % MDA_COLUMNS
        
        # This should be handled by the check above.
        # if row >= MDA_ROWS:
            # return
            
        # Fill in the internal character generator attributes.
        cg_attributes = CHARGEN_ATTR_NONE
        if attributes & MDA_ATTR_INTENSITY:
            cg_attributes |= CHARGEN_ATTR_BRIGHT
            
        self.char_generator.blit_character(self.screen, (column * self.char_generator.char_width, row * self.char_generator.char_height), character, cg_attributes)
        
    def get_ports_list(self):
        # range() is not inclusive so add one.
        return [x for x in range(MDA_PORTS_START, MDA_PORTS_END + 1)]
        
    def io_read_byte(self, port):
        if port in DATA_REG_ACCESS_PORTS:
            return 0x00 # self.read_crt_data_register(self.data_reg_index)
            
        elif port == CONTROL_REG_PORT:
            return self.control_reg
            
        else:
            return 0x00
            
    def io_write_byte(self, port, value):
        if port in DATA_REG_INDEX_PORTS:
            self.data_reg_index = value
            
        elif port in DATA_REG_ACCESS_PORTS:
            pass # self.write_crt_data_register(self.data_reg_index, value)
            
        elif port == CONTROL_REG_PORT:
            # The first time we see the enable bit, "reset" the MDA card.
            if self.control_reg & CONTROL_REG_HIRES == 0x00 and value & CONTROL_REG_HIRES == CONTROL_REG_HIRES:
                self.reset()
                
            self.control_reg = value
            
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
    CHAR_COUNT = 256
    
    FontInfo = namedtuple("FontInfo", ["start_address", "byte_width", "rows_stored", "cols_actual", "rows_actual"])
    
    FONT_INFO = {
        # (Start address, byte width, rows in data, cols actual, rows actual)
        MDA_FONT : FontInfo(0x0000, 1, 16, 9, 14),
        CGA_NARROW_FONT : FontInfo(0x1000, 1, 8, 8, 8),
        CGA_WIDE_FONT : FontInfo(0x1800, 1, 8, 8, 8),
    }
    
    def __init__(self, rom_file, font = MDA_FONT):
        self.font_info = self.FONT_INFO[font]
        
        self.font_data_normal = pygame.Surface((self.font_info.cols_actual * self.CHAR_COUNT, self.font_info.rows_actual))
        self.font_data_normal.fill(EGA_BLACK)
        
        self.font_data_bright = pygame.Surface((self.font_info.cols_actual * self.CHAR_COUNT, self.font_info.rows_actual))
        self.font_data_bright.fill(EGA_BLACK)
        
        pix_normal = pygame.PixelArray(self.font_data_normal)
        pix_bright = pygame.PixelArray(self.font_data_bright)
        
        # The characters are split top and bottom across the first 2 2k pages of the part.
        with open(rom_file, "rb") as fileptr:
            fileptr.seek(self.font_info.start_address)
            upper_half = fileptr.read(self.PAGE_SIZE)
            lower_half = fileptr.read(self.PAGE_SIZE)
            
        for index in xrange(self.CHAR_COUNT):
            for row in xrange(0, self.font_info.rows_actual):
                if row < 8:
                    byte = ord(upper_half[(index * 8) + row])
                else:
                    byte = ord(lower_half[(index  * 8) + (row - 8)])
                    
                for bit in BITS_LO_TO_HI:
                    if (1 << bit) & byte:
                        pix_normal[(index * self.char_width) + (7 - bit), row] = EGA_GREEN
                        pix_bright[(index * self.char_width) + (7 - bit), row] = EGA_BRIGHT_GREEN
                        
                # For the box drawing characters, the last column is duplicated for continuous lines.
                if self.char_width == 9 and 0xC0 <= index <= 0xDF:
                    if byte & 0x01:
                        pix_normal[(index * self.char_width) + 8, row] = EGA_GREEN
                        pix_bright[(index * self.char_width) + 8, row] = EGA_BRIGHT_GREEN
                        
        # Make sure to explicitly del this to free the surface lock.
        del pix_normal
        del pix_bright
        
    def blit_character(self, surface, location, index, attributes = CHARGEN_ATTR_NONE):
        """ Place a character onto a surface at the given location. """
        if index >= self.CHAR_COUNT:
            return
            
        font_data = self.font_data_normal
        if attributes & CHARGEN_ATTR_BRIGHT:
            font_data = self.font_data_bright
            
        surface.blit(font_data, location, area = (self.char_width * index, 0, self.char_width, self.char_height))
        pygame.display.flip()
        
    @property
    def char_width(self):
        """ Returns the width of characters in pixels. """
        return self.font_info.cols_actual
        
    @property
    def char_height(self):
        """ Returns the width of characters in pixels. """
        return self.font_info.rows_actual
        
# Test application.
def main():
    """ Test application for the MDA card. """
    import sys
    
    print("MDA test application.")
    char_generator = CharacterGeneratorMDA_CGA_ROM(sys.argv[1], CharacterGeneratorMDA_CGA_ROM.MDA_FONT)
    
    mda = MonochromeDisplayAdapter(char_generator)
    mda.reset()
    
    # Test the font.
    for x in xrange(256):
        mda.mem_write_byte((x % 32) + ((x // 32) * 80) << 1, x)
        
    # Test screen width and setting attributes after setting chars.
    for x in xrange(80):
        mda.mem_write_byte((x << 1) + 1600, 0x30 + (x % 10))
        mda.mem_write_byte((x << 1) + 1600 + 1, 0x08 if x & 0x01 else 0x00)
        
    # Test setting attributes before setting chars.
    for x in xrange(5):
        mda.mem_write_byte((x << 1) + 1920 + 1, 0x08)
    for x, char in enumerate("Hello world"):
        mda.mem_write_byte((x << 1) + 1920, ord(char))
        
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
                
if __name__ == "__main__":
    main()
    
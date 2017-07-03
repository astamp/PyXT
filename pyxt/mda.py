"""
pyxt.mda - Monochrome display adapter for PyXT based on Pygame.

Some really useful info was gathered here:
http://www.seasip.info/VintagePC/mda.html
"""

# Standard library imports
import array
import random
from collections import namedtuple

# Six imports
import six
from six.moves import range # pylint: disable=redefined-builtin

# PyXT imports
from pyxt.bus import Device
from pyxt.helpers import *
from pyxt.constants import *
from pyxt.chargen import CharacterGeneratorMDA_CGA_ROM

# Pygame Imports
import pygame

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

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

STATUS_REG_PORT = 0x3BA
STATUS_REG_BASE = 0xF0
STATUS_REG_PIXEL_ON = 0x08
STATUS_REG_HORIZONTAL_RETRACE = 0x01

MDA_ATTR_UNDERLINE =  0x01
MDA_ATTR_FOREGROUND = 0x07
MDA_ATTR_INTENSITY =  0x08
MDA_ATTR_BACKGROUND = 0x70
MDA_ATTR_BLINK =      0x80

MDA_COLUMNS = 80
MDA_ROWS = 25
MDA_BYTES_PER_CHAR = 2

# WARNING: This has to be 4k in order to pass the memory test! (Was 4000)
# MDA_RAM_SIZE = MDA_COLUMNS * MDA_ROWS * MDA_BYTES_PER_CHAR
MDA_RAM_SIZE = 4096

MDA_BLACK = (0x00, 0x00, 0x00)
MDA_GREEN = (0x00, 0xAA, 0x00)
MDA_BRIGHT_GREEN = (0x55, 0xFF, 0x55)

# https://superuser.com/questions/361297/what-colour-is-the-dark-green-on-old-fashioned-green-screen-computer-displays
MDA_CRT_BACKGROUND = (0x28, 0x28, 0x28)
MDA_AMBER = (0xFF, 0xB0, 0x00)
MDA_BRIGHT_AMBER = (0xFF, 0xCC, 0x00)

MonoPalette = namedtuple("MonoPalette", ["off", "on", "bright"])
PALETTE_GREEN = MonoPalette(MDA_BLACK, MDA_GREEN, MDA_BRIGHT_GREEN)
PALETTE_AMBER = MonoPalette(MDA_CRT_BACKGROUND, MDA_AMBER, MDA_BRIGHT_AMBER)
MONO_PALETTES = {
    "green" : PALETTE_GREEN,
    "amber" : PALETTE_AMBER,
}

# Classes
class Cursor(object):
    """ Structure containing the cursor parameters. """
    NO_BLINK = 0
    FAST_BLINK_RATE = 16
    MEDIUM_BLINK_RATE = 24
    SLOW_BLINK_RATE = 32
    
    MODE_MASK = 0x60
    MODE_NORMAL = 0x00
    MODE_ALWAYS_OFF = 0x20
    MODE_FAST_BLINK = 0x40
    MODE_SLOW_BLINK = 0x60
    
    def __init__(self):
        self.addr = 0 # Character location in video memory to place the cursor.
        self.start = 0 # Top scanline of the cursor relative to the character cell.
        self.end = 0 # Bottom scanline of the cursor relative to the character cell.
        self.interval = self.SLOW_BLINK_RATE # Number of vertical refreshes per cursor blink.
        self.timer = 0 # Current index into vertical refresh interval.
        self.enabled = True
        self.mode = None # Intentionally None to force set_mode to update.
        
        self.displayed = False # Is the cursor currently displayed on the screen.
        self.displayed_addr = 0 # Location of currently displayed cursor.
        
        self.set_mode(self.MODE_NORMAL)
        
    def set_mode(self, mode):
        """ Set the cursor mode from bits 5 and 6 of the top scanline byte. """
        if mode != self.mode:
            self.mode = mode
            self.timer = 0
            self.enabled = True
            
            if mode == self.MODE_NORMAL:
                self.interval = self.MEDIUM_BLINK_RATE
                
            elif mode == self.MODE_ALWAYS_OFF:
                self.interval = self.NO_BLINK
                self.enabled = False
                
            elif mode == self.MODE_FAST_BLINK:
                self.interval = self.FAST_BLINK_RATE
                
            elif mode == self.MODE_SLOW_BLINK:
                self.interval = self.SLOW_BLINK_RATE
                
class MonochromeDisplayAdapter(Device):
    def __init__(self, char_generator, randomize = False, palette = PALETTE_GREEN):
        super(MonochromeDisplayAdapter, self).__init__()
        
        self.char_generator = char_generator
        
        self.control_reg = 0x00
        self.data_reg_index = 0x00
        
        self.video_ram = array.array("B", (0,) * MDA_RAM_SIZE)
        
        # If desired, randomize the contents of video memory at startup for effect.
        if randomize:
            for index in range(MDA_RAM_SIZE):
                self.video_ram[index] = random.randint(0, 255)
                
        # Handle to the Pygame display object.
        self.screen = None
        
        # Flag to indicate if we have updated the bitmap and need to display it.
        self.needs_draw = True
        
        # Every other call to the status register will flip the horizontal retrace bit.
        self.horizontal_retrace = False
        
        # Used to simulate the pixel on bit when the status register is being read.
        self.current_pixel = [0, 0]
        
        # Cursor parameters.
        self.cursor = Cursor()
        
        # Palette (off, on, bright).
        self.palette = palette
        
    def reset(self):
        pygame.init()
        self.screen = pygame.display.set_mode(MDA_RESOLUTION)
        pygame.display.set_caption("PyXT Monochrome Display Adapter")
        
        # Now that we have a display draw whatever is currently in RAM.
        self.redraw()
        
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
        
        # Reblit using the character as the base, not an attribute.
        self.blit_single_char(offset & 0x1FFE)
        
        # Mark that the display bitmap is dirty and needs to be updated.
        self.needs_draw = True
        
    def get_ports_list(self):
        # range() is not inclusive so add one.
        return [x for x in range(MDA_PORTS_START, MDA_PORTS_END + 1)]
        
    def io_read_byte(self, port):
        if port in DATA_REG_ACCESS_PORTS:
            # log.warning("Data reg port 0x%03x read, returning 0x00!", port)
            return 0x00 # self.read_crt_data_register(self.data_reg_index)
            
        elif port == CONTROL_REG_PORT:
            log.debug("Control reg port 0x%03x read, returning 0x%02x!", port, self.control_reg)
            return self.control_reg
            
        elif port == STATUS_REG_PORT:
            status = STATUS_REG_BASE
            if self.get_current_pixel():
                status |= STATUS_REG_PIXEL_ON
            if self.horizontal_retrace:
                status |= STATUS_REG_HORIZONTAL_RETRACE
                
            self.horizontal_retrace = not self.horizontal_retrace
            return status
            
        else:
            # log.warning("Unknown port 0x%03x read, returning 0x00!", port)
            return 0x00
            
    def io_write_byte(self, port, value):
        if port in DATA_REG_INDEX_PORTS:
            # log.warning("Data reg index port 0x%03x written with 0x%02x!", port, value)
            self.data_reg_index = value
            
        elif port in DATA_REG_ACCESS_PORTS:
            # log.warning("Data reg access port 0x%03x written with 0x%02x!", port, value)
            self.write_crt_data_register(self.data_reg_index, value)
            
        elif port == CONTROL_REG_PORT:
            log.debug("Control reg port 0x%03x written with 0x%02x!", port, value)
            self.control_reg = value
            
    def write_crt_data_register(self, index, value):
        """ Handles writes to the 6845 CRT controller's parameters. """
        cursor = self.cursor
        
        # if index == 1:
            # log.debug("Character columns: %d", value)
        # elif index == 6:
            # log.debug("Character rows: %d", value)
        # elif index == 9:
            # log.debug("Character scanlines: %d", value + 1)
            
        if index == 10:
            cursor.start = value & 0x1F
            cursor.set_mode(value & cursor.MODE_MASK)
        elif index == 11:
            cursor.end = value
        elif index == 14:
            cursor.addr = (cursor.addr & 0x00FF) | (value << 8)
        elif index == 15:
            cursor.addr = (cursor.addr & 0xFF00) | value
        else:
            log.debug("Other CRT data register 0x%02x written with 0x%02x!", index, value)
        
    def draw(self):
        """ Update the "physical" display if necessary. """
        cursor = self.cursor
        
        # If blinking is enabled, is it time to blink?
        blink_cursor = False
        if cursor.interval:
            cursor.timer += 1
            if cursor.timer > cursor.interval:
                cursor.timer = 0
                blink_cursor = True
                
        # If we are blinking or need to move the cursor.
        if blink_cursor or cursor.addr != cursor.displayed_addr:
            # Re-display the character at the last cursor position to erase the cursor.
            if cursor.displayed:
                self.blit_single_char(cursor.displayed_addr << 1)
                
            elif cursor.enabled:
                # Draw the cursor over the current character.
                row = cursor.addr // MDA_COLUMNS
                column = cursor.addr % MDA_COLUMNS
                pygame.draw.rect(self.screen, self.palette.on, [column * 9, (row * 14) + cursor.start, 9, (cursor.end - cursor.start) + 1])
                
                # Log where the cursor is located so we can erase it.
                cursor.displayed_addr = cursor.addr
                
            # Force a redraw and toggle the cursor active.
            self.needs_draw = True
            cursor.displayed = not cursor.displayed
            
        if self.needs_draw:
            pygame.display.flip()
            self.needs_draw = False
            
    def redraw(self):
        """ Does a full redraw of the display from RAM. """
        for offset in range(0, MDA_RAM_SIZE, 2):
            self.blit_single_char(offset)
            
        self.needs_draw = True
        
    def blit_single_char(self, offset):
        """ Blits a single character to the display given the offset of the character. """
        if offset >= MDA_RAM_SIZE:
            return
            
        # Get the character and attributes from RAM.
        character = self.video_ram[offset]
        attributes = self.video_ram[offset + 1]
        
        # Shift off the lowest bit to get the location base.
        offset = offset >> 1
        row = offset // MDA_COLUMNS
        column = offset % MDA_COLUMNS
        
        # Don't attempt to write characters that are off the screen.
        if row >= MDA_ROWS:
            return
            
        # Calculate the character generator attributes.
        foreground = self.palette.on
        background = self.palette.off
        if attributes & MDA_ATTR_BACKGROUND == MDA_ATTR_BACKGROUND:
            foreground = self.palette.off
            background = self.palette.on
        if attributes & MDA_ATTR_INTENSITY:
            foreground = self.palette.bright
            
        # Blit the character to the bitmap.
        self.char_generator.blit_character(self.screen, (column * self.char_generator.char_width, row * self.char_generator.char_height), character, foreground, background)
        
    def get_current_pixel(self):
        """ Returns if the current pixel is on or off and increments the pixel index. """
        if self.screen is not None:
            color = self.screen.get_at(self.current_pixel)
        else:
            color = (0, 0, 0, 0)
            
        # Update the current pixel for the next status read.
        self.current_pixel[0] += 1
        if self.current_pixel[0] >= MDA_RESOLUTION[0]:
            self.current_pixel[0] = 0
            self.current_pixel[1] += 1
            if self.current_pixel[1] >= MDA_RESOLUTION[1]:
                self.current_pixel[1] = 0
                
        return color[0:3] != MDA_BLACK
        
# Test application.
def main():
    """ Test application for the MDA card. """
    import sys
    
    print("MDA test application.")
    char_generator = CharacterGeneratorMDA_CGA_ROM(sys.argv[1], CharacterGeneratorMDA_CGA_ROM.MDA_FONT)
    
    mda = MonochromeDisplayAdapter(char_generator)
    mda.reset()
    
    # Test the font.
    for x in range(256):
        mda.mem_write_byte((x % 32) + ((x // 32) * 80) << 1, x)
        
    # Test screen width and setting attributes after setting chars.
    for x in range(80):
        mda.mem_write_byte((x << 1) + 1600, 0x30 + (x % 10))
        mda.mem_write_byte((x << 1) + 1600 + 1, 0x08 if x & 0x01 else 0x00)
        
    # Test setting attributes before setting chars.
    for x in range(5):
        mda.mem_write_byte((x << 1) + 1920 + 1, 0x08)
    for x, byte in enumerate(six.iterbytes(b"Hello world")):
        mda.mem_write_byte((x << 1) + 1920, byte)
        
    # Ensure we commit the memory to the "display".
    mda.draw()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
                
if __name__ == "__main__":
    main()
    
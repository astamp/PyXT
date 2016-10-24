"""
pyxt.cga - Color graphics adapter for PyXT based on Pygame.

For more info see here:
http://www.seasip.info/VintagePC/cga.html
http://bochs.sourceforge.net/techspec/PORTS.LST
http://webpages.charter.net/danrollins/techhelp/0066.HTM
http://webpages.charter.net/danrollins/techhelp/0089.HTM
http://www.oldskool.org/pc/cgacal
https://en.wikipedia.org/wiki/Color_Graphics_Adapter
http://www.eivanov.com/2011/01/cga-programming.html
http://nerdlypleasures.blogspot.com/2016/05/ibms-cga-hardware-explained.html
"""

from __future__ import print_function

# Standard library imports
import array
import random
from collections import namedtuple

# Six imports
import six
from six.moves import range # pylint: disable=redefined-builtin

# PyXT imports
from pyxt.bus import Device
from pyxt.chargen import CharacterGenerator

# Pygame Imports
import pygame

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants
CGA_START_ADDRESS = 0xB8000

# This is a hack until devices can be installed at non 64k boundaries.
CGA_OFFSET = 0x8000

# TODO: This will not work 640x200 graphics mode.
BASE_RESOLUTION = 320, 200
# Calculate the space for a border around the screen, the color of this can be changed in CGA.
OVERSCAN = 16
OVERSCAN_RESOLUTION = BASE_RESOLUTION[0] + (2 * OVERSCAN), BASE_RESOLUTION[1] + (2 * OVERSCAN)
# Scale up the display size for modern monitors.
DOUBLE_RESOLUTION = OVERSCAN_RESOLUTION[0] * 2, OVERSCAN_RESOLUTION[1] * 2

CGA_PORTS_START = 0x3D0
CGA_PORTS_END = 0x3DA
DATA_REG_INDEX_PORTS = (0x3D0, 0x3D2, 0x3D4, 0x3D6)
DATA_REG_ACCESS_PORTS = (0x3D1, 0x3D3, 0x3D5, 0x3D7)

CONTROL_REG_PORT = 0x3D8
CONTROL_REG_80_COLUMN =     0x01
CONTROL_REG_GRAPHICS_MODE = 0x02
CONTROL_REG_MONO =          0x04
CONTROL_REG_VIDEO_ENABLE =  0x08
CONTROL_REG_640_X_200_GFX = 0x10
CONTROL_REG_BLINK_ENABLE =  0x20

PALETTE_REG_PORT = 0x3D9
PALETTE_REG_COLOR_MASK = 0x0F
PALETTE_REG_SELECT = 0x20

STATUS_REG_PORT = 0x3DA
STATUS_REG_BASE = 0xF0
STATUS_REG_PIXEL_ON = 0x08
STATUS_REG_HORIZONTAL_RETRACE = 0x01

CGA_ATTR_FG_BLUE =   0x01
CGA_ATTR_FG_GREEN =  0x02
CGA_ATTR_FG_RED =    0x04
CGA_ATTR_FG_BRIGHT = 0x08
CGA_ATTR_BG_BLUE =   0x10
CGA_ATTR_BG_GREEN =  0x20
CGA_ATTR_BG_RED =    0x40
CGA_ATTR_BG_BRIGHT = 0x80
CGA_ATTR_FG_BLINK =  0x80 # Must be combined with CONTROL_REG_BLINK_ENABLE.

CGA_RAM_SIZE = 16 * 1024

BITS_LO_TO_HI = [7, 6, 5, 4, 3, 2, 1, 0]

CGA_COLOR_MAP = {
    0x0 : (0x00, 0x00, 0x00),
    0x1 : (0x00, 0x00, 0xA8),
    0x2 : (0x00, 0xA8, 0x00),
    0x3 : (0x00, 0xA8, 0xA8),
    0x4 : (0xA8, 0x00, 0x00),
    0x5 : (0xA8, 0x00, 0xA8),
    0x6 : (0xA8, 0x54, 0x00), # Doesn't follow pattern for compat with 3270? See cgacal link above.
    0x7 : (0xA8, 0xA8, 0xA8),
    0x8 : (0x54, 0x54, 0x54),
    0x9 : (0x54, 0x54, 0xFC),
    0xA : (0x54, 0xFC, 0x54),
    0xB : (0x54, 0xFC, 0xFC),
    0xC : (0xFC, 0x54, 0x54),
    0xD : (0xFC, 0x54, 0xFC),
    0xE : (0xFC, 0xFC, 0x54),
    0xF : (0xFC, 0xFC, 0xFC),
}

PALETTE_0_COLOR_MAP = {
    0 : CGA_COLOR_MAP[0x0],
    1 : CGA_COLOR_MAP[0x2],
    2 : CGA_COLOR_MAP[0x4],
    3 : CGA_COLOR_MAP[0x6],
}

PALETTE_1_COLOR_MAP = {
    0 : CGA_COLOR_MAP[0x0],
    1 : CGA_COLOR_MAP[0x3],
    2 : CGA_COLOR_MAP[0x5],
    3 : CGA_COLOR_MAP[0x7],
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
                
class ColorGraphicsAdapter(Device):
    def __init__(self, char_generator, randomize = False):
        super(ColorGraphicsAdapter, self).__init__()
        
        self.char_generator = char_generator
        
        self.control_reg = 0x00
        self.data_reg_index = 0x00
        
        self.video_ram = array.array("B", (0,) * CGA_RAM_SIZE)
        
        # If desired, randomize the contents of video memory at startup for effect.
        if randomize:
            for index in range(CGA_RAM_SIZE):
                self.video_ram[index] = random.randint(0, 255)
                
        # Handle to the Pygame display object.
        self.window = None # Actual window overscan res scaled up 2x.
        self.overscan = None # Intermediate video memory for prescaled image.
        self.screen = None # Actual screen area, subsurface of overscan surface.
        
        # Flag to indicate if we have updated the bitmap and need to display it.
        self.needs_draw = True
        
        # Every other call to the status register will flip the horizontal retrace bit.
        self.horizontal_retrace = False
        
        # Used to simulate the pixel on bit when the status register is being read.
        self.current_pixel = [0, 0]
        
        # Cursor parameters.
        self.cursor = Cursor()
        
        # Overscan.
        self.overscan_color = 0x00
        self.last_overscan_color = 0x00
        
        # Text mode geometry.
        self.rows = 25
        self.columns = 40
        
        # Video page support.
        self.page_offset = 0x0000
        
        # Graphics support.
        self.graphics_mode = False
        self.graphics_palette = PALETTE_0_COLOR_MAP
        
    def reset(self):
        pygame.init()
        self.window = pygame.display.set_mode(DOUBLE_RESOLUTION)
        pygame.display.set_caption("PyXT Color Graphics Adapter")
        self.overscan = pygame.Surface(OVERSCAN_RESOLUTION, pygame.SRCALPHA)
        self.screen = self.overscan.subsurface((OVERSCAN, OVERSCAN, BASE_RESOLUTION[0], BASE_RESOLUTION[1]))
        
        # Now that we have a display draw whatever is currently in RAM.
        self.redraw()
        
    def get_memory_size(self):
        return CGA_RAM_SIZE
        
    def mem_read_word(self, offset):
        # TODO: Combine this into one operation for speed.
        return (self.mem_read_byte(offset) | (self.mem_read_byte(offset + 1) << 8))
        
    def mem_read_byte(self, offset):
        # HACK: 64k boundary issue.
        offset -= CGA_OFFSET
        if offset >= CGA_RAM_SIZE or offset < 0:
            return 0x00
            
        return self.video_ram[offset]
        
    def mem_write_word(self, offset, value):
        # 0xCAFE => 0:0xFE & 1:0xCA
        # TODO: Combine this into one operation for speed.
        self.mem_write_byte(offset, value & 0x00FF)
        self.mem_write_byte(offset + 1, (value >> 8) & 0x00FF)
        
    def mem_write_byte(self, offset, value):
        # HACK: 64k boundary issue.
        offset -= CGA_OFFSET
        if offset >= CGA_RAM_SIZE or offset < 0:
            return
            
        # Direct write to the "video RAM" for reading back.
        self.video_ram[offset] = value
        
        # Reblit using the character as the base, not an attribute.
        if self.graphics_mode:
            self.draw_single_byte(offset)
        else:
            self.blit_single_char(offset & 0x1FFE)
        
        # Mark that the display bitmap is dirty and needs to be updated.
        self.needs_draw = True
        
    def get_ports_list(self):
        # range() is not inclusive so add one.
        return [x for x in range(CGA_PORTS_START, CGA_PORTS_END + 1)]
        
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
            self.graphics_mode = value & CONTROL_REG_GRAPHICS_MODE == CONTROL_REG_GRAPHICS_MODE
            
            self.control_reg = value
            
        elif port == PALETTE_REG_PORT:
            log.debug("Palette reg port 0x%03x written with 0x%02x!", port, value)
            self.overscan_color = value & PALETTE_REG_COLOR_MASK
            self.graphics_palette = PALETTE_1_COLOR_MAP if value & PALETTE_REG_SELECT else PALETTE_0_COLOR_MAP
            
    def write_crt_data_register(self, index, value):
        """ Handles writes to the 6845 CRT controller's parameters. """
        cursor = self.cursor
        
        if index == 1:
            log.debug("Character columns: %d", value)
            self.columns = value
        elif index == 6:
            log.debug("Character rows: %d", value)
            self.rows = value
        elif index == 9:
            log.debug("Character scanlines: %d", value + 1)
        elif index == 10:
            cursor.start = value & 0x1F
            cursor.set_mode(value & cursor.MODE_MASK)
        elif index == 11:
            cursor.end = value
        elif index == 12:
            self.page_offset = (self.page_offset & 0x00FF) | (value << 8)
            # HACK: For now, redraw the entire screen on page swap.
            self.redraw()
        elif index == 13:
            self.page_offset = (self.page_offset & 0xFF00) | value
            # HACK: For now, redraw the entire screen on page swap.
            self.redraw()
        elif index == 14:
            cursor.addr = (cursor.addr & 0x00FF) | (value << 8)
        elif index == 15:
            cursor.addr = (cursor.addr & 0xFF00) | value
        else:
            log.debug("Other CRT data register 0x%02x written with 0x%02x!", index, value)
        
    def draw(self):
        """ Update the "physical" display if necessary. """
        cursor = self.cursor
        
        # Do not use the hardware cursor in graphics mode.
        if not self.graphics_mode:
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
                    row = cursor.addr // self.columns
                    column = cursor.addr % self.columns
                    self.screen.fill(
                        CGA_COLOR_MAP[self.video_ram[cursor.addr + 1] & 0x0F],
                        [column * 8, (row * 8) + cursor.start, 8, (cursor.end - cursor.start) + 1],
                    )
                    
                    # Log where the cursor is located so we can erase it.
                    cursor.displayed_addr = cursor.addr
                    
                # Force a redraw and toggle the cursor active.
                self.needs_draw = True
                cursor.displayed = not cursor.displayed
            
        # Draw the overscan region if the color has changed.
        if self.overscan_color != self.last_overscan_color:
            self.last_overscan_color = self.overscan_color
            
            color = CGA_COLOR_MAP[self.overscan_color]
            self.overscan.fill(color, (0, 0, OVERSCAN_RESOLUTION[0], OVERSCAN)) # Top
            self.overscan.fill(color, (0, OVERSCAN_RESOLUTION[1] - OVERSCAN, OVERSCAN_RESOLUTION[0], OVERSCAN)) # Bottom
            self.overscan.fill(color, (0, 0, OVERSCAN, OVERSCAN_RESOLUTION[1])) # Left
            self.overscan.fill(color, (OVERSCAN_RESOLUTION[0] - OVERSCAN, 0, OVERSCAN, OVERSCAN_RESOLUTION[1])) # Right
            
            self.needs_draw = True
            
        if self.needs_draw:
            # pygame.transform.scale2x(self.overscan, self.window)
            pygame.transform.scale(self.overscan, DOUBLE_RESOLUTION, self.window)
            # pygame.transform.smoothscale(self.overscan, DOUBLE_RESOLUTION, self.window)
            pygame.display.flip()
            self.needs_draw = False
            
    def redraw(self):
        """ Does a full redraw of the display from RAM. """
        if self.graphics_mode:
            for offset in range(0, CGA_RAM_SIZE):
                self.draw_single_byte(offset)
        else:
            for offset in range(0, self.rows * self.columns * 2, 2):
                self.blit_single_char(self.page_offset + offset)
                
        self.needs_draw = True
        
    def blit_single_char(self, offset):
        """ Blits a single character to the display given the offset of the character. """
        # Get the character and attributes from RAM.
        character = self.video_ram[offset]
        attributes = self.video_ram[offset + 1]
        
        # Shift off the lowest bit to get the location base.
        offset = offset >> 1
        row = offset // self.columns
        column = offset % self.columns
        
        # Don't attempt to write characters that are off the screen.
        if row >= self.rows:
            return
            
        # Blit the character to the bitmap.
        self.char_generator.blit_character(
            self.screen,
            (column * self.char_generator.char_width, row * self.char_generator.char_height),
            character,
            CGA_COLOR_MAP[attributes & 0x0F],
            CGA_COLOR_MAP[attributes >> 4],
        )
        
    def draw_single_byte(self, offset):
        """ Draws a single byte of packed graphics to the display given the offset into video RAM. """
        byte = self.video_ram[offset]
        px0 = (byte >> 6) & 0x3
        px1 = (byte >> 4) & 0x3
        px2 = (byte >> 2) & 0x3
        px3 = byte & 0x3
        
        row = (((offset & 0x1FFF) // 80) << 1) + (1 if offset & 0x2000 == 0x2000 else 0)
        if row > 199:
            return
            
        column = ((offset & 0x1FFF) % 80) * 4
        
        # TODO: There must be a faster way to do this.
        self.screen.set_at((column, row), self.graphics_palette[px0])
        self.screen.set_at((column + 1, row), self.graphics_palette[px1])
        self.screen.set_at((column + 2, row), self.graphics_palette[px2])
        self.screen.set_at((column + 3, row), self.graphics_palette[px3])
        
    def get_current_pixel(self):
        """ Returns if the current pixel is on or off and increments the pixel index. """
        if self.screen is not None:
            color = self.screen.get_at(self.current_pixel)
        else:
            color = (0, 0, 0, 0)
            
        # Update the current pixel for the next status read.
        self.current_pixel[0] += 1
        if self.current_pixel[0] >= BASE_RESOLUTION[0]:
            self.current_pixel[0] = 0
            self.current_pixel[1] += 1
            if self.current_pixel[1] >= BASE_RESOLUTION[1]:
                self.current_pixel[1] = 0
                
        return color[0:3] != (0, 0, 0)
        
class CharacterGeneratorCGA(CharacterGenerator):
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
        self.working_char = pygame.Surface((self.font_info.cols_actual, self.font_info.rows_actual), pygame.SRCALPHA)
        
        self.font_data_alpha = pygame.Surface((self.font_info.cols_actual * self.CHAR_COUNT, self.font_info.rows_actual), pygame.SRCALPHA)
        
        pix_alpha = pygame.PixelArray(self.font_data_alpha)
        
        # The characters are split top and bottom across the first 2 2k pages of the part.
        with open(rom_file, "rb") as fileptr:
            fileptr.seek(self.font_info.start_address)
            upper_half = fileptr.read(self.PAGE_SIZE)
            lower_half = fileptr.read(self.PAGE_SIZE)
            
        for index in range(self.CHAR_COUNT):
            for row in range(0, self.font_info.rows_actual):
                if row < 8:
                    byte = six.indexbytes(upper_half, (index * 8) + row)
                else:
                    byte = six.indexbytes(lower_half, (index  * 8) + (row - 8))
                    
                for bit in BITS_LO_TO_HI:
                    if (1 << bit) & byte:
                        pix_alpha[(index * self.char_width) + (7 - bit), row] = (255, 255, 255, 255)
                        
        # Make sure to explicitly del this to free the surface lock.
        del pix_alpha
        
    def blit_character(self, surface, location, index, foreground, background):
        """ Place a character onto a surface at the given location. """
        if index >= self.CHAR_COUNT:
            return
            
        surface.fill(background, (location[0], location[1], self.char_width, self.char_height))
        self.working_char.fill(foreground)
        self.working_char.blit(self.font_data_alpha, (0, 0), (self.char_width * index, 0, self.char_width, self.char_height), pygame.BLEND_RGBA_MULT)
        surface.blit(self.working_char, location)
        
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
    """ Test application for the CGA card. """
    import sys
    
    print("CGA test application.")
    char_generator = CharacterGeneratorCGA(sys.argv[1], CharacterGeneratorCGA.CGA_WIDE_FONT)
    
    cga = ColorGraphicsAdapter(char_generator)
    cga.reset()
    
    pygame.key.set_repeat(250, 25)
    overscan_color = 0x00
    cursor = CGA_OFFSET
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_KP_PLUS:
                    overscan_color = (overscan_color + 1) & 0x0F
                    print("overscan_color = 0x%x" % overscan_color)
                    cga.io_write_byte(PALETTE_REG_PORT, overscan_color)
                    cga.draw()
                elif event.key == pygame.K_KP_MULTIPLY:
                    cga.io_write_byte(CONTROL_REG_PORT, CONTROL_REG_GRAPHICS_MODE)
                    cga.mem_write_byte(CGA_OFFSET + 0, 0xA5)
                    cga.mem_write_byte(CGA_OFFSET + 8192, 0x5A)
                    cga.draw()
                elif len(event.unicode) > 0:
                    byte = six.byte2int(event.unicode.encode("utf-8"))
                    cga.mem_write_byte(cursor, byte)
                    cga.mem_write_byte(cursor + 1, random.randint(1, 0x0F))
                    cursor += 2
                    cga.draw()
                    
            elif event.type == pygame.QUIT:
                sys.exit()
                
if __name__ == "__main__":
    main()
    
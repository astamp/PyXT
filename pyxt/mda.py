"""
pyxt.mda - Monochrome display adapter for PyXT based on Pygame.
"""

# Standard library imports
import array

# PyXT imports
from pyxt.bus import Device
from pyxt.helpers import *
from pyxt.constants import *

# Pygame Imports
import pygame
from pygame.locals import *

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

ATTR_FOREGROUND = 0x07
ATTR_INTENSITY = 0x08
ATTR_BACKGROUND = 0x70
ATTR_BLINK = 0x80

ATTR_UNDERLINE = 0x01

CHAR_WIDTH = 9
CHAR_HEIGHT = 14

# Classes
class MonochromeDisplayAdapter(Device):
    def __init__(self):
        super(MonochromeDisplayAdapter, self).__init__()
        
        self.control_reg = 0x00
        self.data_reg_index = 0x00
        
        self.screen = None
        self.reset()
        
    def reset(self):
        pygame.init()
        self.screen = pygame.display.set_mode(MDA_RESOLUTION)
        pygame.display.set_caption("PyXT Monochrome Display Adapter")
        
    def mem_write_byte(self, offset, value):
        pass
        
    def get_ports_list(self):
        # range() is not inclusive so add one.
        return [x for x in xrange(MDA_PORTS_START, MDA_PORTS_END + 1)]
        
    def io_read_byte(self, port):
        if port in DATA_REG_ACCESS_PORTS:
            return self.read_crt_data_register(self.data_reg_index)
            
        elif port == CONTROL_REG_PORT:
            return self.control_reg
            
        else:
            return 0x00
            
    def io_write_byte(self, port, value):
        if port in DATA_REG_INDEX_PORTS:
            self.data_reg_index = value
            
        elif port in DATA_REG_ACCESS_PORTS:
            self.write_crt_data_register(self.data_reg_index, value)
            
        elif port == CONTROL_REG_PORT:
            self.control_reg = value
            
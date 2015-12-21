"""
pyxt.mda - Monochrome display adapter for PyXT.
"""

# Standard library imports
import array

# PyXT imports
from pyxt.bus import Device
from pyxt.helpers import *
from pyxt.constants import *

# Pyglet importrs
import pyglet

# Constants
MDA_PORTS_START = 0x3B0
MDA_PORTS_END = 0x3BB # Don't include the parallel port on the MDA card.
CONTROL_REG_PORT = 0x3B8
DATA_REG_INDEX_PORTS = (0x3B0, 0x3B2, 0x3B4, 0x3B6)
DATA_REG_ACCESS_PORTS = (0x3B1, 0x3B3, 0x3B5, 0x3B7)

# Classes
class MonochromeDisplayAdapter(Device):
    def __init__(self):
        super(MonochromeDisplayAdapter, self).__init__()
        
        self.control_reg = 0x00
        self.data_reg_index = 0x00
        
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
            
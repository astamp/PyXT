"""
pyxt.memory - Memory devices for PyXT.
"""

# Standard library imports
import array

# PyXT imports
from pyxt.helpers import *
from pyxt.constants import *
from pyxt.bus import Device

# Classes
class RAM(Device):
    """ A device emulating a RAM storage device. """
    def __init__(self, size, **kwargs):
        super(RAM, self).__init__(**kwargs)
        self.contents = array.array("B", (0,) * size)
        
    def __repr__(self):
        return "<%s(size=0x%x)>" % (self.__class__.__name__, len(self.contents))
        
    def mem_read_byte(self, offset):
        return self.contents[offset]
        
    def mem_read_word(self, offset):
        return bytes_to_word((self.contents[offset], self.contents[offset + 1]))
        
    def mem_write_byte(self, offset, value):
        self.contents[offset] = value
        
    def mem_write_word(self, offset, value):
        self.contents[offset], self.contents[offset + 1] = word_to_bytes(value)
        
class ROM(RAM):
    """ A device emulating a ROM storage device. """
    def __init__(self, size, init_file = None, **kwargs):
        super(ROM, self).__init__(size, **kwargs)
        if init_file is not None:
            self.load_from_file(init_file)
            
    def load_from_file(self, filename, offset = 0):
        with open(filename, "rb") as fileptr:
            data = fileptr.read()
            
        for index, char in enumerate(data, start = offset):
            self.contents[index] = ord(char)
            
    def mem_write_byte(self, offset, value):
        pass
        
    def mem_write_word(self, offset, value):
        pass
        
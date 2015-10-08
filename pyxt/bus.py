"""
pyxt.bus - System bus and component interface for PyXT.
"""

# Standard library imports
import array

# PyXT imports
from pyxt.helpers import *

# Constants
DEVICE_PREFIX = 0xF8000

# Classes
class BusComponent(object):
    def __init__(self, bus = None):
        self.bus = bus
        
    def read_byte(self, offset):
        """ Read a byte from the device at offset. """
        raise NotImplementedError
        
    def read_word(self, offset):
        """ Read a word from the device at offset. """
        raise NotImplementedError
        
    def write_byte(self, offset, value):
        """ Write a byte value to the device at offset. """
        raise NotImplementedError
        
    def write_word(self, offset):
        """ Write a word value to the device at offset. """
        raise NotImplementedError
        
class RAM(BusComponent):
    """ A BusComponent emulating a RAM storage device. """
    def __init__(self, size, **kwargs):
        super(RAM, self).__init__(**kwargs)
        self.contents = array.array("B", (0,) * size)
        
    def read_byte(self, offset):
        return self.contents[offset]
        
    def read_word(self, offset):
        return bytes_to_word((self.contents[offset], self.contents[offset + 1]))
        
    def write_byte(self, offset, value):
        self.contents[offset] = value
        
    def write_word(self, offset, value):
        self.contents[offset], self.contents[offset + 1] = word_to_bytes(value)
        
class ROM(RAM):
    """ A BusComponent emulating a ROM storage device. """
    def __init__(self, size, init_file = None, **kwargs):
        super(ROM, self).__init__(size, **kwargs)
        if init_file is not None:
            self.load_from_file(init_file)
            
    def load_from_file(self, filename, offset = 0):
        with open(filename, "rb") as fileptr:
            data = fileptr.read()
            
        for index, char in enumerate(data, start = offset):
            self.contents[index] = ord(char)
            
    def write_byte(self, offset, value):
        pass
        
    def write_word(self, offset, value):
        pass
        
class SystemBus(object):
    def __init__(self):
        # Array of devices by 5 bit prefix.
        self.devices = [None] * 32
        print self.devices
        
    def add_device(self, prefix, device_cls, *args, **kwargs):
        device = device_cls(bus = self, *args, **kwargs)
        print prefix >> 15
        self.devices[prefix >> 15] = device
        print self.devices
        return device
        
    def read_byte(self, address):
        device = self.devices[address >> 15]
        if device is not None:
            return device.read_byte(address)
        else:
            return 0
            
        
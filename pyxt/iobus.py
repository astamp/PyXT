"""
pyxt.iobus - I/O bus and component interface for PyXT.
"""

# Standard library imports
import array

# PyXT imports
from pyxt.helpers import *
from pyxt.constants import *

# Classes
class IOComponent(object):
    def __init__(self):
        self.io_bus = None
        
    def get_address_list(self):
        """ Return a list of addresses used by the device. """
        raise NotImplementedError
        
    def clock(self):
        """ Handle one iteration of the system clock tick. """
        pass
        
    def read_byte(self, address):
        """ Read a byte from the device at address. """
        raise NotImplementedError
        
    def read_word(self, address):
        """ Read a word from the device at address. """
        raise NotImplementedError
        
    def write_byte(self, address, value):
        """ Write a byte value to the device at address. """
        raise NotImplementedError
        
    def write_word(self, address):
        """ Write a word value to the device at address. """
        raise NotImplementedError
        
class ProgrammableInterruptController(IOComponent):
    """ An IOComponent emulating an 8259 PIC controller. """
    def __init__(self, base, **kwargs):
        super(ProgrammableInterruptController, self).__init__(**kwargs)
        self.base = base
        self.mask = 0x00
        
    def get_address_list(self):
        return [x for x in xrange(self.base, self.base + 2)]
        
    def read_byte(self, address):
        offset = address - self.base
        if offset == 0 or offset == 1 or offset == 2:
            return self.channels[offset]
        elif offset == 3:
            print "CONTROL REGISTER"
        else:
            raise ValueError("Bad offset to the 8253!!!")
            
    def write_byte(self, address, value):
        offset = address - self.base
        if offset == 0:
            print "CONTROL REGISTER", value
        elif offset == 1:
            print "DATA REGISTER", value
        else:
            raise ValueError("Bad offset to the 8259!!!")
            
class ProgrammableIntervalTimer(IOComponent):
    """ An IOComponent emulating an 8253 PIT timer. """
    def __init__(self, base, **kwargs):
        super(ProgrammableIntervalTimer, self).__init__(**kwargs)
        self.base = base
        self.channels = [0, 0, 0]
        
    def get_address_list(self):
        return [x for x in xrange(self.base, self.base + 8)]
        
    def read_byte(self, address):
        offset = address - self.base
        if offset == 0 or offset == 1 or offset == 2:
            return self.channels[offset]
        elif offset == 3:
            print "CONTROL REGISTER"
        else:
            raise ValueError("Bad offset to the 8253!!!")
            
        
class InputOutputBus(object):
    def __init__(self):
        self.devices = []
        self.decoder = {}
        
    def install_device(self, device):
        device.io_bus = self
        self.devices.append(device)
        for address in device.get_address_list():
            self.decoder[address] = device
            
    def read_byte(self, address):
        device = self.decoder.get(address, None)
        if device is not None:
            return device.read_byte(address)
        else:
            return 0
            
    # def read_word(self, address):
        # device = self.devices[address >> BLOCK_PREFIX_SHIFT]
        # if device is not None:
            # return device.read_word(address & BLOCK_OFFSET_MASK)
        # else:
            # return 0
            
    def write_byte(self, address, value):
        device = self.decoder.get(address, None)
        if device is not None:
            device.write_byte(address, value)
            
    # def write_word(self, address, value):
        # device = self.devices[address >> BLOCK_PREFIX_SHIFT]
        # if device is not None:
            # device.write_word(address & BLOCK_OFFSET_MASK, value)
            
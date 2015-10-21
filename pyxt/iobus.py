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
        """
        Handle one iteration of the system clock tick.
        
        This is not required to be implemented as not all devices have a clock input.
        """
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
    EDGE_TRIGGERED = 0
    LEVEL_TRIGGERED = 1
    
    def __init__(self, base, **kwargs):
        super(ProgrammableInterruptController, self).__init__(**kwargs)
        self.base = base
        
        # Configuration "registers".
        self.cascade = False
        self.mask = 0x00
        self.trigger_mode = self.EDGE_TRIGGERED
        self.priorities = [0, 1, 2, 3, 4, 5, 6, 7]
        self.vector_base = 0x00
        self.i8086_8088_mode = False
        self.auto_eoi = False
        
        # ICWS (Initialization Commands Words) state machine, per the datasheet.
        # 0 indicates the idle state, 1-4 indicate what byte will be processed next.
        self.icws_state = 0
        self.icw4_needed = False
        
    def get_address_list(self):
        return [x for x in xrange(self.base, self.base + 2)]
        
    def start_initialization_sequence(self):
        self.mask = 0x00
        self.trigger_mode = self.EDGE_TRIGGERED
        self.priorities[7] = 7
        self.icws_state = 1
        self.icw4_needed = False
        
    def process_icws_byte(self, value):
        if self.icws_state == 1:
            self.icw4_needed = value & 0x01 == 0x01
            self.cascade = value & 0x02 == 0x02
            self.trigger_mode = self.LEVEL_TRIGGERED if value & 0x04 == 0x04 else self.EDGE_TRIGGERED
            
            if not self.icw4_needed:
                self.i8086_8088_mode = False
                self.auto_eoi = False
                
            self.icws_state = 2
            
        elif self.icws_state == 2:
            self.vector_base = value & 0xF1
            
            if self.cascade:
                self.icws_state = 3
            elif self.icw4_needed:
                self.icws_state = 4
            else:
                self.icws_state = 0
                
        elif self.icws_state == 3:
            # TODO: Something with this byte maybe?!
            if self.icw4_needed:
                self.icws_state = 4
            else:
                self.icws_state = 0
                
        elif self.icws_state == 4:
            self.i8086_8088_mode = value & 0x01 == 0x01
            self.auto_eoi = value & 0x02 == 0x02
            
            self.icws_state = 0
            
    def process_ocw2_byte(self, value):
        command = (value & 0xE0) >> 5
        interrupt = value & 0x07
        print "command = %r, interrupt = %r" % (command, interrupt)
        
    # def read_byte(self, address):
        # offset = address - self.base
        # if offset == 0 or offset == 1 or offset == 2:
            # return self.channels[offset]
        # elif offset == 3:
            # print "CONTROL REGISTER"
        # else:
            # raise ValueError("Bad offset to the 8253!!!")
            
    def write_byte(self, address, value):
        offset = address - self.base
        if offset == 0 and value & 0x10 == 0x10:
            self.start_initialization_sequence()
        # elif offset == 1:
            # print "DATA REGISTER", value
        # else:
            # raise ValueError("Bad offset to the 8259!!!")
        
        if self.icws_state > 0:
            self.process_icws_byte(value)
        else:
            if offset == 1:
                self.mask = value
            else:
                if value & 0x08 == 0x08:
                    self.process_ocw3_byte(value)
                else:
                    self.process_ocw2_byte(value)
                    
            
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
            
"""
pyxt.bus - System bus and component interface for PyXT.
"""

# Standard library imports

# PyXT imports
from pyxt.constants import BLOCK_PREFIX_SHIFT, BLOCK_OFFSET_MASK

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Classes
class Device(object):
    """ Base class for a devuce on the system bus. """
    def __init__(self):
        self.bus = None
        
    # Common stuff.
    def install(self, bus):
        """ Install this device into the supplied system bus. """
        self.bus = bus
        
    def reset(self):
        """ Called to reset the device at the beginning of time. """
        pass
        
    def clock(self):
        """
        Handle one iteration of the system clock tick.
        
        This is not required to be implemented as not all devices have a clock input.
        """
        pass
        
    # Memory bus.
    def get_memory_size(self): # pylint: disable=no-self-use
        """ Return the length of the memory mapped area of this device. """
        return 0
        
    def mem_read_byte(self, offset):
        """ Read a byte from memory at the supplied offset from the device's base. """
        raise NotImplementedError("This device doesn't support memory mapping.")
        
    def mem_read_word(self, offset):
        """ Read a word from memory at the supplied offset from the device's base. """
        raise NotImplementedError("This device doesn't support memory mapping.")
        
    def mem_write_byte(self, offset, value):
        """ Write a byte to memory at the supplied offset from the device's base. """
        raise NotImplementedError("This device doesn't support memory mapping.")
        
    def mem_write_word(self, offset, value):
        """ Write a word to memory at the supplied offset from the device's base. """
        raise NotImplementedError("This device doesn't support memory mapping.")
        
    # I/O bus.
    def get_ports_list(self): # pylint: disable=no-self-use
        """ Return a list of ports used by this device. """
        return []
        
    def io_read_byte(self, port):
        """ Read a byte from the supplied port. """
        raise NotImplementedError("This device doesn't support I/O ports.")
        
    def io_read_word(self, port):
        """ Read a word from the supplied port. """
        raise NotImplementedError("This device doesn't support I/O ports.")
        
    def io_write_byte(self, port, value):
        """ Write a byte to the supplied port. """
        raise NotImplementedError("This device doesn't support I/O ports.")
        
    def io_write_word(self, port, value):
        """ Write a word to the supplied port. """
        raise NotImplementedError("This device doesn't support I/O ports.")
        
class SystemBus(object):
    """ The main system bus for PyXT including memory mapped devices and I/O ports. """
    def __init__(self, pic = None, dma = None):
        # Array of memory blocks indexed by 4 bit prefix.
        self.devices = [None] * 16
        
        self.io_devices = []
        self.io_decoder = {}
        
        self.debugger = None
        
        self.pic = pic
        self.dma = dma
        
    def install_device(self, prefix, device):
        """ Install a device into the system bus. """
        device.bus = self
        
        # The memory bus uses a prefix to index to the correct device.
        if prefix is not None:
            self.devices[prefix >> BLOCK_PREFIX_SHIFT] = device
            
        # The I/O bus uses a decoder (dictionary in our case).
        if len(device.get_ports_list()) > 0:
            self.io_devices.append(device)
            for address in device.get_ports_list():
                self.io_decoder[address] = device
                
    def mem_read_byte(self, address):
        """ Read a byte from the supplied physical memory address. """
        device = self.devices[address >> BLOCK_PREFIX_SHIFT]
        if device is not None:
            return device.mem_read_byte(address & BLOCK_OFFSET_MASK)
        else:
            return 0
            
    def mem_read_word(self, address):
        """ Read a word from the supplied physical memory address. """
        device = self.devices[address >> BLOCK_PREFIX_SHIFT]
        if device is not None:
            return device.mem_read_word(address & BLOCK_OFFSET_MASK)
        else:
            return 0
            
    def mem_write_byte(self, address, value):
        """ Write a byte to the supplied physical memory address. """
        device = self.devices[address >> BLOCK_PREFIX_SHIFT]
        if device is not None:
            device.mem_write_byte(address & BLOCK_OFFSET_MASK, value)
            
    def mem_write_word(self, address, value):
        """ Write a word to the supplied physical memory address. """
        device = self.devices[address >> BLOCK_PREFIX_SHIFT]
        if device is not None:
            device.mem_write_word(address & BLOCK_OFFSET_MASK, value)
            
            
    def io_read_byte(self, port):
        """ Read a byte from the supplied port. """
        device = self.io_decoder.get(port, None)
        if device is not None:
            return device.io_read_byte(port)
        else:
            log.warning("No handler for reading I/O port: 0x%03x, returning 0x00.", port)
            return 0x00
            
    def io_read_word(self, port):
        """ Read a word from the supplied port. """
        raise NotImplementedError("TODO: Support words on the I/O bus.")
        
    def io_write_byte(self, port, value):
        """ Write a byte to the supplied port. """
        device = self.io_decoder.get(port, None)
        if device is not None:
            device.io_write_byte(port, value)
        else:
            log.warning("No handler for writing I/O port: 0x%03x. Tried to write 0x%02x", port, value)
            
    def io_write_word(self, port, value):
        """ Write a word to the supplied port. """
        raise NotImplementedError("TODO: Support words on the I/O bus.")
        
    def force_debugger_break(self, message = None):
        """ Force the debugger to break into single step mode. """
        if self.debugger is not None:
            if message:
                log.critical("Force break: %s", message)
                
            self.debugger.single_step = True
            
    def interrupt_request(self, irq):
        """ Signals the appropriate IRQ on the interrupt controller. """
        # First, and only, interrupt controller on the XT.
        if self.pic and 0 <= irq <= 7:
            self.pic.interrupt_request(irq)
            
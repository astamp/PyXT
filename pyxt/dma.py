"""
pyxt.dma - Virtual DMA controller for PyXT.
"""

# Standard library imports

# Six imports
from six.moves import range # pylint: disable=redefined-builtin

# PyXT imports
from pyxt.bus import Device

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants
STATE_SI = 0
STATE_S0 = 1
STATE_S1 = 2
STATE_S2 = 3
STATE_S3 = 4
STATE_S4 = 5
STATE_SW = 6
STATE_S11 = 7
STATE_S12 = 8
STATE_S13 = 9
STATE_S14 = 10
STATE_S21 = 11
STATE_S22 = 12
STATE_S23 = 13
STATE_S24 = 14

# Functions
def write_low(word, byte):
    """ Writes byte into the low portion of word. """
    return (word & 0xFF00) | (byte & 0xFF)
    
def write_high(word, byte):
    """ Writes byte into the high portion of word. """
    return (word & 0x00FF) | ((byte & 0xFF) << 8)
    
def read_low(word):
    """ Reads the low portion of word. """
    return word & 0x00FF
    
def read_high(word):
    """ Reads the high portion of word. """
    return (word >> 8) & 0x00FF
    
# Classes
class DmaChannel(object):
    """ Holds info about DMA channel configuration. """
    def __init__(self):
        self.address = 0x0000
        self.word_count = 0x0000
        self.base_address = 0x0000
        self.base_word_count = 0x0000
        self.mode = 0x00
        
class DmaController(Device):
    """ A Device emulating an 8237 DMA controller. """
    
    def __init__(self, base, **kwargs):
        super(DmaController, self).__init__(**kwargs)
        self.base = base
        self.state = STATE_SI
        self.low_byte = True
        self.channels = [DmaChannel() for _unused in range(4)]
        
    def get_ports_list(self):
        return [x for x in range(self.base, self.base + 16)]
        
    def clock(self):
        pass
        
    def write_low_high(self, word, value):
        if self.low_byte:
            self.low_byte = False
            return write_low(word, value)
        else:
            self.low_byte = True
            return write_high(word, value)
            
    def read_low_high(self, word):
        if self.low_byte:
            self.low_byte = False
            return read_low(word)
        else:
            self.low_byte = True
            return read_high(word)
            
    def io_read_byte(self, port):
        offset = port - self.base
        if offset & 0x08:
            return 0x00
            
        else:
            # Which DMA channel?
            channel = offset >> 1
            
            # Odd values are word count.
            if offset & 0x01:
                return self.read_low_high(self.channels[channel].word_count)
            else:
                return self.read_low_high(self.channels[channel].address)
                
    def io_write_byte(self, port, value):
        offset = port - self.base
        if offset & 0x08:
            pass
            
        else:
            # Which DMA channel?
            channel = offset >> 1
            
            # Odd values are word count.
            if offset & 0x01:
                self.channels[channel].word_count = self.channels[channel].base_word_count = self.write_low_high(self.channels[channel].word_count, value)
            else:
                self.channels[channel].address = self.channels[channel].base_address = self.write_low_high(self.channels[channel].address, value)
                
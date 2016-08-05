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

# Mode register fields.
CHANNEL_MASK = 0x03

TYPE_MASK = 0x0C
TYPE_VERIFY = 0x00
TYPE_WRITE = 0x04
TYPE_READ = 0x08

AUTOINIT_ENABLE = 0x10
ADDRESS_DECREMENT = 0x20

MODE_MASK = 0xC0
MODE_DEMAND = 0x00
MODE_SINGLE = 0x40
MODE_BLOCK = 0x80
MODE_CASCADE = 0xC0

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
        
        self.mode = MODE_DEMAND
        self.auto_init = False
        self.increment = 1
        self.transfer_type = TYPE_VERIFY
        
        self.requested = False
        self.masked = True
        
        self.port = 0
        self.page_register_port = 0x000
        self.page_register_value = 0x0000
        self.terminal_count_callback = None
        
class DmaController(Device):
    """ A Device emulating an 8237 DMA controller. """
    
    def __init__(self, base, page_register_map, **kwargs):
        super(DmaController, self).__init__(**kwargs)
        self.base = base
        self.state = STATE_SI
        self.low_byte = True
        self.enable = False
        
        # Configuration information for each DMA channel.
        self.channels = [DmaChannel() for _unused in range(4)]
        
        # Create a dictionary lookup for the correct channel for each page register.
        if len(page_register_map) != 4:
            raise ValueError("Page register map length does not match number of channels!")
            
        self.page_register_channel_lookup = {}
        for index, page_register in enumerate(page_register_map):
            self.channels[index].page_register_port = page_register
            self.page_register_channel_lookup[page_register] = self.channels[index]
            
    # Device interface.
    def get_ports_list(self):
        return [x for x in range(self.base, self.base + 16)] + [channel.page_register_port for channel in self.channels]
        
    def clock(self):
        if self.enable:
            for channel in self.channels:
                if channel.requested:
                    # Prefix the address with the page register (not like segment+offset though).
                    full_address = (channel.page_register_value << 16) | channel.address
                    
                    if channel.transfer_type == TYPE_WRITE:
                        self.bus.mem_write_byte(full_address, self.bus.io_read_byte(channel.port))
                        
                    channel.word_count = (channel.word_count - 1) & 0xFFFF
                    channel.address += channel.increment
                    
                    if channel.word_count == 0xFFFF:
                        channel.requested = False
                        if callable(channel.terminal_count_callback):
                            channel.terminal_count_callback()
                            
    def io_read_byte(self, port):
        # If it was a page register read, do that and get out.
        if port in self.page_register_channel_lookup:
            return self.page_register_channel_lookup[port].page_register_value
            
        offset = port - self.base
        
        # Read from the DMA address and word count registers.
        if offset & 0x08 == 0x00:
            # Which DMA channel?
            channel = offset >> 1
            
            # Odd values are word count.
            if offset & 0x01:
                return self.read_low_high(self.channels[channel].word_count)
            else:
                return self.read_low_high(self.channels[channel].address)
                
        # Read the status register.
        elif offset == 0x08:
            value = 0x00
            for index, channel in enumerate(self.channels):
                if channel.requested:
                    value |= (0x10 << index)
                if channel.word_count == 0xFFFF:
                    value |= (0x01 << index)
            return value
            
        else:
            raise NotImplementedError("offset = 0x%02x" % offset)
            
    def io_write_byte(self, port, value):
        # If it was a page register write, do that and get out.
        if port in self.page_register_channel_lookup:
            self.page_register_channel_lookup[port].page_register_value = value
            return
            
        offset = port - self.base
        # print "offset = 0x%02x, value = 0x%02x" % (offset, value)
        
        # Write to the DMA address and word count registers.
        if offset & 0x08 == 0x00:
            # Which DMA channel?
            channel = offset >> 1
            
            # Odd values are word count.
            if offset & 0x01:
                self.channels[channel].word_count = self.channels[channel].base_word_count = self.write_low_high(self.channels[channel].word_count, value)
            else:
                self.channels[channel].address = self.channels[channel].base_address = self.write_low_high(self.channels[channel].address, value)
                
        # Write the command register.
        elif offset == 0x08:
            self.enable = value & 0x04 == 0x00
            
        # Write a single mask bit.
        elif offset == 0x0A:
            channel = self.channels[value & CHANNEL_MASK]
            channel.masked = value & 0x04 == 0x04
            
        # Write mode register.
        elif offset == 0x0B:
            channel = self.channels[value & CHANNEL_MASK]
            channel.mode = value & MODE_MASK
            channel.transfer_type = value & TYPE_MASK
            channel.auto_init = value & AUTOINIT_ENABLE == AUTOINIT_ENABLE
            channel.increment = -1 if value & ADDRESS_DECREMENT == ADDRESS_DECREMENT else 1
            
        # Clear low/high flip-flop.
        elif offset == 0x0C:
            self.low_byte = True
            
        # Master clear.
        elif offset == 0x0D:
            self.low_byte = True
            self.enable = False
            self.state = STATE_SI
            for channel in self.channels:
                channel.requested = False
                channel.masked = True
                
        # Write all mask bits.
        elif offset == 0x0F:
            for index, channel in enumerate(self.channels):
                channel.masked = bool(value & (0x01 << index))
                
        else:
            raise NotImplementedError("offset = 0x%02x" % offset)
            
    # Local functions.
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
            
    def print_dma_stats(self):
        for index, channel in enumerate(self.channels):
            print(self.enable, index, channel.word_count, channel.address)
            
    def dma_request(self, channel, port, terminal_count_callback = None):
        """ Signal from the bus to indicate that DMA service has been requested for a given channel and I/O port """
        self.channels[channel].requested = True
        # HACK: How does the real hardware know what port to use?!
        self.channels[channel].port = port
        # TODO: Proper DREQ/DACK handshaking.
        self.channels[channel].terminal_count_callback = terminal_count_callback
        
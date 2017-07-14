"""
pyxt.timer - Programmable interval timer for PyXT.
"""

# Standard library imports

# Six imports
from six.moves import range # pylint: disable=redefined-builtin

# PyXT imports
from pyxt.bus import Device
from pyxt.speaker import GLOBAL_SPEAKER

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants
PIT_COMMAND_LATCH = 0x00
PIT_READ_WRITE_NONE = 0x00
PIT_READ_WRITE_LOW = 0x01
PIT_READ_WRITE_HIGH = 0x02
PIT_READ_WRITE_BOTH = 0x03

TIMER_IRQ_LINE = 0

# Classes
class Counter(object):
    """ Class containing the configuration for a single PIT channel. """
    def __init__(self, output_changed_callback = None):
        self.output_changed_callback = output_changed_callback
        
        self.count = 0
        self.value = 0
        self.latched_value = None
        self.mode = 0
        self.enabled = False
        
        self.read_write_mode = PIT_READ_WRITE_NONE
        self.low_byte = True
        self.__output = False
        self.__gate = False
        self.gate = False
        
    @property
    def gate(self):
        """ Returns the current gate value. """
        return self.__gate
        
    @gate.setter
    def gate(self, value):
        """ Sets the gate value. """
        self.__gate = value
        
        if self.mode == 2 or self.mode == 3:
            if value:
                self.value = self.count
                self.enabled = True
            else:
                self.enabled = False
                self.output = True
                
    @property
    def output(self):
        """ Returns the current output pin state. """
        return self.__output
        
    @output.setter
    def output(self, value):
        """ Sets the output pin value and calls the callback. """
        if self.__output != value:
            self.__output = value
            if callable(self.output_changed_callback):
                self.output_changed_callback(self.__output)
            
    def clock(self, cycles):
        """ Handle the clock input to the channel. """
        if not self.enabled:
            return
            
        if self.mode == 0:
            if self.gate:
                last_value = self.value
                self.value = (self.value - cycles) & 0xFFFF
                
                if self.value == 0 or self.value > last_value:
                    self.output = True
                    
        elif self.mode == 2:
            last_value = self.value
            self.value = self.value - cycles
            
            # If we crossed one, pulse the output low for one "cycle".
            if self.value == 1 or (last_value > 1 and self.value < 1):
                self.output = False
                
            # If we crossed zero, set the output back high and reset the counter.
            if self.value < 1:
                # TODO: What if the leftover cycles crosses another expiration?
                self.value = (self.count + self.value) & 0xFFFF # Add any negative to the next round.
                self.output = True
                
        elif self.mode == 3:
            while cycles:
                last_value = self.value
                
                # First, deal with an odd value, this should be rare (only on reload).
                if self.value & 0x0001:
                    if self.output:
                        self.value = self.value - 1
                    else:
                        self.value = self.value - 3
                        
                    cycles -= 1
                    
                # HACK: Handle the special case of a zero count (i.e. a count of 0x10000).
                elif self.count == 0 and self.value == 0:
                    self.value = 0xFFFE
                    cycles -= 1
                    
                # Otherwise we are in the main decrement (even).
                else:
                    # Determine if we can use all of the cycles or need to process the reload.
                    cycle_allowance = min(cycles, self.value >> 1)
                    assert cycle_allowance > 0, "Timer is bankrupt!"
                    self.value = self.value - (cycle_allowance << 1)
                    cycles -= cycle_allowance
                    
                # Do the normal zero processing.
                if self.value == 0:
                    self.output = not self.output
                    self.value = self.count
                    
        else:
            raise NotImplementedError("Timer mode %d not supported!" % self.mode)
            
        assert self.value >= 0, ("Timer value fell into a bottomless pit! (mode=%d, count=%d, value=%d, output=%r" % (self.mode, self.count, self.value, self.output))
        
    def latch(self):
        """ Latch the running counter into the holding register. """
        self.latched_value = self.value
        
    def reconfigure(self, command, mode, bcd):
        """ Reconfigure this PIT channel. """
        assert bcd == 0, "BCD mode is not supported."
        assert command != 0, "Command 0x00 should have latched the value!"
        self.mode = mode
        
        self.read_write_mode = command
        if self.read_write_mode == PIT_READ_WRITE_BOTH:
            self.low_byte = True
        
        if self.mode == 0:
            self.output = False
            self.value = self.count
            
        elif self.mode == 2 or self.mode == 3:
            # TODO: If you are gated during reconfigure should that take effect immediately?
            pass
            
        else:
            raise NotImplementedError("Mode %d is not currently supported!" % self.mode)
            
    def get_read_value(self):
        """ Return the value for a read operation. """
        if self.latched_value is not None:
            return self.latched_value
        else:
            return self.value
            
    def read(self):
        """ Read a byte from this counter. """
        value = self.get_read_value()
        
        if self.read_write_mode == PIT_READ_WRITE_LOW:
            return value & 0xFF
            
        elif self.read_write_mode == PIT_READ_WRITE_HIGH:
            return (value >> 8) & 0xFF
            
        elif self.read_write_mode == PIT_READ_WRITE_BOTH:
            if self.low_byte:
                self.low_byte = False
                return value & 0xFF
            else:
                self.low_byte = True
                self.latched_value = None
                return (value >> 8) & 0xFF
                
        else:
            raise RuntimeError("Invalid PIT channel r/w mode: %r", self.read_write_mode)
            
    def write(self, value):
        """ Write a byte to this counter. """
        if self.read_write_mode == PIT_READ_WRITE_LOW:
            self.count = value
            if self.mode == 0:
                self.enabled = True
                self.value = self.count
            elif self.mode == 2 or self.mode == 3:
                self.enabled = True
            
        elif self.read_write_mode == PIT_READ_WRITE_HIGH:
            self.count = value << 8
            if self.mode == 0:
                self.enabled = True
                self.value = self.count
            elif self.mode == 2 or self.mode == 3:
                self.enabled = True
                self.value = self.count
            
        elif self.read_write_mode == PIT_READ_WRITE_BOTH:
            if self.low_byte:
                if self.mode == 0: # Do not disable here for mode 2 or 3.
                    self.enabled = False
                self.low_byte = False
                self.count = value
            else:
                self.low_byte = True
                self.count = (value << 8) | self.count
                if self.mode == 0:
                    self.enabled = True
                    self.value = self.count
                elif self.mode == 2 or self.mode == 3:
                    self.enabled = True
        else:
            raise RuntimeError("Invalid PIT channel r/w mode: %r", self.read_write_mode)
            
class SpeakerChannel(Counter):
    """ Special timer channel that updates the tone of the emulated PC speaker based on the count. """
    def write(self, value):
        super(SpeakerChannel, self).write(value)
        
        if self.enabled:
            if self.count > 0:
                GLOBAL_SPEAKER.set_tone_from_counter(self.count)
            else:
                GLOBAL_SPEAKER.stop()
                
class ProgrammableIntervalTimer(Device):
    """ A Device emulating an 8253 PIT timer. """
    def __init__(self, base, **kwargs):
        super(ProgrammableIntervalTimer, self).__init__(**kwargs)
        self.base = base
        self.channels = [Counter(self.counter_0_callback), Counter(self.counter_1_callback), SpeakerChannel()]
        
    # Device interface.
    def clock(self, cycles):
        for channel in self.channels:
            channel.clock(cycles)
            
    def get_ports_list(self):
        return [x for x in range(self.base, self.base + 4)]
        
    def io_read_byte(self, port):
        offset = port - self.base
        if offset < 3:
            value = self.channels[offset].read()
        else:
            value = 0x00
            
        log.debug("PIT read: port 0x%03x, 0x%02x", port, value)
        return value
        
    def io_write_byte(self, port, value):
        log.debug("PIT write: port 0x%03x, 0x%02x", port, value)
        offset = port - self.base
        if offset < 3:
            self.channels[offset].write(value)
        elif offset == 3:
            counter, command, mode, bcd = self.decode_control_word(value)
            if command == PIT_COMMAND_LATCH:
                self.channels[counter].latch()
            else:
                self.channels[counter].reconfigure(command, mode, bcd)
                
    # Local functions.
    @classmethod
    def decode_control_word(cls, value):
        """ Decode a control word into its fields. """
        counter = (value >> 6) & 0x03
        assert counter != 3, "There are only 3 counters!"
        
        command = (value >> 4) & 0x03
        
        mode = (value >> 1) & 0x07
        if mode > 5:
            mode -= 4
            
        bcd = value & 0x01
        
        return counter, command, mode, bcd
        
    def counter_0_callback(self, value):
        """
        Called back when channel 0 reaches terminal count.
        """
        # We only care about a positive going transition.
        if value:
            self.bus.interrupt_request(TIMER_IRQ_LINE)
            
    def counter_1_callback(self, value):
        """
        Called back when channel 1 reaches terminal count.
        """
        # We only care about a positive going transition.
        if value:
            self.bus.dma_request(0, 0, None)
            
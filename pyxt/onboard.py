"""
pyxt.components - Various components needed for PyXT.
"""

# Standard library imports

# Six imports
from six.moves import range # pylint: disable=redefined-builtin

# PyXT imports
from pyxt.bus import Device

# Classes
class ProgrammableInterruptController(Device):
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
        self.address_interval = 4
        self.i8086_8088_mode = False
        self.auto_eoi = False
        self.slave_mode_address = 7
        
        # ICWS (Initialization Commands Words) state machine, per the datasheet.
        # 0 indicates the idle state, 1-4 indicate what byte will be processed next.
        self.icws_state = 0
        self.icw4_needed = False
        
        self.interrupt_request_register = 0x00
        
    # Device interface.
    def get_ports_list(self):
        return [x for x in range(self.base, self.base + 2)]
        
    def io_read_byte(self, address):
        offset = address - self.base
        if offset == 1:
            return self.mask
        else:
            return 0
            
    def io_write_byte(self, address, value):
        offset = address - self.base
        if offset == 0 and value & 0x10 == 0x10:
            self.start_initialization_sequence()
            
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
                    
    # Local functions.
    def start_initialization_sequence(self):
        """ Kick off the 8259 initialization sequence. """
        self.trigger_mode = self.EDGE_TRIGGERED
        self.mask = 0x00
        self.priorities[7] = 7
        self.slave_mode_address = 7
        # TODO: Clear special mask mode?
        # TODO: Set status read to IRR?
        self.icws_state = 1
        self.icw4_needed = False
        
    def process_icws_byte(self, value):
        """ Run a byte through the initialization state machine. """
        if self.icws_state == 1:
            self.icw4_needed = value & 0x01 == 0x01
            self.cascade = not (value & 0x02 == 0x02)
            self.address_interval = 4 if value & 0x04 == 0x04 else 8
            self.trigger_mode = self.LEVEL_TRIGGERED if value & 0x04 == 0x04 else self.EDGE_TRIGGERED
            # TODO: No support for full MCS-80/8085 vector addresses.
            
            if not self.icw4_needed:
                self.i8086_8088_mode = False
                self.auto_eoi = False
                
            self.icws_state = 2
            
        elif self.icws_state == 2:
            self.vector_base = value & 0xF1
            # TODO: No support for full MCS-80/8085 vector addresses.
            
            if self.cascade:
                self.icws_state = 3
            elif self.icw4_needed:
                self.icws_state = 4
            else:
                self.icws_state = 0
                
        elif self.icws_state == 3:
            # TODO: Currently no support for cascade mode or slave 8259's.
            if self.icw4_needed:
                self.icws_state = 4
            else:
                self.icws_state = 0
                
        elif self.icws_state == 4:
            self.i8086_8088_mode = value & 0x01 == 0x01
            self.auto_eoi = value & 0x02 == 0x02
            # TODO: Currently no support for buffered mode.
            # TODO: No support for "special fully nested mode".
            self.icws_state = 0
            
    def process_ocw2_byte(self, value):
        command = (value & 0xE0) >> 5
        interrupt = value & 0x07
        print("command = %r, interrupt = %r" % (command, interrupt))
        
    def interrupt_request(self, irq):
        """ Called when an interrupt is requested from a device. """
        irq_mask = 0x01 << irq
        
        # If the IRQ is masked, ignore the request.
        if irq_mask & self.mask == irq_mask:
            return
            
        # Log that the interrupt is pending service.
        self.interrupt_request_register |= irq_mask
        
    def interrupt_pending(self):
        """ Returns True if an interrupt request is pending. """
        return self.interrupt_request_register != 0x00
        
PIT_COMMAND_LATCH = 0x00
PIT_READ_WRITE_NONE = 0x00
PIT_READ_WRITE_LOW = 0x01
PIT_READ_WRITE_HIGH = 0x02
PIT_READ_WRITE_BOTH = 0x03

class Counter(object):
    """ Class containing the configuration for a single PIT channel. """
    def __init__(self):
        self.count = 0
        self.value = 0
        self.latched_value = None
        self.mode = 0
        self.enabled = False
        
        self.read_write_mode = PIT_READ_WRITE_NONE
        self.low_byte = True
        self.output = False
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
                
    def clock(self):
        """ Handle the clock input to the channel. """
        if not self.enabled:
            return
            
        if self.mode == 0:
            if self.gate:
                self.value -= 1
                
            if self.value == 0:
                self.output = True
            elif self.value == -1:
                self.value = 0xFFFF
                
        elif self.mode == 2:
            self.value = (self.value - 1) & 0xFFFF
            if self.value == 1:
                self.output = False
            elif self.value == 0:
                self.value = self.count
                self.output = True
                
        elif self.mode == 3:
            if self.value & 0x0001:
                if self.output:
                    self.value -= 1
                else:
                    self.value -= 3
            else:
                self.value -= 2
                
            if self.value == 0:
                self.output = not self.output
                self.value = self.count
                
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
            
class ProgrammableIntervalTimer(Device):
    """ An IOComponent emulating an 8253 PIT timer. """
    # This is intentionally not 4 so that it is misaligned with the CPU which currenly assumes 1
    # clock cycle per instruction.
    CLOCK_DIVISOR = 3
    
    def __init__(self, base, **kwargs):
        super(ProgrammableIntervalTimer, self).__init__(**kwargs)
        self.base = base
        self.channels = [Counter(), Counter(), Counter()]
        self.divisor = self.CLOCK_DIVISOR
        
    # Device interface.
    def clock(self):
        self.divisor -= 1
        if self.divisor == 0:
            self.divisor = self.CLOCK_DIVISOR
            for channel in self.channels:
                channel.clock()
        # else:
            
    def get_ports_list(self):
        return [x for x in range(self.base, self.base + 4)]
        
    def io_read_byte(self, port):
        offset = port - self.base
        if offset < 3:
            return self.channels[offset].read()
        else:
            return 0x00
            
    def io_write_byte(self, port, value):
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
        
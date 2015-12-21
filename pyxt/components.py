"""
pyxt.components - Various components needed for PyXT.
"""

# Standard library imports

# PyXT imports
from pyxt.helpers import *
from pyxt.constants import *
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
        self.i8086_8088_mode = False
        self.auto_eoi = False
        self.slave_mode_address = 7
        
        # ICWS (Initialization Commands Words) state machine, per the datasheet.
        # 0 indicates the idle state, 1-4 indicate what byte will be processed next.
        self.icws_state = 0
        self.icw4_needed = False
        
    def get_ports_list(self):
        return [x for x in xrange(self.base, self.base + 2)]
        
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
            self.cascade = value & 0x02 == 0x02
            # TODO: Do we need call address interval for 8086 mode?
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
        print "command = %r, interrupt = %r" % (command, interrupt)
        
    # def io_read_byte(self, address):
        # offset = address - self.base
        # if offset == 0 or offset == 1 or offset == 2:
            # return self.channels[offset]
        # elif offset == 3:
            # print "CONTROL REGISTER"
        # else:
            # raise ValueError("Bad offset to the 8253!!!")
            
    def io_write_byte(self, address, value):
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
                    
            
class ProgrammableIntervalTimer(Device):
    """ An IOComponent emulating an 8253 PIT timer. """
    def __init__(self, base, **kwargs):
        super(ProgrammableIntervalTimer, self).__init__(**kwargs)
        self.base = base
        self.channels = [0, 0, 0]
        
    def get_ports_list(self):
        return [x for x in xrange(self.base, self.base + 8)]
        
    def io_read_byte(self, address):
        offset = address - self.base
        if offset == 0 or offset == 1 or offset == 2:
            return self.channels[offset]
        elif offset == 3:
            print "CONTROL REGISTER"
        else:
            raise ValueError("Bad offset to the 8253!!!")
            
"""
pyxt.components - Various components needed for PyXT.
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

# Classes
class ProgrammableInterruptController(Device):
    """ An IOComponent emulating an 8259 PIC controller. """
    EDGE_TRIGGERED = 0
    LEVEL_TRIGGERED = 1
    
    READ_NONE = 0x00
    READ_NONE_ALSO = 0x01
    READ_IR_REGISTER = 0x02
    READ_IS_REGISTER = 0x03
    OCW3_READ_REGISTER_MASK = 0x03
    
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
        
        self.read_register = self.READ_NONE
        self.interrupt_request_register = 0x00
        self.interrupt_in_service_register = 0x00
        
        self.__interrupt_pending = False
        
    # Device interface.
    def get_ports_list(self):
        return [x for x in range(self.base, self.base + 2)]
        
    def io_read_byte(self, address):
        offset = address - self.base
        if offset == 1:
            return self.mask
        elif self.read_register == self.READ_IR_REGISTER:
            return self.interrupt_request_register
        elif self.read_register == self.READ_IS_REGISTER:
            return self.interrupt_in_service_register
        else:
            return 0x00
            
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
            self.vector_base = value & 0xF8
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
        # print("command = %r, interrupt = %r" % (command, interrupt))
        
    def process_ocw3_byte(self, value):
        self.read_register = value & self.OCW3_READ_REGISTER_MASK
        
    def interrupt_request(self, irq):
        """ Called when an interrupt is requested from a device. """
        irq_mask = 0x01 << irq
        
        # If the IRQ is masked, ignore the request.
        if irq_mask & self.mask == irq_mask:
            return
            
        # Log that the interrupt is pending service.
        self.interrupt_request_register |= irq_mask
        
        # Signal the CPU that an interrupt has occured.
        self.set_interrupt_signal(True)
        
    def interrupt_acknowledge(self):
        """ Acknowledges the highest priority interrupt and returns the vector number. """
        # TODO: Proper priority handling.
        for irq in range(8):
            irq_mask = 0x01 << irq
            if irq_mask & self.interrupt_request_register == irq_mask:
                self.interrupt_request_register &= ~irq_mask
                self.interrupt_in_service_register |= irq_mask
                
                # If this was the only bit set, clear the interrupt line.
                if self.interrupt_request_register == 0x00 and self.bus:
                    self.set_interrupt_signal(False)
                    
                return self.vector_base + irq
        
        raise RuntimeError("interrupt_acknowledge() called with no pending interrupts!")
        
    def interrupt_pending(self):
        """ Returns the state of the INT line to the CPU for unit testing. """
        return self.__interrupt_pending
        
    def set_interrupt_signal(self, value):
        """ Set the state of the INT line to the CPU. """
        self.__interrupt_pending = value
        if self.bus and self.bus.cpu:
            self.bus.cpu.interrupt_signaled = value
            
"""
pyxt.fdc - Floppy diskette controller for PyXT.
"""

# Standard library imports

# PyXT imports
from pyxt.bus import Device

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants
FDC_CONTROL = 2 # Digital output register, external to the actual controller.
FDC_STATUS = 4
FDC_DATA = 5

FDC_IRQ_LINE = 6

CONTROL_DRIVE0_MOTOR = 0x10 # A:
CONTROL_DRIVE1_MOTOR = 0x20 # B:
CONTROL_DRIVE2_MOTOR = 0x40 # C: ???
CONTROL_DRIVE3_MOTOR = 0x80 # D: ???
CONTROL_DMA_ENABLE = 0x08
CONTROL_N_RESET = 0x04
CONTROL_DRIVE_SELECT = 0x03 # Mask for drive number.

# MSR - Main status register.
MSR_DRIVE0_BUSY = 0x01
MSR_DRIVE1_BUSY = 0x02
MSR_DRIVE2_BUSY = 0x04
MSR_DRIVE3_BUSY = 0x08
MSR_FDC_BUSY = 0x10
MSR_NON_DMA_MODE = 0x20
MSR_DIRECTION = 0x40
MSR_READY = 0x80

# Use these with MSR_DIRECTION.
DIRECTION_FDC_TO_CPU = 0x40
DIRECTION_CPU_TO_FDC = 0x00

# Top-level FDC commands.
COMMAND_READ_DATA = 0x06
COMMAND_READ_DELETED_DATA = 0x0C
COMMAND_WRITE_DATA = 0x05
COMMAND_WRITE_DELETED_DATA = 0x09
COMMAND_READ_A_TRACK = 0x02
COMMAND_READ_ID = 0x0A
COMMAND_FORMAT_TRACK = 0x0D
COMMAND_SCAN_EQUAL = 0x11
COMMAND_SCAN_LOW_OR_EQUAL = 0x19
COMMAND_SCAN_HIGH_OR_EQUAL = 0x1D
COMMAND_RECALIBRATE = 0x07
COMMAND_SENSE_INTERRUPT_STATUS = 0x08
COMMAND_SPECIFY = 0x03
COMMAND_SENSE_DRIVE_STATUS = 0x04
COMMAND_SEEK = 0x0F

COMMAND_OPCODE_MASK = 0x1F
COMMAND_MULTITRACK_MASK = 0x80
COMMAND_MFM_MASK = 0x40
COMMAND_SKIP_MASK = 0x20

# Command states.
ST_READ_MASK = 0x8000
ST_READY = 0x0000

# SIS - Sense interrupt status.
ST_SIS_READ_STATUS_REG_0 = ST_READ_MASK | 0x0010
ST_SIS_READ_PRESENT_CYLINDER = ST_READ_MASK | 0x0011

# Classes
class FloppyDisketteController(Device):
    """ Floppy diskette controller based on the NEC uPD765/Intel 8272A controllers. """
    def __init__(self, base, **kwargs):
        super(FloppyDisketteController, self).__init__(**kwargs)
        self.base = base
        self.enabled = False
        self.state = ST_READY
        
        self.states = {
            # state, : (read_function, write_function, next_state)
            ST_READY : (None, self.write_toplevel_command, ST_READY),
            ST_SIS_READ_STATUS_REG_0 : (self.read_status_register_0, None, ST_SIS_READ_PRESENT_CYLINDER),
            ST_SIS_READ_PRESENT_CYLINDER : (self.read_present_cylinder_number, None, ST_READY),
        }
        
        self.drive_select = 0
        self.head_select = 0
        
        self.drives = [None, None, None, None]
        
    # Device interface.
    def get_ports_list(self):
        return [self.base + FDC_CONTROL, self.base + FDC_STATUS, self.base + FDC_DATA]
        
    def reset(self):
        self.state = ST_READY
        self.bus.pic.interrupt_request(FDC_IRQ_LINE)
        
    def io_read_byte(self, port):
        offset = port - self.base
        if offset == FDC_STATUS:
            status = self.read_main_status_register()
            log.debug("Main status register: 0x%02x.", status)
            return status
        elif offset == FDC_DATA:
            return self.read_data_register()
        else:
            log.warning("Invalid FDC port read: 0x%03x, returning 0x00.", port)
            return 0x00
            
    def io_write_byte(self, port, value):
        offset = port - self.base
        if offset == FDC_CONTROL:
            self.write_control_register(value)
        elif offset == FDC_DATA:
            self.write_data_register(value)
        else:
            log.warning("Invalid FDC port write: 0x%03x, with: 0x%02x.", port, value)
            
    # Local functions.
    def attach_drive(self, drive, number):
        """ Attach a drive to the diskette controller. """
        self.drives[number] = drive
        
    def write_control_register(self, value):
        """ Helper for performing actions when the control register is written. """
        previously_enabled = self.enabled
        self.enabled = value & CONTROL_N_RESET == CONTROL_N_RESET
        
        if self.enabled and not previously_enabled:
            self.reset()
        
    def read_main_status_register(self):
        """ Helper for building the response to a main status register request. """
        value = 0x00
        if self.enabled:
            value |= MSR_READY
        if self.state != ST_READY:
            value |= MSR_FDC_BUSY
        if self.state & ST_READ_MASK == ST_READ_MASK:
            value |= DIRECTION_FDC_TO_CPU
        return value
        
    def write_data_register(self, value):
        """ Helper for handling writes to the data register. """
        read_function, write_function, self.state = self.states[self.state]
        if write_function:
            write_function(value)
        else:
            log.warning("Attempted to WRITE a READ-ONLY state (0x%04x) with 0x%02x.", self.state, value)
            
    def read_data_register(self):
        """ Helper for handling reads from the data register. """
        read_function, write_function, self.state = self.states[self.state]
        if read_function:
            return read_function()
        else:
            log.warning("Attempted to READ a WRITE-ONLY state (0x%04x), you get 0x00.", self.state)
            return 0x00
            
    def write_toplevel_command(self, value):
        """ Kicks off a top-level FDC command, overwrites state. """
        if value == COMMAND_SENSE_INTERRUPT_STATUS:
            self.state = ST_SIS_READ_STATUS_REG_0
        else:
            log.debug("Invalid command: 0x%02x", value)
            
            # For now, stop in the debugger when we hit an invalid command.
            if self.bus:
                self.bus.force_debugger_break("Invalid FDC command: 0x%02x" % value)
                
    def read_status_register_0(self):
        """ Builds a status register 0 response. """
        value = self.drive_select
        if self.head_select == 1:
            value |= 0x04
        # TODO: The rest of this.
        return value
        
    def read_present_cylinder_number(self):
        """ Returns the present cylinder number for the selected drive. """
        drive = self.drives[self.drive_select]
        if drive:
            return drive.present_cylinder_number
        else:
            return 0
            
class FloppyDisketteDrive(object):
    """ Maintains the "physical state" of an attached diskette drive. """
    def __init__(self, drive_type):
        self.drive_type = drive_type
        self.present_cylinder_number = 0
        
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
ST_READY = 0

# Classes
class FloppyDisketteController(Device):
    """ Floppy diskette controller based on the NEC uPD765/Intel 8272A controllers. """
    def __init__(self, base, **kwargs):
        super(FloppyDisketteController, self).__init__(**kwargs)
        self.base = base
        self.enabled = False
        self.state = ST_READY
        
    # Device interface.
    def get_ports_list(self):
        return [self.base + FDC_CONTROL, self.base + FDC_STATUS, self.base + FDC_DATA]
        
    def reset(self):
        self.state = ST_READY
        self.bus.pic.interrupt_request(FDC_IRQ_LINE)
        
    def io_read_byte(self, port):
        offset = port - self.base
        if offset == FDC_STATUS:
            status = self.read_status_register()
            log.debug("Read status register: 0x%02x.", status)
            return status
        elif offset == FDC_DATA:
            log.warning("Invalid FDC data register read: 0x%03x, returning 0x00.", port)
            return 0
        else:
            log.warning("Invalid FDC port read: 0x%03x, returning 0x00.", port)
            return 0x00
            
    def io_write_byte(self, port, value):
        offset = port - self.base
        if offset == FDC_CONTROL:
            self.write_control_register(value)
        elif offset == FDC_DATA:
            log.warning("FDC data register write: 0x%03x, with: 0x%02x.", port, value)
            pass
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
        
    def read_status_register(self):
        """ Helper for building the response to a status request. """
        value = 0x00
        if self.enabled:
            value |= MSR_READY
        return value
        
class FloppyDisketteDrive(object):
    """ Maintains the "physical state" of an attached diskette drive. """
    def __init__(self, drive_type):
        self.drive_type = drive_type
        self.present_cylinder_number = 0
        
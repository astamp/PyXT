"""
pyxt.fdc - Floppy diskette controller for PyXT.
"""

# Standard library imports
import array
from collections import namedtuple

# Six imports
import six

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

# SR0 - Status register 0.
SR0_DRIVE_SELECT_MASK = 0x03
SR0_HEAD_SELECT = 0x04
SR0_NOT_READY = 0x08
SR0_EQUIPMENT_CHECK = 0x10
SR0_SEEK_END = 0x20
SR0_INT_CODE_MASK = 0xC0
SR0_INT_CODE_NORMAL = 0x00
SR0_INT_CODE_ABNORMAL = 0x40
SR0_INT_CODE_INVALID = 0x80
SR0_INT_CODE_READY_CHANGE = 0xC0

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
ST_EXECUTE_MASK = 0x4000
ST_READY = 0x0000

# SIS - Sense interrupt status.
ST_SIS_READ_STATUS_REG_0 = ST_READ_MASK | 0x0010
ST_SIS_READ_PRESENT_CYLINDER = ST_READ_MASK | 0x0011

# RECAL - Recalibrate.
ST_RECAL_SELECT_DRIVE = 0x0020
ST_RECAL_EXECUTE = ST_EXECUTE_MASK | 0x0021

# SPEC - Specify.
ST_SPEC_HEAD_UNLOAD_STEP_RATE = 0x0030
ST_SPEC_HEAD_LOAD_NON_DMA = 0x0031

# Seek.
ST_SEEK_SELECT_DRIVE_HEAD = 0x0040
ST_SEEK_WRITE_NEW_CYLINDER = 0x0041
ST_SEEK_EXECUTE = ST_EXECUTE_MASK | 0x0042

# Drive type definitions.
DriveInfo = namedtuple("DriveInfo", ["bytes_per_sector", "sectors_per_track", "tracks_per_side", "sides"])

FIVE_INCH_360_KB = DriveInfo(512, 9, 40, 2)
FIVE_INCH_1_2_MB = DriveInfo(512, 15, 80, 2)
THREE_INCH_720_KB = DriveInfo(512, 9, 80, 2)
THREE_INCH_1_4_MB = DriveInfo(512, 18, 80, 2)

# Classes
class FloppyDisketteController(Device):
    """ Floppy diskette controller based on the NEC uPD765/Intel 8272A controllers. """
    def __init__(self, base, **kwargs):
        super(FloppyDisketteController, self).__init__(**kwargs)
        self.base = base
        self.enabled = False
        self.state = ST_READY
        
        self.states = {
            # state, : (read_function, write_function, execute_function, next_state)
            ST_READY : (None, self.write_toplevel_command, None, ST_READY),
            
            # Sense interrupt status.
            ST_SIS_READ_STATUS_REG_0 : (self.read_status_register_0, None, None, ST_SIS_READ_PRESENT_CYLINDER),
            ST_SIS_READ_PRESENT_CYLINDER : (self.read_present_cylinder_number, None, None, ST_READY),
            
            # Recalibrate.
            ST_RECAL_SELECT_DRIVE : (None, self.write_drive_head_select, None, ST_RECAL_EXECUTE),
            ST_RECAL_EXECUTE : (None, None, self.recalibrate, ST_READY),
            
            # Specify.
            ST_SPEC_HEAD_UNLOAD_STEP_RATE : (None, self.write_head_unload_step_rate, None, ST_SPEC_HEAD_LOAD_NON_DMA),
            ST_SPEC_HEAD_LOAD_NON_DMA : (None, self.write_head_load_and_dma, None, ST_READY),
            
            # Seek.
            ST_SEEK_SELECT_DRIVE_HEAD : (None, self.write_drive_head_select, None, ST_SEEK_WRITE_NEW_CYLINDER),
            ST_SEEK_WRITE_NEW_CYLINDER : (None, self.write_new_cylinder_number, None, ST_SEEK_EXECUTE),
            ST_SEEK_EXECUTE : (None, None, self.seek, ST_READY),
        }
        
        self.drive_select = 0
        self.head_select = 0
        self.dma_enable = False
        
        self.interrupt_code = SR0_INT_CODE_NORMAL
        
        self.drives = [None, None, None, None]
        
    # Device interface.
    def get_ports_list(self):
        return [self.base + FDC_CONTROL, self.base + FDC_STATUS, self.base + FDC_DATA]
        
    def reset(self):
        self.state = ST_READY
        self.dma_enable = False
        self.signal_interrupt(SR0_INT_CODE_READY_CHANGE)
        
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
        # self.bus.force_debugger_break("FDC WRITE")
        log.debug("WRITE 0x%02x to state 0x%04x", value, self.state)
        read_function, write_function, execute_function, self.state = self.states[self.state]
        if write_function:
            write_function(value)
        else:
            log.warning("Attempted to WRITE a READ-ONLY state (0x%04x) with 0x%02x.", self.state, value)
            
        # If this was the last write for a command, check if we are in an execute state.
        if self.state & ST_EXECUTE_MASK == ST_EXECUTE_MASK:
            read_function, write_function, execute_function, self.state = self.states[self.state]
            execute_function()
        
    def read_data_register(self):
        """ Helper for handling reads from the data register. """
        # self.bus.force_debugger_break("FDC READ")
        log.debug("READ from state 0x%04x", self.state)
        read_function, write_function, execute_function, self.state = self.states[self.state]
        if read_function:
            return read_function()
        else:
            log.warning("Attempted to READ a WRITE-ONLY state (0x%04x), you get 0x00.", self.state)
            return 0x00
            
    def write_toplevel_command(self, value):
        """ Kicks off a top-level FDC command, overwrites state. """
        if value == COMMAND_SENSE_INTERRUPT_STATUS:
            self.state = ST_SIS_READ_STATUS_REG_0
        elif value == COMMAND_RECALIBRATE:
            self.state = ST_RECAL_SELECT_DRIVE
        elif value == COMMAND_SPECIFY:
            self.state = ST_SPEC_HEAD_UNLOAD_STEP_RATE
        elif value == COMMAND_SEEK:
            self.state = ST_SEEK_SELECT_DRIVE_HEAD
        else:
            log.debug("Invalid command: 0x%02x", value)
            
            # For now, stop in the debugger when we hit an invalid command.
            if self.bus:
                self.bus.force_debugger_break("Invalid FDC command: 0x%02x" % value)
                
    def read_status_register_0(self):
        """ Builds a status register 0 response. """
        value = self.drive_select | self.interrupt_code
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
            
    def write_drive_head_select(self, value):
        """ Configures the FDC drive and head select lines. """
        self.drive_select = value & 0x03
        self.head_select = 1 if value & 0x04 else 0
        
    def write_head_unload_step_rate(self, value):
        """ Configures the FDC head unload time and step rate. """
        # TODO: Should these be stored/used for something?
        
    def write_head_load_and_dma(self, value):
        """ Configures the FDC head load time and DMA configuration. """
        # TODO: Should the head load time be stored/used for something?
        # Bit 0 indicates NON-DMA mode.
        self.dma_enable = value & 0x01 == 0x00
        
    def write_new_cylinder_number(self, value):
        """ Sets the new target cylinder for the currently selected drive. """
        drive = self.drives[self.drive_select]
        if drive:
            drive.target_cylinder_number = value
            
    def seek(self):
        """ Performs a seek on the selected drive. """
        drive = self.drives[self.drive_select]
        if drive:
            if drive.target_cylinder_number < drive.drive_info.tracks_per_side:
                drive.present_cylinder_number = drive.target_cylinder_number
                self.signal_interrupt(SR0_INT_CODE_NORMAL | SR0_SEEK_END)
            else:
                self.signal_interrupt(SR0_INT_CODE_ABNORMAL | SR0_SEEK_END)
            
    def recalibrate(self):
        """ Performs a recalibrate on the selected drive. """
        drive = self.drives[self.drive_select]
        if drive:
            drive.present_cylinder_number = 0
            self.signal_interrupt(SR0_INT_CODE_NORMAL | SR0_SEEK_END)
            
    def signal_interrupt(self, reason):
        """ Signal the FDC IRQ line and set the last interrupt reason. """
        self.interrupt_code = reason
        if self.bus:
            self.bus.pic.interrupt_request(FDC_IRQ_LINE)
        
class FloppyDisketteDrive(object):
    """ Maintains the "physical state" of an attached diskette drive. """
    def __init__(self, drive_info):
        self.drive_info = drive_info
        
        self.present_cylinder_number = 0
        self.target_cylinder_number = 0
        self.contents = None
        
    @property
    def size_in_bytes(self):
        """ Returns the diskette size in bytes based on the drive geometry. """
        return (self.drive_info.bytes_per_sector * self.drive_info.sectors_per_track *
                self.drive_info.tracks_per_side * self.drive_info.sides)
                
    def load_diskette(self, filename):
        """ Load a diskette image, "ejecting" a previous one if present. """
        log.info("Loading diskette from: %s", filename)
        self.contents = None
        
        if filename is not None:
            self.contents = array.array("B", (0,) * self.size_in_bytes)
            with open(filename, "rb") as fileptr:
                data = fileptr.read()
                
                if len(data) > self.size_in_bytes:
                    raise ValueError("Disk image (%d byte) is larger than supported by the drive (%d bytes)!" % (
                        len(data), self.size_in_bytes,
                    ))
                    
            for index, byte in enumerate(six.iterbytes(data)):
                self.contents[index] = byte
                
    def store_diskette(self, filename):
        """ Write the content of the virtual diskette back to an image file. """
        log.info("Writing diskette to: %s", filename)
        
        if self.contents is not None:
            with open(self.filename, "wb") as fileptr:
                self.contents.tofile(fileptr)
                
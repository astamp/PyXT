"""
pyxt.fdc - Floppy diskette controller for PyXT.
"""

# Standard library imports
import array
from collections import namedtuple

# Six imports
import six
from six.moves import range # pylint: disable=redefined-builtin

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
FDC_DMA_CHANNEL = 2

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

# SR3 - Status register 3.
SR3_DRIVE_SELECT_MASK = 0x03
SR3_HEAD_SELECT = 0x04
SR3_TWO_SIDED = 0x08
SR3_TRACK_ZERO = 0x10
SR3_READY = 0x20
SR3_WRITE_PROTECT = 0x40
SR3_FAULT = 0x80

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

# RDDATA - Read data.
ST_RDDATA_SELECT_DRIVE_HEAD = 0x0050
ST_RDDATA_SELECT_CYLINDER = 0x0051
ST_RDDATA_SELECT_HEAD = 0x0052
ST_RDDATA_SELECT_SECTOR = 0x0053
ST_RDDATA_SET_BYTES_PER_SECTOR = 0x0054
ST_RDDATA_SET_END_OF_TRACK = 0x0055
ST_RDDATA_SET_GAP_LENGTH = 0x0056
ST_RDDATA_SET_DATA_LENGTH = 0x0057
ST_RDDATA_BEGIN_EXECUTION = ST_EXECUTE_MASK | 0x0058
ST_RDDATA_IN_PROGRESS = ST_READ_MASK | 0x0059
ST_RDDATA_READ_STATUS_REG_0 = ST_READ_MASK | 0x005A

# SDS - Sense drive status.
ST_SDS_SELECT_DRIVE_HEAD = 0x0060
ST_SDS_READ_STATUS_REG_3 = ST_READ_MASK | 0x0061

# WRTDATA - Read data.
ST_WRTDATA_SELECT_DRIVE_HEAD = 0x0070
ST_WRTDATA_SELECT_CYLINDER = 0x0071
ST_WRTDATA_SELECT_HEAD = 0x0072
ST_WRTDATA_SELECT_SECTOR = 0x0073
ST_WRTDATA_SET_BYTES_PER_SECTOR = 0x0074
ST_WRTDATA_SET_END_OF_TRACK = 0x0075
ST_WRTDATA_SET_GAP_LENGTH = 0x0076
ST_WRTDATA_SET_DATA_LENGTH = 0x0077
ST_WRTDATA_BEGIN_EXECUTION = ST_EXECUTE_MASK | 0x0078
ST_WRTDATA_IN_PROGRESS = 0x0079
ST_WRTDATA_READ_STATUS_REG_0 = ST_READ_MASK | 0x007A

# Drive type definitions.
DriveInfo = namedtuple("DriveInfo", ["bytes_per_sector", "sectors_per_track", "tracks_per_side", "sides"])

FIVE_INCH_180_KB = DriveInfo(512, 9, 40, 1)
FIVE_INCH_360_KB = DriveInfo(512, 9, 40, 2)
FIVE_INCH_1_2_MB = DriveInfo(512, 15, 80, 2)
THREE_INCH_720_KB = DriveInfo(512, 9, 80, 2)
THREE_INCH_1_4_MB = DriveInfo(512, 18, 80, 2)

IMAGE_SIZE_TO_DRIVE_INFO = {
    184320 : FIVE_INCH_180_KB,
    368640 : FIVE_INCH_360_KB,
    1228800 : FIVE_INCH_1_2_MB,
    737280 : THREE_INCH_720_KB,
    1474560 : THREE_INCH_1_4_MB,
}

# Helper functions
# See: https://en.wikipedia.org/wiki/Cylinder-head-sector#CHS_to_LBA_mapping
def chs_to_lba(drive_info, cylinder, head, sector):
    """ Converts a cylinder/head/sector address to a logical block address for a given drive geometry. """
    if sector == 0:
        raise ValueError("Sectors start counting at 1!")
    return (((cylinder * drive_info.sides) + head) * drive_info.sectors_per_track) + (sector - 1)
    
def calculate_parameters(drive_info, command_parms):
    """ Return the offset and length to index into the disk data based on the supplied drive geometry and parameters. """
    # if command_parms.multi_track:
        # starting_sector = 1
        # final_sector = drive_info.sectors_per_track * drive_info.sides
    # else:
    starting_sector = command_parms.sector
    final_sector = command_parms.end_of_track
        
    lba = chs_to_lba(drive_info, command_parms.cylinder, command_parms.head, starting_sector)
    offset = lba * drive_info.bytes_per_sector
    # TODO: How is the number of sectors calculated, is it always 1?!
    sectors = 1
    # sectors = (final_sector - starting_sector) + 1
    length = sectors * drive_info.bytes_per_sector
    return offset, length
    
def detect_diskette_type_from_image_size(size):
    """ Return the appropriate DriveInfo definition for the given image size. """
    return IMAGE_SIZE_TO_DRIVE_INFO.get(size, None)
    
# Command parameters.
class CommandParameters(object):
    """ Parameters for an FDC read/write/scan command. """
    def __init__(self):
        self.multi_track = False # MT
        self.mfm = False # MFM
        self.skip_deleted = False # SK
        self.cylinder = 0 # C
        self.head = 0 # H
        self.sector = 1 # R (Starts at 1)
        self.bytes_per_sector = 0 # N
        self.sectors_per_cylinder = 0 # SC
        self.end_of_track = 1 # EOT (Starts at 1)
        self.gap_length = 0 # GPL
        self.data_length = 0 # DTL
        
    def dump(self):
        """ Return a string containing all of the command parameters. """
        return "\r\n".join([
            "multi_track = %r" % self.multi_track,
            "mfm = %r" % self.mfm,
            "skip_deleted = %r" % self.skip_deleted,
            "cylinder = %r" % self.cylinder,
            "head = %r" % self.head,
            "sector = %r" % self.sector,
            "bytes_per_sector = %r" % self.bytes_per_sector,
            "sectors_per_cylinder = %r" % self.sectors_per_cylinder,
            "end_of_track = %r" % self.end_of_track,
            "gap_length = %r" % self.gap_length,
            "data_length = %r" % self.data_length,
        ])
        
    def next_sector(self):
        """ Increments the command parameters to point at the next sector on disk. """
        if self.sector == self.end_of_track:
            if self.multi_track:
                self.sector = 1
                if self.head == 0:
                    self.head = 1
                else:
                    self.head = 0
                    self.cylinder += 1
            else:
                self.sector = 1
                self.cylinder += 1
        else:
            self.sector += 1
            
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
            
            # Read data.
            ST_RDDATA_SELECT_DRIVE_HEAD : (None, self.write_drive_head_select, None, ST_RDDATA_SELECT_CYLINDER),
            ST_RDDATA_SELECT_CYLINDER : (None, self.write_cylinder_parameter, None, ST_RDDATA_SELECT_HEAD),
            ST_RDDATA_SELECT_HEAD : (None, self.write_head_parameter, None, ST_RDDATA_SELECT_SECTOR),
            ST_RDDATA_SELECT_SECTOR : (None, self.write_sector_parameter, None, ST_RDDATA_SET_BYTES_PER_SECTOR),
            ST_RDDATA_SET_BYTES_PER_SECTOR : (None, self.write_bytes_per_sector_parameter, None, ST_RDDATA_SET_END_OF_TRACK),
            ST_RDDATA_SET_END_OF_TRACK : (None, self.write_end_of_track_parameter, None, ST_RDDATA_SET_GAP_LENGTH),
            ST_RDDATA_SET_GAP_LENGTH : (None, self.write_gap_length_parameter, None, ST_RDDATA_SET_DATA_LENGTH),
            ST_RDDATA_SET_DATA_LENGTH : (None, self.write_data_length_parameter, None, ST_RDDATA_BEGIN_EXECUTION),
            ST_RDDATA_BEGIN_EXECUTION : (None, None, self.begin_read_data, ST_RDDATA_IN_PROGRESS),
            ST_RDDATA_IN_PROGRESS : (self.read_data, None, None, ST_RDDATA_IN_PROGRESS),
            ST_RDDATA_READ_STATUS_REG_0 : (self.read_status_register_0, None, None, ST_READY),
            
            # Sense drive status.
            ST_SDS_SELECT_DRIVE_HEAD : (None, self.write_drive_head_select, None, ST_SDS_READ_STATUS_REG_3),
            ST_SDS_READ_STATUS_REG_3 : (self.read_status_register_3, None, None, ST_READY),
            
            # Write data.
            ST_WRTDATA_SELECT_DRIVE_HEAD : (None, self.write_drive_head_select, None, ST_WRTDATA_SELECT_CYLINDER),
            ST_WRTDATA_SELECT_CYLINDER : (None, self.write_cylinder_parameter, None, ST_WRTDATA_SELECT_HEAD),
            ST_WRTDATA_SELECT_HEAD : (None, self.write_head_parameter, None, ST_WRTDATA_SELECT_SECTOR),
            ST_WRTDATA_SELECT_SECTOR : (None, self.write_sector_parameter, None, ST_WRTDATA_SET_BYTES_PER_SECTOR),
            ST_WRTDATA_SET_BYTES_PER_SECTOR : (None, self.write_bytes_per_sector_parameter, None, ST_WRTDATA_SET_END_OF_TRACK),
            ST_WRTDATA_SET_END_OF_TRACK : (None, self.write_end_of_track_parameter, None, ST_WRTDATA_SET_GAP_LENGTH),
            ST_WRTDATA_SET_GAP_LENGTH : (None, self.write_gap_length_parameter, None, ST_WRTDATA_SET_DATA_LENGTH),
            ST_WRTDATA_SET_DATA_LENGTH : (None, self.write_data_length_parameter, None, ST_WRTDATA_BEGIN_EXECUTION),
            ST_WRTDATA_BEGIN_EXECUTION : (None, None, self.begin_write_data, ST_WRTDATA_IN_PROGRESS),
            ST_WRTDATA_IN_PROGRESS : (None, self.write_data, None, ST_WRTDATA_IN_PROGRESS),
            ST_WRTDATA_READ_STATUS_REG_0 : (self.read_status_register_0, None, None, ST_READY),
            
        }
        
        self.drive_select = 0
        self.head_select = 0
        
        self.parameters = CommandParameters()
        
        self.dma_enable = False
        
        self.interrupt_code = SR0_INT_CODE_NORMAL
        
        self.drives = [None, None, None, None]
        
        self.buffer = []
        self.cursor = 0
        
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
        # log.debug("READ from state 0x%04x", self.state)
        read_function, write_function, execute_function, self.state = self.states[self.state]
        if read_function:
            return read_function()
        else:
            log.warning("Attempted to READ a WRITE-ONLY state (0x%04x), you get 0x00.", self.state)
            return 0x00
            
    def write_toplevel_command(self, value):
        """ Kicks off a top-level FDC command, overwrites state. """
        # The top 3 bits of the command are used as flags.
        self.parameters.multi_track = value & COMMAND_MULTITRACK_MASK == COMMAND_MULTITRACK_MASK
        self.parameters.mfm = value & COMMAND_MFM_MASK == COMMAND_MFM_MASK
        self.parameters.skip_deleted = value & COMMAND_SKIP_MASK == COMMAND_SKIP_MASK
        
        if value == COMMAND_SENSE_INTERRUPT_STATUS:
            self.state = ST_SIS_READ_STATUS_REG_0
        elif value == COMMAND_RECALIBRATE:
            self.state = ST_RECAL_SELECT_DRIVE
        elif value == COMMAND_SPECIFY:
            self.state = ST_SPEC_HEAD_UNLOAD_STEP_RATE
        elif value == COMMAND_SEEK:
            self.state = ST_SEEK_SELECT_DRIVE_HEAD
        elif value == COMMAND_SENSE_DRIVE_STATUS:
            self.state = ST_SDS_SELECT_DRIVE_HEAD
        elif value & COMMAND_OPCODE_MASK == COMMAND_READ_DATA:
            self.state = ST_RDDATA_SELECT_DRIVE_HEAD
        elif value & COMMAND_OPCODE_MASK == COMMAND_WRITE_DATA:
            self.state = ST_WRTDATA_SELECT_DRIVE_HEAD
        else:
            log.warning("Invalid command: 0x%02x", value)
            
            # For now, stop in the debugger when we hit an invalid command.
            if self.bus:
                self.bus.force_debugger_break("Invalid FDC command: 0x%02x" % value)
                
    def read_status_register_0(self):
        """ Builds a status register 0 response. """
        # Start with unit select and last interrupt code (and not ready/seek end).
        value = self.drive_select | self.interrupt_code
        if self.head_select == 1:
            value |= SR0_HEAD_SELECT
            
        return value
        
    def read_status_register_1(self):
        """ Builds a status register 1 response. """
        # TODO: Implement this.
        return 0x00
        
    def read_status_register_2(self):
        """ Builds a status register 2 response. """
        # TODO: Implement this.
        return 0x00
        
    def read_status_register_3(self):
        """ Builds a status register 3 response. """
        value = self.drive_select
        if self.head_select == 1:
            value |= SR3_HEAD_SELECT
            
        drive = self.drives[self.drive_select]
        if drive:
            if drive.present_cylinder_number == 0:
                value |= SR3_TRACK_ZERO
            if drive.write_protect:
                value |= SR3_WRITE_PROTECT
                
        # TODO: FAULT, READY, TWO SIDE?
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
            
    def write_cylinder_parameter(self, value):
        """ Writes the cylinder parameter to the command buffer. """
        self.parameters.cylinder = value
        
    def write_head_parameter(self, value):
        """ Writes the head parameter to the command buffer. """
        self.parameters.head = value
        
    def write_sector_parameter(self, value):
        """ Writes the sector parameter to the command buffer. """
        self.parameters.sector = value
        
    def write_bytes_per_sector_parameter(self, value):
        """ Writes the bytes per sector parameter to the command buffer. """
        self.parameters.bytes_per_sector = 128 << value
        
    def write_end_of_track_parameter(self, value):
        """ Writes the end of track parameter to the command buffer. """
        self.parameters.end_of_track = value
        
    def write_gap_length_parameter(self, value):
        """ Writes the gap length parameter to the command buffer. """
        self.parameters.gap_length = value
        
    def write_data_length_parameter(self, value):
        """ Writes the data length parameter to the command buffer. """
        self.parameters.data_length = value
        
    def begin_read_data(self, continuation = False):
        """ Reads data from the diskette and writes it out via DMA/interrupts. """
        # self.bus.force_debugger_break("BEGIN READ DATA")
        # log.critical(self.parameters.dump())
        
        # TODO: Read the requested data into the buffer.
        drive = self.drives[self.drive_select]
        if drive:
            self.buffer = drive.read(self.parameters)
            self.cursor = 0
            
            # If no data is available and we get to this state, we must not have a diskette in the drive.
            # Throw an interrupt and get out.
            if len(self.buffer) == 0:
                self.signal_interrupt(SR0_INT_CODE_ABNORMAL | SR0_NOT_READY)
                self.state = ST_RDDATA_READ_STATUS_REG_0
                return
                
        # Do not setup DMA if this is a continuation of a previous read.
        if continuation:
            return
            
        # Signal the DMA request or trigger an interrupt so data can be read by the CPU.
        if self.dma_enable:
            self.bus.dma_request(FDC_DMA_CHANNEL, self.base + FDC_DATA, self.terminal_count)
        else:
            self.signal_interrupt(SR0_INT_CODE_NORMAL)
            
    def read_data(self):
        """ Called when a byte is read from the internal buffer. """
        # log.debug("read_data, cursor = %d, len(buffer) = %d", self.cursor, len(self.buffer))
        byte = self.buffer[self.cursor]
        self.cursor += 1
        
        # If we reached the end of the current buffer, prime the buffer for the next sector.
        if self.cursor == len(self.buffer):
            log.debug("Read data complete!")
            self.parameters.next_sector()
            self.begin_read_data(continuation = True)
            
        # We need to signal the interrupt for every byte in non-DMA mode.
        if not self.dma_enable:
            self.signal_interrupt(SR0_INT_CODE_NORMAL)
            
        return byte
        
    def terminal_count(self):
        """ Called when the FDC DMA channel reaches terminal count. """
        if self.state == ST_RDDATA_IN_PROGRESS:
            self.state = ST_RDDATA_READ_STATUS_REG_0
        elif self.state == ST_WRTDATA_IN_PROGRESS:
            self.state = ST_WRTDATA_READ_STATUS_REG_0
        else:
            raise RuntimeError("Terminal count signaled in state: 0x%04x" % self.state)
            
        self.signal_interrupt(SR0_INT_CODE_NORMAL)
        
    def begin_write_data(self, continuation = False):
        """ Writes data to the diskette from data via DMA/interrupts. """
        # self.bus.force_debugger_break("BEGIN WRITE DATA")
        # log.critical(self.parameters.dump())
        
        # Allocate a buffer for the write data.
        drive = self.drives[self.drive_select]
        if drive:
            _unused, length = calculate_parameters(drive.drive_info, self.parameters)
            self.buffer = array.array("B", (0,) * length)
            self.cursor = 0
            
            # If we don't have a diskette present, throw an interrupt and get out.
            if drive.write_protect or not drive.diskette_present:
                self.signal_interrupt(SR0_INT_CODE_ABNORMAL | SR0_NOT_READY)
                self.state = ST_WRTDATA_READ_STATUS_REG_0
                return
                
        # Do not setup DMA if this is a continuation of a previous write.
        if continuation:
            return
            
        # Signal the DMA request or trigger an interrupt so data can be written by the CPU.
        if self.dma_enable:
            self.bus.dma_request(FDC_DMA_CHANNEL, self.base + FDC_DATA, self.terminal_count)
        else:
            self.signal_interrupt(SR0_INT_CODE_NORMAL)
            
    def write_data(self, value):
        """ Called when a byte is written to the controller. """
        # log.debug("write_data, cursor = %d, len(buffer) = %d", self.cursor, len(self.buffer))
        self.buffer[self.cursor] = value
        self.cursor += 1
        
        # If we reached the end of the current buffer, prime the buffer for the next sector.
        if self.cursor == len(self.buffer):
            log.debug("write data complete!")
            drive = self.drives[self.drive_select]
            if drive:
                drive.write(self.parameters, self.buffer)
                drive.store_diskette()
                
            self.parameters.next_sector()
            self.begin_write_data(continuation = True)
            
        # We need to signal the interrupt for every byte in non-DMA mode.
        if not self.dma_enable:
            self.signal_interrupt(SR0_INT_CODE_NORMAL)
            
class FloppyDisketteDrive(object):
    """ Maintains the "physical state" of an attached diskette drive. """
    def __init__(self, drive_info):
        self.drive_info = drive_info
        
        self.present_cylinder_number = 0
        self.target_cylinder_number = 0
        self.contents = None
        self.write_protect = False
        self.filename = None
        
    @property
    def size_in_bytes(self):
        """ Returns the diskette size in bytes based on the drive geometry. """
        return (self.drive_info.bytes_per_sector * self.drive_info.sectors_per_track *
                self.drive_info.tracks_per_side * self.drive_info.sides)
                
    @property
    def diskette_present(self):
        """ Returns True if a diskette is present in the drive. """
        return self.contents is not None
        
    def load_diskette(self, filename, write_protect = False):
        """ Load a diskette image, "ejecting" a previous one if present. """
        log.info("Loading diskette from: %s", filename)
        self.contents = None
        self.write_protect = write_protect
        self.filename = filename
        
        if self.filename is not None:
            self.contents = array.array("B", (0,) * self.size_in_bytes)
            with open(self.filename, "rb") as fileptr:
                data = fileptr.read()
                
                if len(data) > self.size_in_bytes:
                    raise ValueError("Disk image (%d byte) is larger than supported by the drive (%d bytes)!" % (
                        len(data), self.size_in_bytes,
                    ))
                    
            for index, byte in enumerate(six.iterbytes(data)):
                self.contents[index] = byte
                
    def store_diskette(self):
        """ Write the content of the virtual diskette back to an image file. """
        log.info("Writing diskette to: %s", self.filename)
        
        if self.write_protect:
            raise RuntimeError("Writing to a write-protected disk is forbidden!")
            
        if self.contents is not None and self.filename is not None:
            with open(self.filename, "wb") as fileptr:
                self.contents.tofile(fileptr)
                
    def read(self, parms):
        """ Perform a diskette "read" operation based on the given parameters. """
        offset, length = calculate_parameters(self.drive_info, parms)
        if self.contents:
            # log.debug("Reading from image file, offset = %d, length = %d", offset, length)
            return self.contents[offset : offset + length]
        else:
            return array.array("B")
            
    def write(self, parms, buffer):
        """ Perform a diskette "write" operation based on the given parameters. """
        offset, length = calculate_parameters(self.drive_info, parms)
        assert length == len(buffer)
        if self.contents:
            for index in range(length):
                self.contents[index + offset] = buffer[index]
                
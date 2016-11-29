import unittest

import array

from pyxt.tests.utils import SystemBusTestable, get_test_file
from pyxt.fdc import *

class HelperTests(unittest.TestCase):
    def test_chs_to_lba(self):
        test_data = (
            # C, H, S, LBA
            (0, 0, 1, 0), # First sector on a 360KB diskette.
            (0, 0, 2, 1),
            (0, 1, 1, 9),
            (1, 0, 1, 18),
            (39, 1, 9, 719), # Last sector on a 360KB diskette.
        )
        for (c, h, s, lba) in test_data:
            self.assertEqual(chs_to_lba(FIVE_INCH_360_KB, c, h, s), lba)
            
    def test_chs_to_lba_invalid(self):
        with self.assertRaises(ValueError):
            chs_to_lba(FIVE_INCH_360_KB, 0, 0, 0)
            
    def test_calculate_parameters_one_sector(self):
        # First row in the data sheet.
        parms = CommandParameters()
        parms.multi_track = False
        parms.mfm = False
        parms.bytes_per_sector = 128
        parms.cylinder = 0
        parms.head = 0
        parms.sector = 1
        parms.end_of_track = 1
        drive_info = DriveInfo(128, 26, 0, 2)
        self.assertEqual(calculate_parameters(drive_info, parms), (0, 128))
        
    def test_calculate_next_sector(self):
        # Assume 9 cylinders per track.
        test_data = [
            # multi_track, cylinder, head, sector, new_cylinder, new_head, new_sector
            (False, 1, 0, 1, 1, 0, 2), # Next sector.
            (False, 1, 0, 9, 2, 0, 1), # Last sector, next cylinder.
            (False, 1, 1, 1, 1, 1, 2), # Next sector.
            (False, 1, 1, 9, 2, 1, 1), # Last sector, next cylinder.
            (True, 1, 0, 1, 1, 0, 2), # Next sector.
            (True, 1, 0, 9, 1, 1, 1), # Last sector, next head.
            (True, 1, 1, 1, 1, 1, 2), # Next sector.
            (True, 1, 1, 9, 2, 0, 1), # Last sector, next cylinder.
        ]
        for multi_track, cylinder, head, sector, new_cylinder, new_head, new_sector in test_data:
            # print multi_track, cylinder, head, sector, new_cylinder, new_head, new_sector
            parms = CommandParameters()
            parms.multi_track = multi_track
            parms.cylinder = cylinder
            parms.head = head
            parms.sector = sector
            parms.end_of_track = 9
            parms.next_sector()
            
            self.assertEqual(parms.cylinder, new_cylinder)
            self.assertEqual(parms.head, new_head)
            self.assertEqual(parms.sector, new_sector)
            
class FDCTests(unittest.TestCase):
    def setUp(self):
        self.fdc = FloppyDisketteController(0x3F0)
        
        self.bus = SystemBusTestable()
        self.bus.install_device(None, self.fdc)
        
        self.reset_called = False
        
    def test_address_list(self):
        self.assertEqual(self.fdc.get_ports_list(), [0x3F2, 0x3F4, 0x3F5])
        
    def test_initial_state(self):
        self.assertFalse(self.fdc.enabled)
        self.assertFalse(self.fdc.dma_enable)
        self.assertEqual(self.fdc.state, ST_READY)
        self.assertEqual(self.fdc.drive_select, 0)
        self.assertEqual(self.fdc.head_select, 0)
        self.assertIsNotNone(self.fdc.parameters)
        self.assertEqual(self.fdc.interrupt_code, 0)
        self.assertEqual(self.fdc.drives, [None, None, None, None])
        
    def test_reset(self):
        self.fdc.state = 5643
        self.fdc.dma_enable = True
        self.fdc.reset()
        self.assertFalse(self.fdc.dma_enable)
        self.assertEqual(self.fdc.state, ST_READY)
        self.assertEqual(self.fdc.interrupt_code, SR0_INT_CODE_READY_CHANGE)
        self.assertEqual(self.bus.get_irq_log(), [6])
        
    def test_enable_fdc(self):
        self.fdc.io_write_byte(0x3F2, 0x04)
        self.assertTrue(self.fdc.enabled)
        
    def _reset_hook(self):
        self.reset_called = True
        
    def test_enabling_fdc_calls_reset(self):
        self.fdc.reset = self._reset_hook
        
        self.fdc.io_write_byte(0x3F2, 0x04)
        self.assertTrue(self.reset_called)
        
    def test_reset_not_called_if_already_enabled(self):
        self.fdc.reset = self._reset_hook
        
        self.fdc.enabled = True
        self.fdc.io_write_byte(0x3F2, 0x04)
        self.assertFalse(self.reset_called)
        
    # Main status register tests.
    def test_main_status_register_in_reset(self):
        self.assertEqual(self.fdc.io_read_byte(0x3F4), 0x00)
        
    def test_main_status_register_after_reset(self):
        self.fdc.io_write_byte(0x3F2, 0x04)
        self.assertEqual(self.fdc.io_read_byte(0x3F4), 0x80)
        
    def test_main_status_busy_command_in_progress(self):
        self.fdc.enabled = True
        self.fdc.state = ST_SIS_READ_STATUS_REG_0
        self.assertEqual(self.fdc.io_read_byte(0x3F4), 0xD0)
        
    # Read/write helper tests.
    def test_read_status_register_0(self):
        self.fdc.drive_select = 2
        self.fdc.head_select = 1
        self.assertEqual(self.fdc.read_status_register_0(), 0x06)
        
    def test_read_present_cylinder_number_valid(self):
        drive = FloppyDisketteDrive(FIVE_INCH_360_KB)
        drive.present_cylinder_number = 33
        self.fdc.attach_drive(drive, 0)
        self.assertEqual(self.fdc.read_present_cylinder_number(), 33)
        
    def test_read_present_cylinder_number_invalid(self):
        self.fdc.drive_select = 2
        self.assertEqual(self.fdc.read_present_cylinder_number(), 0)
        
    def test_write_drive_head_select(self):
        self.fdc.write_drive_head_select(0x07)
        self.assertEqual(self.fdc.drive_select, 3)
        self.assertEqual(self.fdc.head_select, 1)
        
    def test_recalibrate(self):
        drive0 = FloppyDisketteDrive(FIVE_INCH_360_KB)
        drive0.present_cylinder_number = 33
        self.fdc.attach_drive(drive0, 0)
        drive1 = FloppyDisketteDrive(FIVE_INCH_360_KB)
        drive1.present_cylinder_number = 34
        self.fdc.attach_drive(drive1, 1)
        
        self.fdc.drive_select = 1
        self.fdc.recalibrate()
        
        self.assertEqual(self.bus.get_irq_log(), [6])
        self.assertEqual(self.fdc.interrupt_code, 0x20) # Normal termination, seek end.
        self.assertEqual(drive0.present_cylinder_number, 33)
        self.assertEqual(drive1.present_cylinder_number, 0)
        
    def test_write_new_cylinder_number(self):
        drive = FloppyDisketteDrive(FIVE_INCH_360_KB)
        drive.present_cylinder_number = 33
        self.fdc.attach_drive(drive, 0)
        self.fdc.write_new_cylinder_number(20)
        self.assertEqual(drive.target_cylinder_number, 20)
        
    def test_seek_valid(self):
        drive = FloppyDisketteDrive(FIVE_INCH_360_KB)
        drive.present_cylinder_number = 33
        drive.target_cylinder_number = 34
        self.fdc.attach_drive(drive, 0)
        self.fdc.drive_select = 0
        self.fdc.head_select = 0
        
        self.fdc.seek()
        
        self.assertEqual(drive.present_cylinder_number, 34)
        self.assertEqual(self.bus.get_irq_log(), [6])
        self.assertEqual(self.fdc.interrupt_code, 0x20) # Normal termination, seek end.
        
    def test_seek_invalid(self):
        drive = FloppyDisketteDrive(FIVE_INCH_360_KB)
        drive.present_cylinder_number = 33
        drive.target_cylinder_number = 60
        self.fdc.attach_drive(drive, 0)
        self.fdc.drive_select = 0
        self.fdc.head_select = 0
        
        self.fdc.seek()
        
        self.assertEqual(drive.present_cylinder_number, 33)
        self.assertEqual(self.bus.get_irq_log(), [6])
        self.assertEqual(self.fdc.interrupt_code, 0x60) # Abnormal termination, seek end.
        
    def test_write_cylinder_parameter(self):
        self.fdc.write_cylinder_parameter(22)
        self.assertEqual(self.fdc.parameters.cylinder, 22)
        
    def test_write_head_parameter(self):
        self.fdc.write_head_parameter(1)
        self.assertEqual(self.fdc.parameters.head, 1)
        
    def test_write_sector_parameter(self):
        self.fdc.write_sector_parameter(4)
        self.assertEqual(self.fdc.parameters.sector, 4)
        
    def test_write_bytes_per_sector_parameter(self):
        self.fdc.write_bytes_per_sector_parameter(0)
        self.assertEqual(self.fdc.parameters.bytes_per_sector, 128)
        self.fdc.write_bytes_per_sector_parameter(1)
        self.assertEqual(self.fdc.parameters.bytes_per_sector, 256)
        self.fdc.write_bytes_per_sector_parameter(2)
        self.assertEqual(self.fdc.parameters.bytes_per_sector, 512)
        self.fdc.write_bytes_per_sector_parameter(3)
        self.assertEqual(self.fdc.parameters.bytes_per_sector, 1024)
        self.fdc.write_bytes_per_sector_parameter(4)
        self.assertEqual(self.fdc.parameters.bytes_per_sector, 2048)
        # And so on...
        
    def test_write_end_of_track_parameter(self):
        self.fdc.write_end_of_track_parameter(512)
        self.assertEqual(self.fdc.parameters.end_of_track, 512)
        
    def test_write_gap_length_parameter(self):
        self.fdc.write_gap_length_parameter(27)
        self.assertEqual(self.fdc.parameters.gap_length, 27)
        
    def test_write_data_length_parameter(self):
        self.fdc.write_data_length_parameter(32)
        self.assertEqual(self.fdc.parameters.data_length, 32)
        
    def test_read_status_register_3_unit_select(self):
        self.fdc.drive_select = 2
        self.fdc.head_select = 1
        self.assertEqual(self.fdc.read_status_register_3(), 0x06)
        
    def test_read_status_register_3_track_0(self):
        drive = FloppyDisketteDrive(FIVE_INCH_360_KB)
        drive.present_cylinder_number = 1
        self.fdc.attach_drive(drive, 0)
        self.fdc.drive_select = 0
        self.fdc.head_select = 0
        self.assertEqual(self.fdc.read_status_register_3(), 0x00)
        
        drive.present_cylinder_number = 0
        self.assertEqual(self.fdc.read_status_register_3(), 0x10)
        
    def test_read_status_register_3_write_protect(self):
        drive = FloppyDisketteDrive(FIVE_INCH_360_KB)
        drive.present_cylinder_number = 1
        self.fdc.attach_drive(drive, 0)
        self.fdc.drive_select = 0
        self.fdc.head_select = 0
        drive.write_protect = False
        self.assertEqual(self.fdc.read_status_register_3(), 0x00)
        
        drive.write_protect = True
        self.assertEqual(self.fdc.read_status_register_3(), 0x40)
        
    def test_terminal_count_read_data(self):
        self.fdc.state = ST_RDDATA_IN_PROGRESS
        self.fdc.terminal_count()
        self.assertEqual(self.fdc.state, ST_RDDATA_READ_STATUS_REG_0)
        self.assertEqual(self.bus.get_irq_log(), [6])
        self.assertEqual(self.fdc.interrupt_code, SR0_INT_CODE_NORMAL)
        
    def test_terminal_count_write_data(self):
        self.fdc.state = ST_WRTDATA_IN_PROGRESS
        self.fdc.terminal_count()
        self.assertEqual(self.fdc.state, ST_WRTDATA_READ_STATUS_REG_0)
        self.assertEqual(self.bus.get_irq_log(), [6])
        self.assertEqual(self.fdc.interrupt_code, SR0_INT_CODE_NORMAL)
        
    def test_terminal_count_other_raises_error(self):
        self.fdc.state = ST_READY
        with self.assertRaises(RuntimeError):
            self.fdc.terminal_count()
            
    def test_begin_write_data_normal(self):
        drive = FloppyDisketteDrive(FIVE_INCH_360_KB)
        drive.present_cylinder_number = 1
        test_file = get_test_file(self, "diskette.img")
        drive.load_diskette(test_file)
        self.fdc.attach_drive(drive, 0)
        self.fdc.drive_select = 0
        self.fdc.head_select = 0
        self.fdc.cursor = 511 # Non-zero for test.
        self.fdc.state = 5643 # Not relevant.
        
        self.fdc.begin_write_data()
        
        self.assertEqual(self.fdc.cursor, 0)
        self.assertEqual(len(self.fdc.buffer), 512)
        
        self.assertEqual(self.bus.get_irq_log(), [6]) # Non-DMA.
        self.assertEqual(self.fdc.interrupt_code, SR0_INT_CODE_NORMAL) # Non-DMA.
        
        self.assertEqual(self.fdc.state, 5643) # Should be unmodified, caller will advance state.
        
    def test_begin_write_data_continuation(self):
        drive = FloppyDisketteDrive(FIVE_INCH_360_KB)
        drive.present_cylinder_number = 1
        test_file = get_test_file(self, "diskette.img")
        drive.load_diskette(test_file)
        self.fdc.attach_drive(drive, 0)
        self.fdc.drive_select = 0
        self.fdc.head_select = 0
        self.fdc.cursor = 511 # Non-zero for test.
        self.fdc.state = 5643 # Not relevant.
        
        self.fdc.begin_write_data(continuation = True)
        
        self.assertEqual(self.fdc.cursor, 0)
        self.assertEqual(len(self.fdc.buffer), 512)
        # No DMA setup or interrupt for continuation (it's really the same write).
        self.assertEqual(self.bus.get_irq_log(), []) # Non-DMA.
        
        self.assertEqual(self.fdc.state, 5643) # Should be unmodified, caller will advance state.
        
    def test_begin_write_data_write_protect(self):
        drive = FloppyDisketteDrive(FIVE_INCH_360_KB)
        drive.present_cylinder_number = 1
        test_file = get_test_file(self, "diskette.img")
        drive.load_diskette(test_file, write_protect = True)
        self.fdc.attach_drive(drive, 0)
        self.fdc.drive_select = 0
        self.fdc.head_select = 0
        self.fdc.cursor = 511 # Non-zero for test.
        
        self.fdc.begin_write_data()
        
        self.assertEqual(self.bus.get_irq_log(), [6])
        self.assertEqual(self.fdc.interrupt_code, SR0_INT_CODE_ABNORMAL | SR0_NOT_READY)
        
        self.assertEqual(self.fdc.state, ST_WRTDATA_READ_STATUS_REG_0)
        
    def test_begin_write_data_no_diskette(self):
        drive = FloppyDisketteDrive(FIVE_INCH_360_KB)
        drive.present_cylinder_number = 1
        self.fdc.attach_drive(drive, 0)
        self.fdc.drive_select = 0
        self.fdc.head_select = 0
        self.fdc.cursor = 511 # Non-zero for test.
        
        self.fdc.begin_write_data()
        
        self.assertEqual(self.bus.get_irq_log(), [6])
        self.assertEqual(self.fdc.interrupt_code, SR0_INT_CODE_ABNORMAL | SR0_NOT_READY)
        
        self.assertEqual(self.fdc.state, ST_WRTDATA_READ_STATUS_REG_0)
        
class FDDTests(unittest.TestCase):
    def setUp(self):
        self.fdd = FloppyDisketteDrive(FIVE_INCH_360_KB)
        
    def test_initial_state(self):
        self.assertEqual(self.fdd.drive_info.bytes_per_sector, 512)
        self.assertEqual(self.fdd.drive_info.sectors_per_track, 9)
        self.assertEqual(self.fdd.drive_info.tracks_per_side, 40)
        self.assertEqual(self.fdd.drive_info.sides, 2)
        
        self.assertEqual(self.fdd.present_cylinder_number, 0)
        self.assertEqual(self.fdd.target_cylinder_number, 0)
        self.assertIsNone(self.fdd.contents)
        self.assertFalse(self.fdd.write_protect)
        self.assertIsNone(self.fdd.filename)
        
        self.assertFalse(self.fdd.diskette_present)
        
    def test_size_in_bytes(self):
        self.assertEqual(self.fdd.size_in_bytes, 368640)
        
    def test_load_diskette(self):
        test_file = get_test_file(self, "diskette.img")
        self.fdd.load_diskette(test_file)
        self.assertEqual(self.fdd.contents[0], 0x64)
        self.assertEqual(len(self.fdd.contents), 368640) # Ensure it is padded to the full size.
        self.assertTrue("diskette.img" in self.fdd.filename)
        self.assertTrue(self.fdd.diskette_present)
        
        self.fdd.load_diskette(None)
        self.assertIsNone(self.fdd.contents)
        self.assertIsNone(self.fdd.filename)
        self.assertFalse(self.fdd.diskette_present)
        
    def test_load_diskette_write_protect(self):
        test_file = get_test_file(self, "diskette.img")
        self.fdd.load_diskette(test_file, write_protect = True)
        self.assertEqual(self.fdd.contents[0], 0x64)
        self.assertTrue(self.fdd.write_protect)
        
    def test_load_diskette_too_big(self):
        test_fdd = FloppyDisketteDrive(DriveInfo(5, 1, 1, 2)) # As much data as I can count on my hands.
        test_file = get_test_file(self, "diskette.img")
        with self.assertRaises(ValueError):
            test_fdd.load_diskette(test_file)
            
class FloppyDisketteDriveTestable(FloppyDisketteDrive):
    """ Testable drive that doesn't actually write back to "disk". """
    def __init__(self, drive_info):
        super(FloppyDisketteDriveTestable, self).__init__(drive_info)
        self.last_stored_data = []
        
    def store_diskette(self):
        # Use tolist to avoid deprecation warning on tostring() in Py3k
        # and lack of tobytes() in 2.7.
        self.last_stored_data = self.contents.tolist()
       
class FDCAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.fdc = FloppyDisketteController(0x3F0)
        self.fdd0 = FloppyDisketteDriveTestable(FIVE_INCH_360_KB)
        
        self.fdc.attach_drive(self.fdd0, 0)
        self.fdd1 = FloppyDisketteDriveTestable(FIVE_INCH_360_KB)
        self.fdc.attach_drive(self.fdd1, 1)
        
        self.bus = SystemBusTestable()
        self.bus.install_device(None, self.fdc)
        
    def install_test_data_diskette(self, fdd):
        fdd.contents = array.array("B", (0xAA, 0x55, 0xCA, 0xFE,) * (368640 // 4))
        
    def install_test_blank_diskette(self, fdd):
        fdd.contents = array.array("B", (0,) * 368640)
        
    def test_command_sense_interrupt_status(self):
        self.fdd0.present_cylinder_number = 27
        
        self.fdc.io_write_byte(0x3F5, 0x08) # Sense interrupt status.
        self.assertEqual(self.fdc.state, ST_SIS_READ_STATUS_REG_0)
        
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 0x00) # Status register 0.
        self.assertEqual(self.fdc.state, ST_SIS_READ_PRESENT_CYLINDER)
        
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 27) # Present cylinder.
        self.assertEqual(self.fdc.state, ST_READY)
        
    def test_recalibrate(self):
        self.fdd0.present_cylinder_number = 27
        self.fdd1.present_cylinder_number = 33
        
        self.fdc.io_write_byte(0x3F5, 0x07) # Recalibrate.
        self.assertEqual(self.fdc.state, ST_RECAL_SELECT_DRIVE)
        
        self.fdc.io_write_byte(0x3F5, 0x01) # Select drive 1.
        self.assertEqual(self.fdc.state, ST_READY)
        
        self.assertEqual(self.fdd1.present_cylinder_number, 0)
        
    def test_specify_non_dma(self):
        self.fdc.io_write_byte(0x3F5, 0x03) # Specify.
        self.assertEqual(self.fdc.state, ST_SPEC_HEAD_UNLOAD_STEP_RATE)
        
        self.fdc.io_write_byte(0x3F5, 0xA5) # Head unload/step time.
        self.assertEqual(self.fdc.state, ST_SPEC_HEAD_LOAD_NON_DMA)
        
        self.fdc.io_write_byte(0x3F5, 0x01) # Head load time/dma mode select.
        self.assertEqual(self.fdc.state, ST_READY)
        
        self.assertFalse(self.fdc.dma_enable)
        
    def test_specify_enable_dma(self):
        self.fdc.io_write_byte(0x3F5, 0x03) # Specify.
        self.assertEqual(self.fdc.state, ST_SPEC_HEAD_UNLOAD_STEP_RATE)
        
        self.fdc.io_write_byte(0x3F5, 0xA5) # Head unload/step time.
        self.assertEqual(self.fdc.state, ST_SPEC_HEAD_LOAD_NON_DMA)
        
        self.fdc.io_write_byte(0x3F5, 0x00) # Head load time/dma mode select.
        self.assertEqual(self.fdc.state, ST_READY)
        
        self.assertTrue(self.fdc.dma_enable)
        
    def test_seek(self):
        self.fdc.io_write_byte(0x3F5, 0x0F) # Seek.
        self.assertEqual(self.fdc.state, ST_SEEK_SELECT_DRIVE_HEAD)
        
        self.fdc.io_write_byte(0x3F5, 0x00) # Select drive 0.
        self.assertEqual(self.fdc.state, ST_SEEK_WRITE_NEW_CYLINDER)
        
        self.fdc.io_write_byte(0x3F5, 20) # Select cylinder 20
        self.assertEqual(self.fdc.state, ST_READY)
        
        self.assertTrue(self.fdd0.present_cylinder_number, 20)
        
    def test_read_data_parse_parameters(self):
        # If there is no diskette in the drive, the read will fail.
        self.install_test_data_diskette(self.fdd1)
        
        self.fdc.io_write_byte(0x3F5, 0xE6) # Read data.
        
        self.assertEqual(self.fdc.state, ST_RDDATA_SELECT_DRIVE_HEAD)
        self.assertTrue(self.fdc.parameters.multi_track)
        self.assertTrue(self.fdc.parameters.mfm)
        self.assertTrue(self.fdc.parameters.skip_deleted)
        
        self.fdc.io_write_byte(0x3F5, 0x05) # Select drive 1, head 1.
        
        self.assertEqual(self.fdc.state, ST_RDDATA_SELECT_CYLINDER)
        self.assertTrue(self.fdc.drive_select, 1)
        self.assertTrue(self.fdc.head_select, 1)
        
        self.fdc.io_write_byte(0x3F5, 20) # Select cylinder 20.
        
        self.assertEqual(self.fdc.state, ST_RDDATA_SELECT_HEAD)
        self.assertEqual(self.fdc.parameters.cylinder, 20)
        
        self.fdc.io_write_byte(0x3F5, 1) # Select head 1.
        
        self.assertEqual(self.fdc.state, ST_RDDATA_SELECT_SECTOR)
        self.assertEqual(self.fdc.parameters.head, 1)
        
        self.fdc.io_write_byte(0x3F5, 5) # Select sector 5.
        
        self.assertEqual(self.fdc.state, ST_RDDATA_SET_BYTES_PER_SECTOR)
        self.assertEqual(self.fdc.parameters.sector, 5)
        
        self.fdc.io_write_byte(0x3F5, 2) # 512 bytes per sector.
        
        self.assertEqual(self.fdc.state, ST_RDDATA_SET_END_OF_TRACK)
        self.assertEqual(self.fdc.parameters.bytes_per_sector, 512)
        
        self.fdc.io_write_byte(0x3F5, 8) # Last sector number in cylinder.
        
        self.assertEqual(self.fdc.state, ST_RDDATA_SET_GAP_LENGTH)
        self.assertEqual(self.fdc.parameters.end_of_track, 8)
        
        self.fdc.io_write_byte(0x3F5, 33) # Gap length 33
        
        self.assertEqual(self.fdc.state, ST_RDDATA_SET_DATA_LENGTH)
        self.assertEqual(self.fdc.parameters.gap_length, 33)
        
        self.assertEqual(self.bus.get_irq_log(), []) # Should be no interrupts yet.
        
        self.fdc.io_write_byte(0x3F5, 64) # Data length 64.
        
        self.assertEqual(self.fdc.state, ST_RDDATA_IN_PROGRESS)
        self.assertEqual(self.fdc.parameters.data_length, 64)
        self.assertEqual(self.bus.get_irq_log(), [6]) # Since this is non-DMA mode, we get an interrupt here.
        
    def test_read_data_reading(self):
        self.install_test_data_diskette(self.fdd0)
        
        parameters = (
            0xE6, # Read data, multitrack, mfm, skip deleted
            0x00, # Drive 0, head 0
            0x00, # Cylinder 0
            0x00, # Head 0
            0x01, # Sector 1 (they start at 1)
            0x02, # 512 bytes per sector
            0x09, # Read up to track 9.
            0x2A, # Gap length (not really applicable)
            0xFF, # Data length (unused if bytes per sector is non-zero?)
        )
        for byte in parameters:
            self.fdc.io_write_byte(0x3F5, byte)
            
        self.assertEqual(self.bus.get_irq_log(), [6]) # Byte was ready... IRQ!
        self.assertEqual(self.fdc.state, ST_RDDATA_IN_PROGRESS)
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 0xAA)
        
        self.assertEqual(self.bus.get_irq_log(), [6, 6]) # Another byte was ready... IRQ!
        self.assertEqual(self.fdc.state, ST_RDDATA_IN_PROGRESS)
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 0x55)
        
        # And so on...
        
        # Pretend we read all but ther last byte of the data.
        self.fdc.cursor = 511 # TODO: Was 9215, which is right?!
        self.assertEqual(self.bus.get_irq_log(), [6, 6, 6]) # Assume there would have been one for all bytes ready to have been read.
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 0xFE)
        
        # At this point if we have not reached terminal count, we should prepare the next sector.
        self.assertEqual(self.fdc.cursor, 0)
        self.assertEqual(self.bus.get_irq_log(), [6, 6, 6, 6]) # Byte was ready... IRQ!
        self.assertEqual(self.fdc.state, ST_RDDATA_IN_PROGRESS)
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 0xAA)
        
    def test_read_data_multiple_sectors(self):
        self.install_test_data_diskette(self.fdd0)
        
        parameters = (
            0xE6, # Read data, multitrack, mfm, skip deleted
            0x00, # Drive 0, head 0
            0x00, # Cylinder 0
            0x00, # Head 0
            0x01, # Sector 1 (they start at 1)
            0x02, # 512 bytes per sector
            0x09, # Read up to track 9.
            0x2A, # Gap length (not really applicable)
            0xFF, # Data length (unused if bytes per sector is non-zero?)
        )
        for byte in parameters:
            self.fdc.io_write_byte(0x3F5, byte)
            
        self.assertEqual(self.bus.get_irq_log(), [6]) # Byte was ready... IRQ!
        self.assertEqual(self.fdc.state, ST_RDDATA_IN_PROGRESS)
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 0xAA)
        
        self.assertEqual(self.bus.get_irq_log(), [6, 6]) # Another byte was ready... IRQ!
        self.assertEqual(self.fdc.state, ST_RDDATA_IN_PROGRESS)
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 0x55)
        
        # And so on...
        
        # Pretend we read all but ther last byte of the data.
        self.fdc.cursor = 511 # TODO: Was 9215, which is right?!
        self.assertEqual(self.bus.get_irq_log(), [6, 6, 6]) # Assume there would have been one for all bytes ready to have been read.
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 0xFE)
        
        self.fdc.terminal_count()
        
        self.assertEqual(self.fdc.state, ST_RDDATA_READ_STATUS_REG_0)
        
    def test_read_data_no_diskette(self):
        parameters = (
            0xE6, # Read data, multitrack, mfm, skip deleted
            0x00, # Drive 0, head 0
            0x00, # Cylinder 0
            0x00, # Head 0
            0x01, # Sector 1 (they start at 1)
            0x02, # 512 bytes per sector
            0x09, # Read up to track 9.
            0x2A, # Gap length (not really applicable)
            0xFF, # Data length (unused if bytes per sector is non-zero?)
        )
        for byte in parameters:
            self.fdc.io_write_byte(0x3F5, byte)
            
        self.assertEqual(self.bus.get_irq_log(), [6]) # Abnormal termination... IRQ!
        self.assertEqual(self.fdc.state, ST_RDDATA_READ_STATUS_REG_0)
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 0x48) # Abnormal exit, not ready.
        
    def test_sense_drive_status(self):
        self.fdc.io_write_byte(0x3F5, 0x04) # Sense drive status.
        self.assertEqual(self.fdc.state, ST_SDS_SELECT_DRIVE_HEAD)
        
        self.fdc.io_write_byte(0x3F5, 0x05) # Select drive 1, head 1.
        self.assertEqual(self.fdc.state, ST_SDS_READ_STATUS_REG_3)
        self.assertTrue(self.fdc.drive_select, 1)
        self.assertTrue(self.fdc.head_select, 1)
        
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 0x15) # Not write protected, track 0.
        self.assertEqual(self.fdc.state, ST_READY)
        
    def test_write_data_parse_parameters(self):
        # If there is no diskette in the drive, the write will fail.
        self.install_test_data_diskette(self.fdd1)
        
        self.fdc.io_write_byte(0x3F5, 0xC5) # Write data.
        
        self.assertEqual(self.fdc.state, ST_WRTDATA_SELECT_DRIVE_HEAD)
        self.assertTrue(self.fdc.parameters.multi_track)
        self.assertTrue(self.fdc.parameters.mfm)
        
        self.fdc.io_write_byte(0x3F5, 0x05) # Select drive 1, head 1.
        
        self.assertEqual(self.fdc.state, ST_WRTDATA_SELECT_CYLINDER)
        self.assertTrue(self.fdc.drive_select, 1)
        self.assertTrue(self.fdc.head_select, 1)
        
        self.fdc.io_write_byte(0x3F5, 20) # Select cylinder 20.
        
        self.assertEqual(self.fdc.state, ST_WRTDATA_SELECT_HEAD)
        self.assertEqual(self.fdc.parameters.cylinder, 20)
        
        self.fdc.io_write_byte(0x3F5, 1) # Select head 1.
        
        self.assertEqual(self.fdc.state, ST_WRTDATA_SELECT_SECTOR)
        self.assertEqual(self.fdc.parameters.head, 1)
        
        self.fdc.io_write_byte(0x3F5, 5) # Select sector 5.
        
        self.assertEqual(self.fdc.state, ST_WRTDATA_SET_BYTES_PER_SECTOR)
        self.assertEqual(self.fdc.parameters.sector, 5)
        
        self.fdc.io_write_byte(0x3F5, 2) # 512 bytes per sector.
        
        self.assertEqual(self.fdc.state, ST_WRTDATA_SET_END_OF_TRACK)
        self.assertEqual(self.fdc.parameters.bytes_per_sector, 512)
        
        self.fdc.io_write_byte(0x3F5, 8) # Last sector number in cylinder.
        
        self.assertEqual(self.fdc.state, ST_WRTDATA_SET_GAP_LENGTH)
        self.assertEqual(self.fdc.parameters.end_of_track, 8)
        
        self.fdc.io_write_byte(0x3F5, 33) # Gap length 33
        
        self.assertEqual(self.fdc.state, ST_WRTDATA_SET_DATA_LENGTH)
        self.assertEqual(self.fdc.parameters.gap_length, 33)
        
        self.assertEqual(self.bus.get_irq_log(), []) # Should be no interrupts yet.
        
        self.fdc.io_write_byte(0x3F5, 64) # Data length 64.
        
        self.assertEqual(self.fdc.state, ST_WRTDATA_IN_PROGRESS)
        self.assertEqual(self.fdc.parameters.data_length, 64)
        self.assertEqual(self.bus.get_irq_log(), [6]) # Since this is non-DMA mode, we get an interrupt here.
        
    def test_write_data_writing(self):
        self.install_test_blank_diskette(self.fdd0)
        
        parameters = (
            0xC5, # Write data, multitrack, mfm
            0x00, # Drive 0, head 0
            0x00, # Cylinder 0
            0x00, # Head 0
            0x01, # Sector 1 (they start at 1)
            0x02, # 512 bytes per sector
            0x09, # Write up to track 9.
            0x2A, # Gap length (not really applicable)
            0xFF, # Data length (unused if bytes per sector is non-zero?)
        )
        for byte in parameters:
            self.fdc.io_write_byte(0x3F5, byte)
            
        self.assertEqual(self.bus.get_irq_log(), [6]) # Ready for data from the host... IRQ!
        self.assertEqual(self.fdc.state, ST_WRTDATA_IN_PROGRESS)
        self.fdc.io_write_byte(0x3F5, 0xAA)
        
        self.assertEqual(self.bus.get_irq_log(), [6, 6]) # Another... IRQ!
        self.assertEqual(self.fdc.state, ST_WRTDATA_IN_PROGRESS)
        self.fdc.io_write_byte(0x3F5, 0x55)
        
        # And so on...
        
        self.assertEqual(len(self.fdd0.last_stored_data), 0) # Should not be written yet.
        
        # Pretend we wrote all but ther last byte of the data.
        self.fdc.cursor = 511
        self.assertEqual(self.bus.get_irq_log(), [6, 6, 6]) # Assume there would have been one for all bytes written.
        self.fdc.io_write_byte(0x3F5, 0xFE)
        
        self.assertEqual(len(self.fdd0.last_stored_data), 368640) # Should be written now.
        self.assertEqual(self.fdd0.last_stored_data[0], 0xAA)
        self.assertEqual(self.fdd0.last_stored_data[1], 0x55)
        self.assertEqual(self.fdd0.last_stored_data[511], 0xFE)
        
        # At this point if we have not reached terminal count, we should prepare the next sector.
        self.assertEqual(self.fdc.cursor, 0)
        self.assertEqual(self.bus.get_irq_log(), [6, 6, 6, 6]) # Ready for next byte... IRQ!
        self.assertEqual(self.fdc.state, ST_WRTDATA_IN_PROGRESS)
        
        # We could write more but if we get TC then exit the write state.
        self.fdc.terminal_count()
        self.assertEqual(self.bus.get_irq_log(), [6, 6, 6, 6, 6]) # It's over... IRQ!
        self.assertEqual(self.fdc.state, ST_WRTDATA_READ_STATUS_REG_0)
        
    def test_write_data_no_diskette(self):
        parameters = (
            0xC5, # Write data, multitrack, mfm
            0x00, # Drive 0, head 0
            0x00, # Cylinder 0
            0x00, # Head 0
            0x01, # Sector 1 (they start at 1)
            0x02, # 512 bytes per sector
            0x09, # Write up to track 9.
            0x2A, # Gap length (not really applicable)
            0xFF, # Data length (unused if bytes per sector is non-zero?)
        )
        for byte in parameters:
            self.fdc.io_write_byte(0x3F5, byte)
            
        self.assertEqual(self.bus.get_irq_log(), [6]) # Abnormal termination... IRQ!
        self.assertEqual(self.fdc.state, ST_WRTDATA_READ_STATUS_REG_0)
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 0x48) # Abnormal exit, not ready.
        
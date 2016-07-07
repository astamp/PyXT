import unittest

from pyxt.tests.utils import SystemBusTestable, get_test_file
from pyxt.fdc import *

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
        self.fdc.write_bytes_per_sector_parameter(64)
        self.assertEqual(self.fdc.parameters.bytes_per_sector, 64)
        
    def test_write_end_of_track_parameter(self):
        self.fdc.write_end_of_track_parameter(512)
        self.assertEqual(self.fdc.parameters.end_of_track, 512)
        
    def test_write_gap_length_parameter(self):
        self.fdc.write_gap_length_parameter(27)
        self.assertEqual(self.fdc.parameters.gap_length, 27)
        
    def test_write_data_length_parameter(self):
        self.fdc.write_data_length_parameter(32)
        self.assertEqual(self.fdc.parameters.data_length, 32)
        
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
        
    def test_size_in_bytes(self):
        self.assertEqual(self.fdd.size_in_bytes, 368640)
        
    def test_load_diskette(self):
        test_file = get_test_file(self, "diskette.img")
        self.fdd.load_diskette(test_file)
        self.assertEqual(self.fdd.contents[0], 0x64)
        self.assertEqual(len(self.fdd.contents), 368640) # Ensure it is padded to the full size.
        
        self.fdd.load_diskette(None)
        self.assertIsNone(self.fdd.contents)
        
    def test_load_diskette_too_big(self):
        test_fdd = FloppyDisketteDrive(DriveInfo(5, 1, 1, 2)) # As much data as I can count on my hands.
        test_file = get_test_file(self, "diskette.img")
        with self.assertRaises(ValueError):
            test_fdd.load_diskette(test_file)
            
class FDCAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.fdc = FloppyDisketteController(0x3F0)
        self.fdd0 = FloppyDisketteDrive(FIVE_INCH_360_KB)
        self.fdc.attach_drive(self.fdd0, 0)
        self.fdd1 = FloppyDisketteDrive(FIVE_INCH_360_KB)
        self.fdc.attach_drive(self.fdd1, 1)
        
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
        
    def test_read_data(self):
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
        
        self.fdc.io_write_byte(0x3F5, 512) # 512 bytes per sector.
        
        self.assertEqual(self.fdc.state, ST_RDDATA_SET_END_OF_TRACK)
        self.assertEqual(self.fdc.parameters.bytes_per_sector, 512)
        
        self.fdc.io_write_byte(0x3F5, 8) # Last sector number in cylinder.
        
        self.assertEqual(self.fdc.state, ST_RDDATA_SET_GAP_LENGTH)
        self.assertEqual(self.fdc.parameters.end_of_track, 8)
        
        self.fdc.io_write_byte(0x3F5, 33) # Gap length 33
        
        self.assertEqual(self.fdc.state, ST_RDDATA_SET_DATA_LENGTH)
        self.assertEqual(self.fdc.parameters.gap_length, 33)
        
        self.fdc.io_write_byte(0x3F5, 64) # Data length 64.
        
        # self.assertEqual(self.fdc.state, ST_RDDATA_EXECUTE)
        self.assertEqual(self.fdc.parameters.data_length, 64)
        
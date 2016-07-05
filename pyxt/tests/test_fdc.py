import unittest

from pyxt.tests.utils import SystemBusTestable
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
        
    def test_size_in_bytes(self):
        self.assertEqual(self.fdd.size_in_bytes, 368640)
        
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
        
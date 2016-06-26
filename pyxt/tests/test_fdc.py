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
        self.assertEqual(self.fdc.state, ST_READY)
        self.assertEqual(self.fdc.drive_select, 0)
        self.assertEqual(self.fdc.head_select, 0)
        self.assertEqual(self.fdc.drives, [None, None, None, None])
        
    def test_reset(self):
        self.fdc.state = 5643
        self.fdc.reset()
        self.assertEqual(self.fdc.state, ST_READY)
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
        drive = FloppyDisketteDrive(0)
        drive.present_cylinder_number = 33
        self.fdc.attach_drive(drive, 0)
        self.assertEqual(self.fdc.read_present_cylinder_number(), 33)
        
    def test_read_present_cylinder_number_invalid(self):
        self.fdc.drive_select = 2
        self.assertEqual(self.fdc.read_present_cylinder_number(), 0)
        
class FDDTests(unittest.TestCase):
    def setUp(self):
        self.fdd = FloppyDisketteDrive(1234)
        
    def test_initial_state(self):
        self.assertEqual(self.fdd.drive_type, 1234)
        self.assertEqual(self.fdd.present_cylinder_number, 0)
        
class FDCAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.fdc = FloppyDisketteController(0x3F0)
        self.fdd0 = FloppyDisketteDrive(0)
        self.fdc.attach_drive(self.fdd0, 0)
        self.fdd1 = FloppyDisketteDrive(0)
        self.fdc.attach_drive(self.fdd1, 1)
        
    def test_command_sense_interrupt_status(self):
        self.fdd0.present_cylinder_number = 27
        
        self.fdc.io_write_byte(0x3F5, 0x08) # Sense interrupt status.
        self.assertEqual(self.fdc.state, ST_SIS_READ_STATUS_REG_0)
        
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 0x00) # Status register 0.
        self.assertEqual(self.fdc.state, ST_SIS_READ_PRESENT_CYLINDER)
        
        self.assertEqual(self.fdc.io_read_byte(0x3F5), 27) # Present cylinder.
        self.assertEqual(self.fdc.state, ST_READY)
        
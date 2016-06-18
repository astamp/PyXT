import unittest

from pyxt.tests.utils import SystemBusTestable
from pyxt.ppi import *

class PPITests(unittest.TestCase):
    def setUp(self):
        self.ppi = ProgrammablePeripheralInterface(0x060)
        self.ppi.write_diag_port = self.diag_port_hook
        self.last_diag_output = None
        
        self.bus = SystemBusTestable()
        self.bus.install_device(None, self.ppi)
        
    def diag_port_hook(self, value):
        self.last_diag_output = value
        
    def test_address_list(self):
        self.assertEqual(self.ppi.get_ports_list(), [0x0060, 0x0061, 0x0062, 0x0063])
        
    def test_writing_to_diag_port(self):
        self.ppi.io_write_byte(0x060, 0xA5)
        self.assertEqual(self.last_diag_output, 0xA5)
        
    def test_input_from_keyboard(self):
        self.ppi.key_pressed((33,))
        self.assertEqual(self.ppi.io_read_byte(0x060), 33)
        self.assertEqual(self.bus.get_irq_log(), [1])
        
    def test_reading_from_keyboard_port(self):
        self.ppi.last_scancode = 0x01
        self.assertEqual(self.ppi.io_read_byte(0x060), 0x01)
        
    def test_writing_port_b(self):
        self.ppi.io_write_byte(0x061, 0x7F)
        self.assertEqual(self.ppi.port_b_output, 0x7F)
        
    def test_read_back_port_b(self):
        self.ppi.io_write_byte(0x061, 0x7F)
        self.assertEqual(self.ppi.io_read_byte(0x061), 0x7F)
        
    def test_port_b_swaps_dip_switches(self):
        self.ppi.dip_switches = 0xA5
        self.ppi.io_write_byte(0x061, 0x00)
        self.assertEqual(self.ppi.io_read_byte(0x062), 0x05)
        self.ppi.io_write_byte(0x061, 0x08)
        self.assertEqual(self.ppi.io_read_byte(0x062), 0x0A)
        
    def test_clear_keyboard(self):
        self.ppi.last_scancode = 0x01
        
        self.ppi.io_write_byte(0x061, 0x00) # Clear keyboard not asserted.
        self.assertEqual(self.ppi.last_scancode, 0x01) # Should be unmodified.
        
        self.ppi.io_write_byte(0x061, 0x80) # Clear keyboard asserted.
        self.assertEqual(self.ppi.last_scancode, 0x00)
        
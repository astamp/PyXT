import unittest

from pyxt.tests.utils import SystemBusTestable
from pyxt.ppi import *

class PPITests(unittest.TestCase):
    def setUp(self):
        self.ppi = ProgrammablePeripheralInterface(0x060)
        self.ppi.write_diag_port = self.diag_port_hook
        self.ppi.signal_keyboard_reset = self.signal_reset_hook
        self.ppi.speaker_control = self.speaker_control_hook
        self.last_diag_output = None
        self.reset_signalled = False
        self.speaker_enabled = False
        
        self.bus = SystemBusTestable()
        self.bus.install_device(None, self.ppi)
        
    # Test hooks.
    def diag_port_hook(self, value):
        self.last_diag_output = value
        
    def signal_reset_hook(self):
        self.reset_signalled = True
        
    def speaker_control_hook(self, enabled):
        self.speaker_enabled = enabled
        
    # Tests.
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
        
    def test_keyboard_reset(self):
        self.port_b_output = 0x00
        self.ppi.io_write_byte(0x061, 0x00) # Keyboard clock disabled.
        self.assertFalse(self.reset_signalled) # Reset not signalled.
        
        self.ppi.io_write_byte(0x061, 0x40) # Keyboard clock enabled.
        self.assertTrue(self.reset_signalled) # Reset signalled only on positive going transition.
        
        self.reset_signalled = False
        self.ppi.io_write_byte(0x061, 0x00) # Keyboard clock disabled.
        self.assertFalse(self.reset_signalled) # Reset not signalled.
        
    def test_self_test_complete(self):
        self.ppi.self_test_complete()
        self.assertEqual(self.ppi.last_scancode, 0xAA)
        self.assertEqual(self.bus.get_irq_log(), [1])
        
    def test_speaker_enabled(self):
        self.assertFalse(self.speaker_enabled)
        self.ppi.io_write_byte(0x061, 0x01) # Just the gate shouldn't enable the speaker.
        self.assertFalse(self.speaker_enabled)
        self.ppi.io_write_byte(0x061, 0x02) # Just the data shouldn't enable the speaker.
        self.assertFalse(self.speaker_enabled)
        self.ppi.io_write_byte(0x061, 0x03) # Both gate and data should enable the speaker.
        self.assertTrue(self.speaker_enabled)
                
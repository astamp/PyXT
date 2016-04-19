import unittest

from pyxt.ppi import *

class PPITests(unittest.TestCase):
    def setUp(self):
        self.ppi = ProgrammablePeripheralInterface(0x060)
        self.ppi.write_diag_port = self.diag_port_hook
        self.last_diag_output = None
        
    def diag_port_hook(self, value):
        self.last_diag_output = value
        
    def test_address_list(self):
        self.assertEqual(self.ppi.get_ports_list(), [0x0060, 0x0061, 0x0062, 0x0063])
        
    def test_writing_to_diag_port(self):
        self.ppi.io_write_byte(0x060, 0xA5)
        self.assertEqual(self.last_diag_output, 0xA5)
        
    def test_reading_from_keyboard_port(self):
        self.ppi.last_scancode = 0x01
        self.assertEqual(self.ppi.io_read_byte(0x060), 0x01)
        
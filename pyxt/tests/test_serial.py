import unittest

from pyxt.tests.utils import SystemBusTestable
from pyxt.serial import *

class SerialPortTests(unittest.TestCase):
    def setUp(self):
        self.ser = SerialAdapter(0x3F8, 4)
        
        self.bus = SystemBusTestable()
        self.bus.install_device(None, self.ser)
        
    def test_address_list(self):
        self.assertEqual(self.ser.get_ports_list(), [0x3F8, 0x3F9, 0x3FA, 0x3FB,
                                                     0x3FC, 0x3FD, 0x3FE, 0x3FF])
        
    def test_read_write_scratch_register(self):
        self.ser.io_write_byte(0x3FF, 0xA5)
        self.assertEqual(self.ser.io_read_byte(0x3FF), 0xA5)
        
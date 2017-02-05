import unittest

from pyxt.tests.utils import SystemBusTestable
from pyxt.parallel import *

class ParallelDeviceSpy(ParallelDevice):
    def __init__(self):
        super(ParallelDeviceSpy, self).__init__()
        self.last_write_byte = 0x00
    
    def write_byte(self, value):
        self.last_write_byte = value
        
class ParallelPortTests(unittest.TestCase):
    def setUp(self):
        self.lpt = ParallelAdapter(0x3BC, 7)
        
        self.bus = SystemBusTestable()
        self.bus.install_device(None, self.lpt)
        
    def test_address_list(self):
        self.assertEqual(self.lpt.get_ports_list(), [0x3BC, 0x3BD, 0x3BE])
        
    def test_initial_state(self):
        self.assertEqual(self.lpt.last_data_byte, 0x00)
        self.assertFalse(self.lpt.irq_enable)
        
    def test_read_back_write_data(self):
        self.lpt.io_write_byte(0x3BC, 0xA5)
        self.assertEqual(self.lpt.io_read_byte(0x3BC), 0xA5)
        
    def test_irq_enable(self):
        self.assertFalse(self.lpt.irq_enable)
        self.lpt.io_write_byte(0x3BE, 0x10)
        self.assertTrue(self.lpt.irq_enable)
        self.lpt.io_write_byte(0x3BE, 0x00)
        self.assertFalse(self.lpt.irq_enable)
        
    @unittest.skip("Not implemented yet.")
    def test_control_port_initial_state(self):
        self.assertEqual(self.lpt.io_read_byte(0x3BE), 0x0B)
        
class ParallelPortDeviceTests(unittest.TestCase):
    def setUp(self):
        self.lpt = ParallelAdapter(0x3BC, 7)
        
        self.dev = ParallelDeviceSpy()
        self.lpt.connect(self.dev)
        
        self.bus = SystemBusTestable()
        self.bus.install_device(None, self.lpt)
        
    def test_write_to_device(self):
        self.lpt.io_write_byte(0x3BC, 0xA5)
        self.assertEqual(self.dev.last_write_byte, 0xA5)
        
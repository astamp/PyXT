import unittest

from pyxt.bus import SystemBus
from pyxt.fdc import *

class InterruptControllerSpy(object):
    def __init__(self):
        self.irq_log = []
        
    def interrupt_request(self, irq):
        self.irq_log.append(irq)
        
class FDCTests(unittest.TestCase):
    def setUp(self):
        self.fdc = FloppyDisketteController(0x3F0)
        
        self.pic = InterruptControllerSpy()
        self.bus = SystemBus(self.pic)
        self.bus.install_device(None, self.fdc)
        
        self.reset_called = False
        
    def test_address_list(self):
        self.assertEqual(self.fdc.get_ports_list(), [0x3F2, 0x3F4, 0x3F5])
        
    def test_initial_state(self):
        self.assertFalse(self.fdc.enabled)
        self.assertEqual(self.fdc.state, ST_READY)
        
    def test_reset(self):
        self.fdc.state = 5643
        self.fdc.reset()
        self.assertEqual(self.fdc.state, ST_READY)
        self.assertEqual(self.pic.irq_log, [6])
        
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
        
    def test_status_register_in_reset(self):
        self.assertEqual(self.fdc.io_read_byte(0x3F4), 0x00)
        
    def test_status_register_after_reset(self):
        self.fdc.io_write_byte(0x3F2, 0x04)
        self.assertEqual(self.fdc.io_read_byte(0x3F4), 0x80)
        
    def test_status_register_after_reset(self):
        self.fdc.io_write_byte(0x3F2, 0x04)
        self.assertEqual(self.fdc.io_read_byte(0x3F4), 0x80)
        
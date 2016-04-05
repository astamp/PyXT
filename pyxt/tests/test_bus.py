import unittest

from pyxt.bus import *

class DeviceTests(unittest.TestCase):
    def setUp(self):
        self.device = Device()
        
    def test_initial_state(self):
        self.assertTrue(self.device.bus is None)
        
    def test_install(self):
        self.device.install(5643)
        self.assertEqual(self.device.bus, 5643)
        
    def test_reset_not_pure_virtual(self):
        self.device.reset()
        
    def test_clock_not_pure_virtual(self):
        self.device.clock()
        
        
    def test_memory_size_zero(self):
        self.assertEqual(self.device.get_memory_size(), 0)
        
    def test_no_mem_reads(self):
        with self.assertRaises(NotImplementedError):
            self.device.mem_read_byte(0)
            
        with self.assertRaises(NotImplementedError):
            self.device.mem_read_word(0)
            
    def test_no_mem_writes(self):
        with self.assertRaises(NotImplementedError):
            self.device.mem_write_byte(0, 0)
            
        with self.assertRaises(NotImplementedError):
            self.device.mem_write_word(0, 0)
            
            
    def test_address_list_empty(self):
        self.assertEqual(self.device.get_ports_list(), [])
        
    def test_no_io_reads(self):
        with self.assertRaises(NotImplementedError):
            self.device.io_read_byte(0)
            
        with self.assertRaises(NotImplementedError):
            self.device.io_read_word(0)
            
    def test_no_io_writes(self):
        with self.assertRaises(NotImplementedError):
            self.device.io_write_byte(0, 0)
            
        with self.assertRaises(NotImplementedError):
            self.device.io_write_word(0, 0)
            
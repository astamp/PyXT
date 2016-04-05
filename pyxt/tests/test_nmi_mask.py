import unittest

from pyxt.nmi_mask import *

class NMIMaskTests(unittest.TestCase):
    def setUp(self):
        self.nmi_mask = NMIMaskRegister(0x0A0)
        
    def test_address_list(self):
        self.assertEqual(self.nmi_mask.get_ports_list(), [0x0A0])
        
    def test_initial_state(self):
        self.assertFalse(self.nmi_mask.masked)
        
    def test_disable_nmi(self):
        self.nmi_mask.masked = False
        self.nmi_mask.io_write_byte(0x0A0, 0x00)
        self.assertTrue(self.nmi_mask.masked)
        
    def test_enable_nmi(self):
        self.nmi_mask.masked = True
        self.nmi_mask.io_write_byte(0x0A0, 0x80)
        self.assertFalse(self.nmi_mask.masked)
        
    def test_read_state(self):
        self.nmi_mask.masked = False
        self.assertEqual(self.nmi_mask.io_read_byte(0x0A0), 0x80)
        self.nmi_mask.masked = True
        self.assertEqual(self.nmi_mask.io_read_byte(0x0A0), 0x00)
        
        
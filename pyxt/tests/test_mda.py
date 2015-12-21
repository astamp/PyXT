import unittest

from pyxt.mda import *

class MDATests(unittest.TestCase):
    def setUp(self):
        self.obj = MonochromeDisplayAdapter()
        
    def test_ports_list(self):
        self.assertEqual(self.obj.get_ports_list(), [0x03B0, 0x03B1, 0x03B2, 0x03B3,
                                                     0x03B4, 0x03B5, 0x03B6, 0x03B7,
                                                     0x03B8, 0x03B9, 0x03BA, 0x03BB])
        
    def test_initial_state(self):
        self.assertEqual(self.obj.control_reg, 0x00)
        self.assertEqual(self.obj.data_reg_index, 0x00)
        
    # def test_
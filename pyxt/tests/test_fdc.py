import unittest

from pyxt.fdc import *

class FDCTests(unittest.TestCase):
    def setUp(self):
        self.fdc = FloppyDisketteController(0x3F0)
        
    def test_address_list(self):
        self.assertEqual(self.fdc.get_ports_list(), [0x3F2, 0x3F4, 0x3F5])
        
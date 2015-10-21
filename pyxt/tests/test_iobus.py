import unittest

from pyxt.iobus import *

class PICTests(unittest.TestCase):
    def setUp(self):
        self.obj = ProgrammableInterruptController(0x00A0)
        
    def test_address_list(self):
        self.assertEqual(self.obj.get_address_list(), [0x00A0, 0x00A1])
        
    def test_initial_state(self):
        self.assertEqual(self.obj.mask, 0x00)
        
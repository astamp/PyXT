import unittest

from pyxt.dma import *

class DMATests(unittest.TestCase):
    def setUp(self):
        self.dma = DmaController(0x0000)
        
    def test_address_list(self):
        self.assertEqual(self.dma.get_ports_list(), [0x0000, 0x0001, 0x0002, 0x0003,
                                                     0x0004, 0x0005, 0x0006, 0x0007,
                                                     0x0008, 0x0009, 0x000A, 0x000B,
                                                     0x000C, 0x000D, 0x000E, 0x000F])
        
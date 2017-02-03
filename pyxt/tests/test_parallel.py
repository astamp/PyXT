import unittest

from pyxt.tests.utils import SystemBusTestable
from pyxt.parallel import *

class ParallelPortTests(unittest.TestCase):
    def setUp(self):
        self.lpt = ParallelAdapter(0x3BC, 7)
        
        self.bus = SystemBusTestable()
        self.bus.install_device(None, self.lpt)
        
    def test_address_list(self):
        self.assertEqual(self.lpt.get_ports_list(), [0x3BC, 0x3BD, 0x3BE])
        
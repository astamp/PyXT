import unittest
import binascii

import six
from six.moves import range # pylint: disable=redefined-builtin 

from pyxt.constants import *
from pyxt.cpu import *
from pyxt.bus import Device
from pyxt.tests.utils import SystemBusTestable
from pyxt.memory import RAM

class BaseOpcodeTimingTests(unittest.TestCase):
    """
    Base class for testing instruction timings (clock cycles).
    """
    def setUp(self):
        self.bus = SystemBusTestable()
        self.cpu = CPU()
        self.cpu.install_bus(self.bus)
        self.cpu.regs.CS = 0x0000
        self.cpu.regs.DS = 0x0000
        self.memory = RAM(SIXTY_FOUR_KB)
        self.bus.install_device(0x0000, self.memory)
        
    def load_code_bytes(self, *args):
        """ Load a program into the base memory, returning the number of bytes loaded. """
        count = 0
        
        for index, byte in enumerate(args):
            self.memory.mem_write_byte(index, byte)
            count += 1
            
        return count
        
    def load_code_string(self, code):
        """ Load a program into the base memory from a hex string, returning the number of bytes loaded. """
        return self.load_code_bytes(*[byte for byte in six.iterbytes(binascii.unhexlify(code.replace(" ", "")))])
        
    def run_single_instruction(self):
        """
        Run a single instruction, returning the number of cycles executed.
        """
        # Reset these in case there are multiple runs in the same test.
        self.cpu.regs.IP = 0x0000
        return self.cpu.fetch()
        
class EffectiveAddressTimingTests(BaseOpcodeTimingTests):
    """ Based on Table 2-20 1981 iAPX 86/88 Users Manual (page 2-51). """
    def setUp(self):
        super(EffectiveAddressTimingTests, self).setUp()
        self.cpu.regs.BX = 0x1000
        self.cpu.regs.BP = 0x2080
        self.cpu.regs.SI = 0x400F
        self.cpu.regs.DI = 0x8C00
        
    # Displacement only (6 cycles)
    def test_displacement_only(self):
        """
        add cx, [0xcafe]
        """
        self.load_code_string("03 0E FE CA")
        self.cpu.regs.IP = 0x0001
        self.assertEqual(self.cpu.get_modrm_operands(16), ("CX", ADDRESS, 0xCAFE, 6))
        
    # Base or index only (5 cycles)
    def test_bx_only(self):
        """
        add cx, [bx]
        """
        self.load_code_string("03 0F")
        self.cpu.regs.IP = 0x0001
        self.assertEqual(self.cpu.get_modrm_operands(16), ("CX", ADDRESS, 0x1000, 5))
        
    @unittest.skip("BP always has a zero displacement because mod 0, rm 110 is absolute immediate.")
    def test_bp_only(self):
        """
        add cx, [bp]
        """
        self.load_code_string("03 4E 00")
        self.cpu.regs.IP = 0x0001
        self.assertEqual(self.cpu.get_modrm_operands(16), ("CX", ADDRESS, 0x2080, 5))
        
    def test_si_only(self):
        """
        add cx, [si]
        """
        self.load_code_string("03 0C")
        self.cpu.regs.IP = 0x0001
        self.assertEqual(self.cpu.get_modrm_operands(16), ("CX", ADDRESS, 0x400F, 5))
        
    def test_di_only(self):
        """
        add cx, [di]
        """
        self.load_code_string("03 0D")
        self.cpu.regs.IP = 0x0001
        self.assertEqual(self.cpu.get_modrm_operands(16), ("CX", ADDRESS, 0x8C00, 5))
        
    # Displacement + base or index (9 cycles)
    def test_bx_with_byte_displacement(self):
        """
        add cx, [bx + 24]
        """
        self.load_code_string("03 4F 18")
        self.cpu.regs.IP = 0x0001
        self.assertEqual(self.cpu.get_modrm_operands(16), ("CX", ADDRESS, 0x1000 + 24, 9))
        
    def test_bx_with_word_displacement(self):
        """
        add cx, [bx + 384]
        """
        self.load_code_string("03 8F 80 01")
        self.cpu.regs.IP = 0x0001
        self.assertEqual(self.cpu.get_modrm_operands(16), ("CX", ADDRESS, 0x1000 + 384, 9))
        
    def test_bp_with_byte_displacement(self):
        """
        add cx, [bp + 24]
        """
        self.load_code_string("03 4E 18")
        self.cpu.regs.IP = 0x0001
        self.assertEqual(self.cpu.get_modrm_operands(16), ("CX", ADDRESS, 0x2080 + 24, 9))
        
    def test_bp_with_word_displacement(self):
        """
        add cx, [bp + 384]
        """
        self.load_code_string("03 8E 80 01")
        self.cpu.regs.IP = 0x0001
        self.assertEqual(self.cpu.get_modrm_operands(16), ("CX", ADDRESS, 0x2080 + 384, 9))
        
    def test_si_with_byte_displacement(self):
        """
        add cx, [si + 24]
        """
        self.load_code_string("03 4C 18")
        self.cpu.regs.IP = 0x0001
        self.assertEqual(self.cpu.get_modrm_operands(16), ("CX", ADDRESS, 0x400F + 24, 9))
        
    def test_si_with_word_displacement(self):
        """
        add cx, [si + 384]
        """
        self.load_code_string("03 8C 80 01")
        self.cpu.regs.IP = 0x0001
        self.assertEqual(self.cpu.get_modrm_operands(16), ("CX", ADDRESS, 0x400F + 384, 9))
        
    def test_di_with_byte_displacement(self):
        """
        add cx, [di + 24]
        """
        self.load_code_string("03 4D 18")
        self.cpu.regs.IP = 0x0001
        self.assertEqual(self.cpu.get_modrm_operands(16), ("CX", ADDRESS, 0x8C00 + 24, 9))
        
    def test_di_with_word_displacement(self):
        """
        add cx, [di + 384]
        """
        self.load_code_string("03 8D 80 01")
        self.cpu.regs.IP = 0x0001
        self.assertEqual(self.cpu.get_modrm_operands(16), ("CX", ADDRESS, 0x8C00 + 384, 9))
        
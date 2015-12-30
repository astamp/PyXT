import unittest
import binascii

from pyxt.constants import *
from pyxt.cpu import *
from pyxt.bus import SystemBus
from pyxt.memory import RAM

class FlagsRegisterTest(unittest.TestCase):
    def setUp(self):
        self.obj = FLAGS()
        
    def test_initialized_to_zero(self):
        self.assertEqual(self.obj.value, 0)
        
    def test_set(self):
        self.obj.value = FLAGS.CARRY
        self.obj.set(FLAGS.PARITY)
        self.assertEqual(self.obj.value, FLAGS.CARRY | FLAGS.PARITY)
        
    def test_clear(self):
        self.obj.value = FLAGS.CARRY | FLAGS.PARITY
        self.obj.clear(FLAGS.PARITY)
        self.assertEqual(self.obj.value, FLAGS.CARRY)
        
    def test_assign(self):
        self.obj.value = FLAGS.CARRY
        self.obj.assign(FLAGS.ZERO, True)
        self.assertEqual(self.obj.value, FLAGS.CARRY | FLAGS.ZERO)
        self.obj.assign(FLAGS.ZERO, False)
        self.assertEqual(self.obj.value, FLAGS.CARRY)
        
    def test_read(self):
        self.obj.value = FLAGS.CARRY | FLAGS.PARITY
        self.assertTrue(self.obj.read(FLAGS.CARRY))
        self.assertFalse(self.obj.read(FLAGS.ZERO))
        
    # Property tests.
    def test_carry_flag_property_get(self):
        self.assertFalse(self.obj.cf)
        self.obj.value |= FLAGS.CARRY
        self.assertTrue(self.obj.cf)
        
    def test_carry_flag_property_set(self):
        self.assertEqual(self.obj.value, 0)
        self.obj.cf = True
        self.assertEqual(self.obj.value, FLAGS.CARRY)
        self.obj.cf = False
        self.assertEqual(self.obj.value, 0)
        
    def test_parity_flag_property_get(self):
        self.assertFalse(self.obj.pf)
        self.obj.value |= FLAGS.PARITY
        self.assertTrue(self.obj.pf)
        
    def test_parity_flag_property_set(self):
        self.assertEqual(self.obj.value, 0)
        self.obj.pf = True
        self.assertEqual(self.obj.value, FLAGS.PARITY)
        self.obj.pf = False
        self.assertEqual(self.obj.value, 0)
        
    def test_adjust_flag_property_get(self):
        self.assertFalse(self.obj.af)
        self.obj.value |= FLAGS.ADJUST
        self.assertTrue(self.obj.af)
        
    def test_adjust_flag_property_set(self):
        self.assertEqual(self.obj.value, 0)
        self.obj.af = True
        self.assertEqual(self.obj.value, FLAGS.ADJUST)
        self.obj.af = False
        self.assertEqual(self.obj.value, 0)
        
    def test_zero_flag_property_get(self):
        self.assertFalse(self.obj.zf)
        self.obj.value |= FLAGS.ZERO
        self.assertTrue(self.obj.zf)
        
    def test_zero_flag_property_set(self):
        self.assertEqual(self.obj.value, 0)
        self.obj.zf = True
        self.assertEqual(self.obj.value, FLAGS.ZERO)
        self.obj.zf = False
        self.assertEqual(self.obj.value, 0)
        
    def test_sign_flag_property_get(self):
        self.assertFalse(self.obj.sf)
        self.obj.value |= FLAGS.SIGN
        self.assertTrue(self.obj.sf)
        
    def test_sign_flag_property_set(self):
        self.assertEqual(self.obj.value, 0)
        self.obj.sf = True
        self.assertEqual(self.obj.value, FLAGS.SIGN)
        self.obj.sf = False
        self.assertEqual(self.obj.value, 0)
        
class HelperFunctionTest(unittest.TestCase):
    def test_decode_seg_reg_normal(self):
        self.assertEqual(decode_seg_reg(0x00), "ES")
        self.assertEqual(decode_seg_reg(0x01), "CS")
        self.assertEqual(decode_seg_reg(0x02), "SS")
        self.assertEqual(decode_seg_reg(0x03), "DS")
        
    def test_decode_seg_reg_masks_to_2_bits(self):
        self.assertEqual(decode_seg_reg(0xFC), "ES")
        self.assertEqual(decode_seg_reg(0xFD), "CS")
        self.assertEqual(decode_seg_reg(0xFE), "SS")
        self.assertEqual(decode_seg_reg(0xFF), "DS")
        
class BaseOpcodeAcceptanceTests(unittest.TestCase):
    """
    Basic acceptance testing framework for the CPU class.
    
    Code can be generated with the following NASM command:
    nasm temp.asm -f bin -o temp.bin
    """
    def setUp(self):
        self.bus = SystemBus()
        self.cpu = CPU()
        self.cpu.bus = self.bus
        self.cpu.regs["CS"] = 0x0000
        self.cpu.regs["DS"] = 0x0000
        self.memory = RAM(SIXTY_FOUR_KB)
        self.bus.install_device(0x0000, self.memory)
        
    def load_code_bytes(self, *args):
        """ Load a program into the base memory. """
        for index, byte in enumerate(args):
            self.memory.write_byte(index, byte)
            
    def load_code_string(self, code):
        """ Load a program into the base memory from a hex string. """
        self.load_code_bytes(*[ord(byte) for byte in binascii.unhexlify(code.replace(" ", ""))])
        
    def run_to_halt(self, max_instructions = 1000):
        """
        Run the CPU until it halts, returning the number of instructions executed.
        
        If it runs for more than max_instructions the test immediately fails.
        """
        instruction_count = 0
        while not self.cpu.hlt:
            self.cpu.fetch()
            instruction_count += 1
            if instruction_count > max_instructions:
                self.fail("Runaway deetected, terminated after %d instructions." % max_instructions)
                
        return instruction_count
        
class AddOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_add_rm8_r8(self):
        """
        add [value], al
        hlt
        value:
            db 1
        """
        self.cpu.regs["AL"] = 7
        self.load_code_bytes(0x00, 0x06, 0x05, 0x00, 0xF4, 0x01)
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AL"], 7)
        self.assertEqual(self.memory.read_byte(0x05), 8)
        
class MovOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_mov_sreg_rm16(self):
        """
        mov es, [value]
        hlt
        value:
            dw 0xBEEF
        """
        self.cpu.regs["ES"] = 0x0000
        self.load_code_string("8E 06 05 00 F4 EF BE")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["ES"], 0xBEEF)
        
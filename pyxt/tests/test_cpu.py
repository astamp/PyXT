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
            self.memory.mem_write_byte(index, byte)
            
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
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("00 06 05 00 F4 01")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 7)
        self.assertEqual(self.memory.mem_read_byte(0x05), 8)
        
    def test_add_rm16_r16(self):
        """
        add [value], ax
        hlt
        value:
            dw 0xFF
        """
        self.cpu.regs["AX"] = 7
        self.load_code_string("01 06 05 00 F4 FF 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 7)
        self.assertEqual(self.memory.mem_read_word(0x05), 0x0106)
        
    def test_add_r8_rm8(self):
        """
        add al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("02 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 29)
        self.assertEqual(self.memory.mem_read_byte(0x05), 22)
        
    def test_add_r16_rm16(self):
        """
        add ax, [value]
        hlt
        value:
            dw 0xFF
        """
        self.cpu.regs["AX"] = 7
        self.load_code_string("03 06 05 00 F4 FF 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 0x0106)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFF)
        
    def test_add_al_imm8(self):
        """
        add al, 7
        hlt
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("04 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 14)
        
    def test_add_ax_imm16(self):
        """
        add ax, word 2222
        hlt
        """
        self.cpu.regs["AX"] = 1234
        self.load_code_string("05 AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 3456)
        
class OrOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_or_rm8_r8(self):
        """
        or [value], al
        hlt
        value:
            db 0x0F
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 0x18
        self.load_code_string("08 06 05 00 F4 0F")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 0x18)
        self.assertEqual(self.memory.mem_read_byte(0x05), 0x1F)
        
    def test_or_rm16_r16(self):
        """
        or [value], ax
        hlt
        value:
            dw 0x01A5
        """
        self.cpu.regs["AX"] = 0x015A
        self.load_code_string("09 06 05 00 F4 A5 01")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 0x015A)
        self.assertEqual(self.memory.mem_read_word(0x05), 0x01FF)
        
    def test_or_r8_rm8(self):
        """
        or al, [value]
        hlt
        value:
            db 0x04
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 0x08
        self.load_code_string("0A 06 05 00 F4 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 0x0C)
        self.assertEqual(self.memory.mem_read_byte(0x05), 0x04)
        
    def test_or_r16_rm16(self):
        """
        or bx, [value]
        hlt
        value:
            dw 0xF000
        """
        self.cpu.regs["BX"] = 0x0ACE
        self.load_code_string("0B 1E 05 00 F4 00 F0")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["BX"], 0xFACE)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xF000)
        
    def test_or_al_imm8(self):
        """
        or al, 0x07
        hlt
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 0x1E
        self.load_code_string("0C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 0x1F)
        
    def test_or_ax_imm16(self):
        """
        or ax, 0xC0F0
        hlt
        """
        self.cpu.regs["AX"] = 0x0A0E
        self.load_code_string("0D F0 C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 0xCAFE)
        
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
        self.assertEqual(self.memory.mem_read_word(0x05), 0xBEEF)
        
    def test_mov_rm16_sreg(self):
        """
        mov [value], es
        hlt
        value:
            dw 0x0000
        """
        self.cpu.regs["ES"] = 0xCAFE
        self.load_code_string("8C 06 05 00 F4 00 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["ES"], 0xCAFE)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xCAFE)
        
    def test_mov_r16_rm16(self):
        """
        mov bx, [value]
        hlt
        value:
            dw 0x1234
        """
        self.cpu.regs["BX"] = 0x0000
        self.load_code_string("8B 1E 05 00 F4 34 12")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["BX"], 0x1234)
        self.assertEqual(self.memory.mem_read_word(0x05), 0x1234)
        
class FlagOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_stc(self):
        """
        stc
        hlt
        """
        self.assertFalse(self.cpu.flags.read(FLAGS.CARRY))
        self.load_code_string("F9 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertTrue(self.cpu.flags.read(FLAGS.CARRY))
        
    def test_clc(self):
        """
        clc
        hlt
        """
        self.cpu.flags.set(FLAGS.CARRY)
        self.assertTrue(self.cpu.flags.read(FLAGS.CARRY))
        self.load_code_string("F8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertFalse(self.cpu.flags.read(FLAGS.CARRY))
        
    def test_std(self):
        """
        std
        hlt
        """
        self.assertFalse(self.cpu.flags.read(FLAGS.DIRECTION))
        self.load_code_string("FD F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertTrue(self.cpu.flags.read(FLAGS.DIRECTION))
        
    def test_cld(self):
        """
        cld
        hlt
        """
        self.cpu.flags.set(FLAGS.DIRECTION)
        self.assertTrue(self.cpu.flags.read(FLAGS.DIRECTION))
        self.load_code_string("FC F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertFalse(self.cpu.flags.read(FLAGS.DIRECTION))
        
class LoopOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_loop(self):
        """
        again:
            loop again
        hlt
        """
        self.cpu.regs["CX"] = 3
        self.load_code_string("E2 FE F4")
        self.assertEqual(self.run_to_halt(), 4)
        self.assertEqual(self.cpu.regs["CX"], 0x00)
        
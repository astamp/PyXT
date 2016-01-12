import unittest
import binascii

from pyxt.constants import *
from pyxt.cpu import *
from pyxt.bus import SystemBus, Device
from pyxt.memory import RAM

class CpuTests(unittest.TestCase):
    def setUp(self):
        self.cpu = CPU()
        
    def test_cs_init_to_ffff(self):
        self.assertEqual(self.cpu.regs.CS, 0xFFFF)
        
    def test_other_regs_init_to_zero(self):
        self.assertEqual(self.cpu.regs.AX, 0)
        self.assertEqual(self.cpu.regs.BX, 0)
        self.assertEqual(self.cpu.regs.CX, 0)
        self.assertEqual(self.cpu.regs.DX, 0)
        self.assertEqual(self.cpu.regs.IP, 0)
        self.assertEqual(self.cpu.regs.BP, 0)
        self.assertEqual(self.cpu.regs.SI, 0)
        self.assertEqual(self.cpu.regs.DI, 0)
        self.assertEqual(self.cpu.regs.DS, 0)
        self.assertEqual(self.cpu.regs.ES, 0)
        self.assertEqual(self.cpu.regs.SS, 0)
        
class FlagsRegisterTest(unittest.TestCase):
    def setUp(self):
        self.flags = FLAGS()
        
    def test_initialized_to_zero(self):
        self.assertEqual(self.flags.value, 0)
        
    # Property tests.
    def test_carry_flag_property_get(self):
        self.assertFalse(self.flags.carry)
        self.flags.value |= FLAGS.CARRY
        self.assertTrue(self.flags.carry)
        
    def test_carry_flag_property_set(self):
        self.assertEqual(self.flags.value, 0)
        self.flags.carry = True
        self.assertEqual(self.flags.value, FLAGS.CARRY)
        self.flags.carry = False
        self.assertEqual(self.flags.value, 0)
        
    def test_parity_flag_property_get(self):
        self.assertFalse(self.flags.parity)
        self.flags.value |= FLAGS.PARITY
        self.assertTrue(self.flags.parity)
        
    def test_parity_flag_property_set(self):
        self.assertEqual(self.flags.value, 0)
        self.flags.parity = True
        self.assertEqual(self.flags.value, FLAGS.PARITY)
        self.flags.parity = False
        self.assertEqual(self.flags.value, 0)
        
    def test_adjust_flag_property_get(self):
        self.assertFalse(self.flags.adjust)
        self.flags.value |= FLAGS.ADJUST
        self.assertTrue(self.flags.adjust)
        
    def test_adjust_flag_property_set(self):
        self.assertEqual(self.flags.value, 0)
        self.flags.adjust = True
        self.assertEqual(self.flags.value, FLAGS.ADJUST)
        self.flags.adjust = False
        self.assertEqual(self.flags.value, 0)
        
    def test_zero_flag_property_get(self):
        self.assertFalse(self.flags.zero)
        self.flags.value |= FLAGS.ZERO
        self.assertTrue(self.flags.zero)
        
    def test_zero_flag_property_set(self):
        self.assertEqual(self.flags.value, 0)
        self.flags.zero = True
        self.assertEqual(self.flags.value, FLAGS.ZERO)
        self.flags.zero = False
        self.assertEqual(self.flags.value, 0)
        
    def test_sign_flag_property_get(self):
        self.assertFalse(self.flags.sign)
        self.flags.value |= FLAGS.SIGN
        self.assertTrue(self.flags.sign)
        
    def test_sign_flag_property_set(self):
        self.assertEqual(self.flags.value, 0)
        self.flags.sign = True
        self.assertEqual(self.flags.value, FLAGS.SIGN)
        self.flags.sign = False
        self.assertEqual(self.flags.value, 0)
        
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
        
class UnionRegsTest(unittest.TestCase):
    def setUp(self):
        self.regs = UnionRegs()
        
    def test_initialized_to_zero(self):
        self.assertEqual(self.regs.AX, 0)
        self.assertEqual(self.regs.BX, 0)
        self.assertEqual(self.regs.CX, 0)
        self.assertEqual(self.regs.DX, 0)
        
        self.assertEqual(self.regs.SI, 0)
        self.assertEqual(self.regs.DI, 0)
        self.assertEqual(self.regs.BP, 0)
        self.assertEqual(self.regs.SP, 0)
        
        self.assertEqual(self.regs.IP, 0)
        
        self.assertEqual(self.regs.CS, 0)
        self.assertEqual(self.regs.DS, 0)
        self.assertEqual(self.regs.ES, 0)
        self.assertEqual(self.regs.SS, 0)
        
    def test_16_bit_overflow(self):
        self.regs.AX = 0xFFFF
        self.regs.AX += 1
        self.assertEqual(self.regs.AX, 0)
        
    def test_16_bit_underflow(self):
        self.regs.AX = 0
        self.regs.AX -= 1
        self.assertEqual(self.regs.AX, 0xFFFF)
        
    def test_8_bit_overflow_high(self):
        self.regs.AH = 0xFF
        self.regs.AH += 1
        self.assertEqual(self.regs.AH, 0)
        self.assertEqual(self.regs.AX, 0)
        
    def test_8_bit_overflow_low(self):
        self.regs.AL = 0xFF
        self.regs.AL += 1
        self.assertEqual(self.regs.AL, 0)
        self.assertEqual(self.regs.AX, 0)
        
    def test_8_bit_underflow_high(self):
        self.regs.AH = 0
        self.regs.AH -= 1
        self.assertEqual(self.regs.AH, 0xFF)
        self.assertEqual(self.regs.AX, 0xFF00)
        
    def test_8_bit_underflow_low(self):
        self.regs.AL = 0
        self.regs.AL -= 1
        self.assertEqual(self.regs.AL, 0xFF)
        self.assertEqual(self.regs.AX, 0x00FF)
        
    def test_ax_linked_to_ah_al(self):
        self.regs.AX = 0xCAFE
        self.assertEqual(self.regs.AH, 0xCA)
        self.assertEqual(self.regs.AL, 0xFE)
        
        self.regs.AH = 0x12
        self.assertEqual(self.regs.AX, 0x12FE)
        self.regs.AL = 0x34
        self.assertEqual(self.regs.AX, 0x1234)
        
    def test_bx_linked_to_bh_bl(self):
        self.regs.BX = 0xCAFE
        self.assertEqual(self.regs.BH, 0xCA)
        self.assertEqual(self.regs.BL, 0xFE)
        
        self.regs.BH = 0x12
        self.assertEqual(self.regs.BX, 0x12FE)
        self.regs.BL = 0x34
        self.assertEqual(self.regs.BX, 0x1234)
        
    def test_cx_linked_to_ch_cl(self):
        self.regs.CX = 0xCAFE
        self.assertEqual(self.regs.CH, 0xCA)
        self.assertEqual(self.regs.CL, 0xFE)
        
        self.regs.CH = 0x12
        self.assertEqual(self.regs.CX, 0x12FE)
        self.regs.CL = 0x34
        self.assertEqual(self.regs.CX, 0x1234)
        
    def test_dx_linked_to_dh_dl(self):
        self.regs.DX = 0xCAFE
        self.assertEqual(self.regs.DH, 0xCA)
        self.assertEqual(self.regs.DL, 0xFE)
        
        self.regs.DH = 0x12
        self.assertEqual(self.regs.DX, 0x12FE)
        self.regs.DL = 0x34
        self.assertEqual(self.regs.DX, 0x1234)
        
    def test_getitem(self):
        self.regs.AX = 0x5643
        self.assertEqual(self.regs["AX"], 0x5643)
        
    def test_setitem(self):
        self.regs["BX"] = 0xF00D
        self.assertEqual(self.regs.BX, 0xF00D)
        
class BaseOpcodeAcceptanceTests(unittest.TestCase):
    """
    Basic acceptance testing framework for the CPU class.
    
    Code can be generated with the following NASM command:
    nasm temp.asm -f bin -o temp.bin
    """
    def setUp(self):
        self.bus = SystemBus()
        self.cpu = CPU()
        self.cpu.install_bus(self.bus)
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
        # Reset these in case there are multiple runs in the same test.
        self.cpu.regs.IP = 0
        self.cpu.hlt = False
        
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
        
class AdcOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_adc_operator_carry_clear(self):
        self.assertFalse(self.cpu.flags.carry)
        self.assertEqual(self.cpu.operator_adc(7, 5), 12)
        
    def test_adc_operator_carry_set(self):
        self.cpu.flags.carry = True
        self.assertTrue(self.cpu.flags.carry)
        self.assertEqual(self.cpu.operator_adc(7, 5), 13)
        
    def test_adc_rm8_r8_carry_clear(self):
        """
        adc [value], al
        hlt
        value:
            db 1
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("10 06 05 00 F4 01")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 7)
        self.assertEqual(self.memory.mem_read_byte(0x05), 8)
        
    def test_adc_rm8_r8_carry_set(self):
        """
        adc [value], al
        hlt
        value:
            db 1
        """
        self.cpu.flags.carry = True
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("10 06 05 00 F4 01")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 7)
        self.assertEqual(self.memory.mem_read_byte(0x05), 9)
        
    def test_adc_rm16_r16_carry_clear(self):
        """
        adc [value], ax
        hlt
        value:
            dw 0xFF
        """
        self.cpu.regs["AX"] = 7
        self.load_code_string("11 06 05 00 F4 FF 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 7)
        self.assertEqual(self.memory.mem_read_word(0x05), 0x0106)
        
    def test_adc_rm16_r16_carry_set(self):
        """
        adc [value], ax
        hlt
        value:
            dw 0xFF
        """
        self.cpu.flags.carry = True
        self.cpu.regs["AX"] = 7
        self.load_code_string("11 06 05 00 F4 FF 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 7)
        self.assertEqual(self.memory.mem_read_word(0x05), 0x0107)
        
    def test_adc_r8_rm8_carry_clear(self):
        """
        adc al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("12 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 29)
        self.assertEqual(self.memory.mem_read_byte(0x05), 22)
        
    def test_adc_r8_rm8_carry_set(self):
        """
        adc al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.flags.carry = True
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("12 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 30)
        self.assertEqual(self.memory.mem_read_byte(0x05), 22)
        
    def test_adc_r16_rm16_carry_clear(self):
        """
        adc ax, [value]
        hlt
        value:
            dw 0xFF
        """
        self.cpu.regs["AX"] = 7
        self.load_code_string("13 06 05 00 F4 FF 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 0x0106)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFF)
        
    def test_adc_r16_rm16_carry_set(self):
        """
        adc ax, [value]
        hlt
        value:
            dw 0xFF
        """
        self.cpu.flags.carry = True
        self.cpu.regs["AX"] = 7
        self.load_code_string("13 06 05 00 F4 FF 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 0x0107)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFF)
        
    def test_adc_al_imm8_carry_clear(self):
        """
        adc al, 7
        hlt
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("14 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 14)
        
    def test_adc_al_imm8_carry_set(self):
        """
        adc al, 7
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("14 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 15)
        
    def test_adc_ax_imm16_carry_clear(self):
        """
        adc ax, word 2222
        hlt
        """
        self.cpu.regs["AX"] = 1234
        self.load_code_string("15 AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 3456)
        
    def test_adc_ax_imm16_carry_set(self):
        """
        adc ax, word 2222
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs["AX"] = 1234
        self.load_code_string("15 AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 3457)
        
class SubOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_sub_rm8_r8(self):
        """
        sub [value], al
        hlt
        value:
            db 50
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("28 06 05 00 F4 32")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 7)
        self.assertEqual(self.memory.mem_read_byte(0x05), 43)
        
    def test_sub_rm16_r16(self):
        """
        sub [value], ax
        hlt
        value:
            dw 10
        """
        self.cpu.regs["AX"] = 11
        self.load_code_string("29 06 05 00 F4 0A 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 11)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFFFF)
        
    def test_sub_r8_rm8(self):
        """
        sub al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("2A 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 241)
        self.assertEqual(self.memory.mem_read_byte(0x05), 22)
        
    def test_sub_r16_rm16(self):
        """
        sub ax, [value]
        hlt
        value:
            dw 1111
        """
        self.cpu.regs["AX"] = 2345
        self.load_code_string("2B 06 05 00 F4 57 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 1234)
        self.assertEqual(self.memory.mem_read_word(0x05), 1111)
        
    def test_sub_al_imm8(self):
        """
        sub al, 7
        hlt
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("2C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 0)
        
    def test_sub_ax_imm16(self):
        """
        sub ax, word 2222
        hlt
        """
        self.cpu.regs["AX"] = 5643
        self.load_code_string("2D AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 3421)
        
class SbbOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_sbb_operator_carry_clear(self):
        self.assertFalse(self.cpu.flags.carry)
        self.assertEqual(self.cpu.operator_sbb(7, 5), 2)
        
    def test_sbb_operator_carry_set(self):
        self.cpu.flags.carry = True
        self.assertTrue(self.cpu.flags.carry)
        self.assertEqual(self.cpu.operator_sbb(7, 5), 1)
        
    def test_sbb_rm8_r8_carry_clear(self):
        """
        sbb [value], al
        hlt
        value:
            db 50
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("18 06 05 00 F4 32")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 7)
        self.assertEqual(self.memory.mem_read_byte(0x05), 43)
        
    def test_sbb_rm8_r8_carry_set(self):
        """
        sbb [value], al
        hlt
        value:
            db 50
        """
        self.cpu.flags.carry = True
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("18 06 05 00 F4 32")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 7)
        self.assertEqual(self.memory.mem_read_byte(0x05), 42)
        
    def test_sbb_rm16_r16_carry_clear(self):
        """
        sbb [value], ax
        hlt
        value:
            dw 10
        """
        self.cpu.regs["AX"] = 11
        self.load_code_string("19 06 05 00 F4 0A 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 11)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFFFF)
        
    def test_sbb_rm16_r16_carry_set(self):
        """
        sbb [value], ax
        hlt
        value:
            dw 10
        """
        self.cpu.flags.carry = True
        self.cpu.regs["AX"] = 11
        self.load_code_string("19 06 05 00 F4 0A 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 11)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFFFE)
        
    def test_sbb_r8_rm8_carry_clear(self):
        """
        sbb al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("1A 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 241)
        self.assertEqual(self.memory.mem_read_byte(0x05), 22)
        
    def test_sbb_r8_rm8_carry_set(self):
        """
        sbb al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.flags.carry = True
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("1A 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 240)
        self.assertEqual(self.memory.mem_read_byte(0x05), 22)
        
    def test_sbb_r16_rm16_carry_clear(self):
        """
        sbb ax, [value]
        hlt
        value:
            dw 1111
        """
        self.cpu.regs["AX"] = 2345
        self.load_code_string("1B 06 05 00 F4 57 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 1234)
        self.assertEqual(self.memory.mem_read_word(0x05), 1111)
        
    def test_sbb_r16_rm16_carry_set(self):
        """
        sbb ax, [value]
        hlt
        value:
            dw 1111
        """
        self.cpu.flags.carry = True
        self.cpu.regs["AX"] = 2345
        self.load_code_string("1B 06 05 00 F4 57 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 1233)
        self.assertEqual(self.memory.mem_read_word(0x05), 1111)
        
    def test_sbb_al_imm8_carry_clear(self):
        """
        sbb al, 7
        hlt
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("1C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 0)
        
    def test_sbb_al_imm8_carry_set(self):
        """
        sbb al, 7
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("1C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 0xFF)
        
    def test_sbb_ax_imm16_carry_clear(self):
        """
        sbb ax, word 2222
        hlt
        """
        self.cpu.regs["AX"] = 5643
        self.load_code_string("1D AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 3421)
        
    def test_sbb_ax_imm16_carry_set(self):
        """
        sbb ax, word 2222
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs["AX"] = 5643
        self.load_code_string("1D AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 3420)
        
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
        
class AndOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_and_rm8_r8(self):
        """
        and [value], al
        hlt
        value:
            db 0x0F
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 0x7E
        self.load_code_string("20 06 05 00 F4 0F")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 0x7E)
        self.assertEqual(self.memory.mem_read_byte(0x05), 0x0E)
        
    def test_and_rm16_r16(self):
        """
        and [value], ax
        hlt
        value:
            dw 0xFACE
        """
        self.cpu.regs["AX"] = 0x0FF0
        self.load_code_string("21 06 05 00 F4 CE FA")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 0x0FF0)
        self.assertEqual(self.memory.mem_read_word(0x05), 0x0AC0)
        
    def test_and_r8_rm8(self):
        """
        and al, [value]
        hlt
        value:
            db 0x3C
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 0xA5
        self.load_code_string("22 06 05 00 F4 3C")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 0x24)
        self.assertEqual(self.memory.mem_read_byte(0x05), 0x3C)
        
    def test_and_r16_rm16(self):
        """
        and bx, [value]
        hlt
        value:
            dw 0xF000
        """
        self.cpu.regs["BX"] = 0xFACE
        self.load_code_string("23 1E 05 00 F4 00 F0")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["BX"], 0xF000)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xF000)
        
    def test_and_al_imm8(self):
        """
        and al, 0x07
        hlt
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 0x1E
        self.load_code_string("24 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 0x06)
        
    def test_and_ax_imm16(self):
        """
        and ax, 0xF00F
        hlt
        """
        self.cpu.regs["AX"] = 0xBEEF
        self.load_code_string("25 0F F0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 0xB00F)
        
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
        self.assertFalse(self.cpu.flags.carry)
        self.load_code_string("F9 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_clc(self):
        """
        clc
        hlt
        """
        self.cpu.flags.carry = True
        self.assertTrue(self.cpu.flags.carry)
        self.load_code_string("F8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_std(self):
        """
        std
        hlt
        """
        self.assertFalse(self.cpu.flags.direction)
        self.load_code_string("FD F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertTrue(self.cpu.flags.direction)
        
    def test_cld(self):
        """
        cld
        hlt
        """
        self.cpu.flags.direction = True
        self.assertTrue(self.cpu.flags.direction)
        self.load_code_string("FC F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertFalse(self.cpu.flags.direction)
        
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
        
class IOPortTester(Device):
    """ Device that maps to all ports for testing. """
    def __init__(self):
        super(IOPortTester, self).__init__()
        
        # Fill in each port with zero.
        self.data = {}
        for port in self.get_ports_list():
            self.data[port] = 0
            
    def get_ports_list(self):
        return [port for port in xrange(1024)]
        
    def io_read_byte(self, port):
        return self.data[port]
        
    def io_write_byte(self, port, value):
        self.data[port] = value
        
class IOPortOpcodeTests(BaseOpcodeAcceptanceTests):
    def setUp(self):
        super(IOPortOpcodeTests, self).setUp()
        self.port_tester = IOPortTester()
        self.bus.install_device(None, self.port_tester)
        
    def test_in_al_imm8(self):
        """
        in al, 0x40
        hlt
        """
        self.port_tester.data[0x40] = 77
        self.load_code_string("E4 40 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AL"], 77)
        self.assertEqual(self.port_tester.data[0x40], 77)
        
class IncOpcodeTests(BaseOpcodeAcceptanceTests):
    def run_inc_16_bit_test(self, code_string, register):
        """
        Generic function for testing INC on 16 bit registers.
        """
        self.load_code_string(code_string)
        
        test_data = (
            (0, 1), # Start from zero.
            (0xFF, 0x0100), # Byte rollover.
            (5643, 5644), # Random value.
            (0xFFFF, 0), # Word rollover.
        )
        
        for (before, after) in test_data:
            self.cpu.regs[register] = before
            self.assertEqual(self.run_to_halt(), 2)
            self.assertEqual(self.cpu.regs[register], after)
            
    def test_inc_ax(self):
        """
        inc ax
        hlt
        """
        self.run_inc_16_bit_test("40 F4", "AX")
        
    def test_inc_bx(self):
        """
        inc bx
        hlt
        """
        self.run_inc_16_bit_test("43 F4", "BX")
        
    def test_inc_cx(self):
        """
        inc cx
        hlt
        """
        self.run_inc_16_bit_test("41 F4", "CX")
        
    def test_inc_dx(self):
        """
        inc dx
        hlt
        """
        self.run_inc_16_bit_test("42 F4", "DX")
        
    def test_inc_sp(self):
        """
        inc sp
        hlt
        """
        self.run_inc_16_bit_test("44 F4", "SP")
        
    def test_inc_bp(self):
        """
        inc bp
        hlt
        """
        self.run_inc_16_bit_test("45 F4", "BP")
        
    def test_inc_si(self):
        """
        inc si
        hlt
        """
        self.run_inc_16_bit_test("46 F4", "SI")
        
    def test_inc_di(self):
        """
        inc di
        hlt
        """
        self.run_inc_16_bit_test("47 F4", "DI")
        
class DecOpcodeTests(BaseOpcodeAcceptanceTests):
    def run_dec_16_bit_test(self, code_string, register):
        """
        Generic function for testing DEC on 16 bit registers.
        """
        self.load_code_string(code_string)
        
        test_data = (
            (0, 0xFFFF), # Word rollover.
            (0x0100, 0x00FF), # Byte rollover.
            (5643, 5642), # Random value.
            (0xFFFF, 0xFFFE), # Start from "-1".
        )
        
        for (before, after) in test_data:
            self.cpu.regs[register] = before
            self.assertEqual(self.run_to_halt(), 2)
            self.assertEqual(self.cpu.regs[register], after)
            
    def test_dec_ax(self):
        """
        dec ax
        hlt
        """
        self.run_dec_16_bit_test("48 F4", "AX")
        
    def test_dec_bx(self):
        """
        dec bx
        hlt
        """
        self.run_dec_16_bit_test("4B F4", "BX")
        
    def test_dec_cx(self):
        """
        dec cx
        hlt
        """
        self.run_dec_16_bit_test("49 F4", "CX")
        
    def test_dec_dx(self):
        """
        dec dx
        hlt
        """
        self.run_dec_16_bit_test("4A F4", "DX")
        
    def test_dec_sp(self):
        """
        dec sp
        hlt
        """
        self.run_dec_16_bit_test("4C F4", "SP")
        
    def test_dec_bp(self):
        """
        dec bp
        hlt
        """
        self.run_dec_16_bit_test("4D F4", "BP")
        
    def test_dec_si(self):
        """
        dec si
        hlt
        """
        self.run_dec_16_bit_test("4E F4", "SI")
        
    def test_dec_di(self):
        """
        dec di
        hlt
        """
        self.run_dec_16_bit_test("4F F4", "DI")
        
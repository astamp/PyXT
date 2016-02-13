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
        
    def run_set_from_alu_test(self, func, value, zero, sign, carry, parity):
        """ Execute func with value and check the flags, None is a don't care. """
        func(value)
        test_case = "%s(0x%x)" % (func.__name__, value)
        
        if zero is not None:
            self.assertEqual(self.flags.zero, zero, test_case)
            
        if sign is not None:
            self.assertEqual(self.flags.sign, sign, test_case)
            
        if carry is not None:
            self.assertEqual(self.flags.carry, carry, test_case)
            
        if parity is not None:
            self.assertEqual(self.flags.parity, parity, test_case)
            
    def test_set_from_alu_word(self):
        data = [
            # value,    zero,   sign,   carry,  parity  # Description
            (0x0000,    True,   False,  False,  True),  # Zero
            (0x8000,    False,  True,   False,  None),  # Sign
            (0x10000,   False,  False,  True,   None),  # Carry
            (0x0003,    False,  False,  False,  True),  # Even parity
            (0x0007,    False,  False,  False,  False), # Odd parity
            (0x0703,    False,  False,  False,  True),  # Parity only checks low byte
        ]
        
        for args in data:
            self.run_set_from_alu_test(self.flags.set_from_alu_word, *args)
            
    def test_set_from_alu_no_carry_word_previously_cleared(self):
        data = [
            # value,    zero,   sign,   carry,  parity  # Description
            (0x0000,    True,   False,  False,  True),  # Zero
            (0x8000,    False,  True,   False,  None),  # Sign
            (0x10000,   False,  False,  False,  None),  # Carry NOT MODIFIED
            (0x0003,    False,  False,  False,  True),  # Even parity
            (0x0007,    False,  False,  False,  False), # Odd parity
            (0x0703,    False,  False,  False,  True),  # Parity only checks low byte
        ]
        
        for args in data:
            self.run_set_from_alu_test(self.flags.set_from_alu_no_carry_word, *args)
            
    def test_set_from_alu_no_carry_word_previously_set(self):
        data = [
            # value,    zero,   sign,   carry,  parity  # Description
            (0x0000,    True,   False,  True,  True),   # Zero
            (0x8000,    False,  True,   True,  None),   # Sign
            (0x10000,   False,  False,  True,  None),   # Carry NOT MODIFIED
            (0x0003,    False,  False,  True,  True),   # Even parity
            (0x0007,    False,  False,  True,  False),  # Odd parity
            (0x0703,    False,  False,  True,  True),   # Parity only checks low byte
        ]
        
        self.flags.carry = True
        for args in data:
            self.run_set_from_alu_test(self.flags.set_from_alu_no_carry_word, *args)
            
            
    def test_set_from_alu_byte(self):
        data = [
            # value,    zero,   sign,   carry,  parity  # Description
            (0x00,    True,   False,  False,  True),  # Zero
            (0x80,    False,  True,   False,  None),  # Sign
            (0x100,   False,  False,  True,   None),  # Carry
            (0x03,    False,  False,  False,  True),  # Even parity
            (0x07,    False,  False,  False,  False), # Odd parity
        ]
        
        for args in data:
            self.run_set_from_alu_test(self.flags.set_from_alu_byte, *args)
            
    def test_set_from_alu_no_carry_byte_previously_cleared(self):
        data = [
            # value,    zero,   sign,   carry,  parity  # Description
            (0x00,    True,   False,  False,  True),  # Zero
            (0x80,    False,  True,   False,  None),  # Sign
            (0x100,   False,  False,  False,  None),  # Carry NOT MODIFIED
            (0x03,    False,  False,  False,  True),  # Even parity
            (0x07,    False,  False,  False,  False), # Odd parity
        ]
        
        for args in data:
            self.run_set_from_alu_test(self.flags.set_from_alu_no_carry_byte, *args)
            
    def test_set_from_alu_no_carry_byte_previously_set(self):
        data = [
            # value,    zero,   sign,   carry,  parity  # Description
            (0x00,    True,   False,  True,  True),   # Zero
            (0x80,    False,  True,   True,  None),   # Sign
            (0x100,   False,  False,  True,  None),   # Carry NOT MODIFIED
            (0x03,    False,  False,  True,  True),   # Even parity
            (0x07,    False,  False,  True,  False),  # Odd parity
        ]
        
        self.flags.carry = True
        for args in data:
            self.run_set_from_alu_test(self.flags.set_from_alu_no_carry_byte, *args)
            
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
        
    def test_assignment_masks_to_8_bits(self):
        self.regs.AL = 384
        self.assertEqual(self.regs.AL, 128)
        self.assertEqual(self.regs.AH, 0)
        
    def test_assignment_masks_to_16_bits(self):
        self.regs.AX = 115200
        self.assertEqual(self.regs.AX, 49664)
        
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
        """ Load a program into the base memory, returning the number of bytes loaded. """
        count = 0
        
        for index, byte in enumerate(args):
            self.memory.mem_write_byte(index, byte)
            count += 1
            
        return count
        
    def load_code_string(self, code):
        """ Load a program into the base memory from a hex string, returning the number of bytes loaded. """
        return self.load_code_bytes(*[ord(byte) for byte in binascii.unhexlify(code.replace(" ", ""))])
        
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
                self.fail("Runaway detected, terminated after %d instructions." % max_instructions)
                
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
        
class CmpOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_cmp_rm8_r8_none(self):
        """
        cmp [value], al
        hlt
        value:
            db 50
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("38 06 05 00 F4 32")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 7) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(0x05), 50) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_rm8_r8_zero(self):
        """
        cmp [value], al
        hlt
        value:
            db 50
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 50
        self.load_code_string("38 06 05 00 F4 32")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 50) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(0x05), 50) # Should be unmodified.
        
        self.assertTrue(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_rm8_r8_sign_carry(self):
        """
        cmp [value], al
        hlt
        value:
            db 50
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 51
        self.load_code_string("38 06 05 00 F4 32")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 51) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(0x05), 50) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_cmp_rm16_r16_none(self):
        """
        cmp [value], ax
        hlt
        value:
            dw 1000
        """
        self.cpu.regs["AX"] = 11
        self.load_code_string("39 06 05 00 F4 E8 03")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 11) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_word(0x05), 1000) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_rm16_r16_zero(self):
        """
        cmp [value], ax
        hlt
        value:
            dw 1000
        """
        self.cpu.regs["AX"] = 1000
        self.load_code_string("39 06 05 00 F4 E8 03")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 1000) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_word(0x05), 1000) # Should be unmodified.
        
        self.assertTrue(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_rm16_r16_sign_carry(self):
        """
        cmp [value], ax
        hlt
        value:
            dw 1000
        """
        self.cpu.regs["AX"] = 1001
        self.load_code_string("39 06 05 00 F4 E8 03")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 1001) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_word(0x05), 1000) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_cmp_r8_rm8_none(self):
        """
        cmp al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 23
        self.load_code_string("3A 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 23) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(0x05), 22) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_r8_rm8_zero(self):
        """
        cmp al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 22
        self.load_code_string("3A 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 22) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(0x05), 22) # Should be unmodified.
        
        self.assertTrue(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_r8_rm8_sign_carry(self):
        """
        cmp al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 21
        self.load_code_string("3A 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 21) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(0x05), 22) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_cmp_r16_rm16_none(self):
        """
        cmp ax, [value]
        hlt
        value:
            dw 1111
        """
        self.cpu.regs["AX"] = 2000
        self.load_code_string("3B 06 05 00 F4 57 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 2000) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_word(0x05), 1111) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_r16_rm16_zero(self):
        """
        cmp ax, [value]
        hlt
        value:
            dw 1111
        """
        self.cpu.regs["AX"] = 1111
        self.load_code_string("3B 06 05 00 F4 57 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 1111) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_word(0x05), 1111) # Should be unmodified.
        
        self.assertTrue(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_r16_rm16_sign_carry(self):
        """
        cmp ax, [value]
        hlt
        value:
            dw 1111
        """
        self.cpu.regs["AX"] = 500
        self.load_code_string("3B 06 05 00 F4 57 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 500) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_word(0x05), 1111) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_cmp_al_imm8_none(self):
        """
        cmp al, 7
        hlt
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 8
        self.load_code_string("3C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 8) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_al_imm8_zero(self):
        """
        cmp al, 7
        hlt
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 7
        self.load_code_string("3C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 7) # Should be unmodified.
        
        self.assertTrue(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_al_imm8_sign_carry(self):
        """
        cmp al, 7
        hlt
        """
        self.cpu.regs["AH"] = 0xA5
        self.cpu.regs["AL"] = 6
        self.load_code_string("3C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AH"], 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs["AL"], 6) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_cmp_ax_imm16_none(self):
        """
        cmp ax, word 2222
        hlt
        """
        self.cpu.regs["AX"] = 5643
        self.load_code_string("3D AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 5643) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_ax_imm16_zero(self):
        """
        cmp ax, word 2222
        hlt
        """
        self.cpu.regs["AX"] = 2222
        self.load_code_string("3D AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 2222) # Should be unmodified.
        
        self.assertTrue(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_ax_imm16_sign_carry(self):
        """
        cmp ax, word 2222
        hlt
        """
        self.cpu.regs["AX"] = 0
        self.load_code_string("3D AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AX"], 0) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertTrue(self.cpu.flags.carry)
        
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
        
    def test_mov_r8_rm8(self):
        """
        mov bl, [value]
        hlt
        value:
            db 0x5A
        """
        self.cpu.regs.BX = 0x1234
        self.load_code_string("8A 1E 05 00 F4 5A")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BH, 0x12) # Should be unmodified.
        self.assertEqual(self.cpu.regs.BL, 0x5A)
        
    def test_mov_al_moffs8(self):
        """
        mov al, [5643]
        hlt
        """
        self.cpu.regs.AX = 0x1111
        self.memory.mem_write_byte(5643, 0xA7)
        self.load_code_string("A0 0B 16 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0x11) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0xA7)
        self.assertEqual(self.memory.mem_read_byte(5643), 0xA7) # Should be unmodified.
        
    def test_mov_ax_moffs16(self):
        """
        mov ax, [5643]
        hlt
        """
        self.cpu.regs.AX = 0x1111
        self.memory.mem_write_word(5643, 0xDADA)
        self.load_code_string("A1 0B 16 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xDADA)
        self.assertEqual(self.memory.mem_read_word(5643), 0xDADA) # Should be unmodified.
        
    def test_mov_moffs8_al(self):
        """
        mov [5643], al
        hlt
        """
        self.cpu.regs.AX = 0x1234
        self.load_code_string("A2 0B 16 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x1234) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(5642), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(5643), 0x34)
        self.assertEqual(self.memory.mem_read_byte(5644), 0x00) # Should be unmodified.
        
    def test_mov_moffs16_ax(self):
        """
        mov [5643], ax
        hlt
        """
        self.cpu.regs.AX = 0x1234
        self.load_code_string("A3 0B 16 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x1234) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(5642), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(5643), 0x34)
        self.assertEqual(self.memory.mem_read_byte(5644), 0x12)
        self.assertEqual(self.memory.mem_read_byte(5645), 0x00) # Should be unmodified.
        
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
        
    def test_sti(self):
        """
        sti
        hlt
        """
        self.assertFalse(self.cpu.flags.interrupt_enable)
        self.load_code_string("FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertTrue(self.cpu.flags.interrupt_enable)
        
    def test_cli(self):
        """
        cli
        hlt
        """
        self.cpu.flags.interrupt_enable = True
        self.assertTrue(self.cpu.flags.interrupt_enable)
        self.load_code_string("FA F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertFalse(self.cpu.flags.interrupt_enable)
        
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
        
    def test_loop_does_not_modify_flags(self):
        """
        again:
            loop again
        hlt
        """
        self.cpu.flags.zero = False
        self.cpu.flags.sign = True
        self.cpu.flags.carry = True
        
        self.cpu.regs["CX"] = 3
        self.load_code_string("E2 FE F4")
        self.assertEqual(self.run_to_halt(), 4)
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_loopz_zero_set(self):
        """
        again:
            loopz again
        hlt
        """
        self.cpu.flags.zero = True
        self.cpu.regs.CX = 3
        self.load_code_string("E1 FE F4")
        self.assertEqual(self.run_to_halt(), 4)
        self.assertEqual(self.cpu.regs.CX, 0)
        
    def test_loopz_zero_clear(self):
        """
        again:
            loopz again
        hlt
        """
        self.cpu.flags.zero = False
        self.cpu.regs.CX = 3
        self.load_code_string("E1 FE F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.CX, 2) # Still decremented this once.
        
    def test_loopz_does_not_modify_flags(self):
        """
        again:
            loopz again
        hlt
        """
        self.cpu.flags.zero = True
        self.cpu.flags.sign = True
        self.cpu.flags.carry = True
        
        self.cpu.regs.CX = 3
        self.load_code_string("E1 FE F4")
        self.assertEqual(self.run_to_halt(), 4)
        
        self.assertTrue(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_loopnz_zero_set(self):
        """
        again:
            loopnz again
        hlt
        """
        self.cpu.flags.zero = True
        self.cpu.regs.CX = 3
        self.load_code_string("E0 FE F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.CX, 2) # Still decremented this once.
        
    def test_loopnz_zero_clear(self):
        """
        again:
            loopnz again
        hlt
        """
        self.cpu.flags.zero = False
        self.cpu.regs.CX = 3
        self.load_code_string("E0 FE F4")
        self.assertEqual(self.run_to_halt(), 4)
        self.assertEqual(self.cpu.regs.CX, 0)
        
    def test_loopnz_does_not_modify_flags(self):
        """
        again:
            loopnz again
        hlt
        """
        self.cpu.flags.zero = False
        self.cpu.flags.sign = True
        self.cpu.flags.carry = True
        
        self.cpu.regs.CX = 3
        self.load_code_string("E0 FE F4")
        self.assertEqual(self.run_to_halt(), 4)
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertTrue(self.cpu.flags.carry)
        
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
        
    def test_in_al_dx(self):
        """
        in al, dx
        hlt
        """
        self.cpu.regs.DX = 0x3F8
        self.port_tester.data[0x3F8] = 77
        self.load_code_string("EC F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs["AL"], 77)
        self.assertEqual(self.port_tester.data[0x3F8], 77)
        
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
        
class LodsOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_lodsb_incrementing(self):
        """
        lodsb
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.SI = 0x0004
        self.cpu.regs.AX = 0x0000
        self.memory.mem_write_word(19, 0xF0)
        self.memory.mem_write_word(20, 0x77)
        self.memory.mem_write_word(21, 0x0F)
        self.load_code_string("AC F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x77)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DS, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SI, 0x0005)
        
    def test_lodsb_decrementing(self):
        """
        lodsb
        hlt
        """
        self.cpu.flags.direction = True
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.SI = 0x0004
        self.cpu.regs.AX = 0x0000
        self.memory.mem_write_word(19, 0xF0)
        self.memory.mem_write_word(20, 0x77)
        self.memory.mem_write_word(21, 0x0F)
        self.load_code_string("AC F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x77)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DS, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SI, 0x0003)
        
    def test_lodsw_incrementing(self):
        """
        lodsw
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.SI = 0x0004
        self.cpu.regs.AX = 0x00
        self.memory.mem_write_word(19, 0xF0)
        self.memory.mem_write_word(20, 0x77)
        self.memory.mem_write_word(21, 0x0F)
        self.load_code_string("AD F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0F77)
        self.assertEqual(self.cpu.regs.DS, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SI, 0x0006)
        
    def test_lodsw_decrementing(self):
        """
        lodsw
        hlt
        """
        self.cpu.flags.direction = True
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.SI = 0x0004
        self.cpu.regs.AX = 0x00
        self.memory.mem_write_word(19, 0xF0)
        self.memory.mem_write_word(20, 0x77)
        self.memory.mem_write_word(21, 0x0F)
        self.load_code_string("AD F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0F77)
        self.assertEqual(self.cpu.regs.DS, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SI, 0x0002)
        
class TestOpcodeTests(BaseOpcodeAcceptanceTests):
    """ Yo dawg... """
    def test_test_rm8_imm8_zero(self):
        """
        test bl, 0x80
        hlt
        """
        self.cpu.regs.BL = 0x1F
        self.load_code_string("F6 C3 80 F4")
        self.assertEqual(self.run_to_halt(), 2)
        
        self.assertTrue(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_test_rm8_imm8_nonzero(self):
        """
        test bl, 0x80
        hlt
        """
        self.cpu.regs.BL = 0xF0
        self.load_code_string("F6 C3 80 F4")
        self.assertEqual(self.run_to_halt(), 2)
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_test_rm16_imm16_zero(self):
        """
        test bx, 0x80FF
        hlt
        """
        self.cpu.regs.BX = 0x7F00
        self.load_code_string("F7 C3 FF 80 F4")
        self.assertEqual(self.run_to_halt(), 2)
        
        self.assertTrue(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_test_rm16_imm16_nonzero(self):
        """
        test bx, 0x80FF
        hlt
        """
        self.cpu.regs.BX = 0x8000
        self.load_code_string("F7 C3 FF 80 F4")
        self.assertEqual(self.run_to_halt(), 2)
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_test_al_imm8_zero(self):
        """
        test al, 0x80
        hlt
        """
        self.cpu.regs.AL = 0x7F
        self.load_code_string("A8 80 F4")
        self.assertEqual(self.run_to_halt(), 2)
        
        self.assertTrue(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_test_al_imm8_nonzero(self):
        """
        test al, 0x80
        hlt
        """
        self.cpu.regs.AL = 0xF0
        self.load_code_string("A8 80 F4")
        self.assertEqual(self.run_to_halt(), 2)
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
class RolOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_rol_rm8_1_simple(self):
        """
        rol al, 1
        hlt
        """
        self.cpu.regs.AL = 0x0F
        self.load_code_string("D0 C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x1E)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertFalse(self.cpu.flags.carry)
        
    def test_rol_rm8_1_wrap_around(self):
        """
        rol al, 1
        hlt
        """
        self.cpu.regs.AL = 0x80
        self.load_code_string("D0 C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x01)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertTrue(self.cpu.flags.carry)
        
    def test_rol_rm16_1_simple(self):
        """
        rol ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x00F0
        self.load_code_string("D1 C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x01E0)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_rol_rm16_1_wrap_around(self):
        """
        rol ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x8000
        self.load_code_string("D1 C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0001)
        self.assertTrue(self.cpu.flags.carry)
        
class SarOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_sar_rm8_1_positive(self):
        """
        sar al, 1
        hlt
        """
        self.cpu.regs.AL = 0x40
        self.load_code_string("D0 F8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x20)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertFalse(self.cpu.flags.carry)
        
    def test_sar_rm8_1_negative(self):
        """
        sar al, 1
        hlt
        """
        self.cpu.regs.AL = 0x80
        self.load_code_string("D0 F8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0xC0)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertFalse(self.cpu.flags.carry)
        
    def test_sar_rm8_1_shift_out(self):
        """
        sar al, 1
        hlt
        """
        self.cpu.regs.AL = 0x01
        self.load_code_string("D0 F8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x00)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertTrue(self.cpu.flags.carry)
        
    def test_sar_rm16_1_positive(self):
        """
        sar ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x4000
        self.load_code_string("D1 F8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x2000)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_sar_rm8_1_negative(self):
        """
        sar al, 1
        hlt
        """
        self.cpu.regs.AX = 0x8000
        self.load_code_string("D1 F8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xC000)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_sar_rm8_1_shift_out(self):
        """
        sar al, 1
        hlt
        """
        self.cpu.regs.AX = 0x0001
        self.load_code_string("D1 F8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0000)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_sar_rm8_1_cross_byte(self):
        """
        sar al, 1
        hlt
        """
        self.cpu.regs.AX = 0x0100
        self.load_code_string("D1 F8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x0080)
        self.assertFalse(self.cpu.flags.carry)
        
class StosOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_stosb_incrementing(self):
        """
        stosb
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AH = 0xFF
        self.cpu.regs.AL = 0x77
        self.load_code_string("AA F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x77) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AH, 0xFF) # Should be unmodified.
        self.assertEqual(self.cpu.regs.ES, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DI, 0x0005)
        self.assertEqual(self.memory.mem_read_byte(19), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x77)
        self.assertEqual(self.memory.mem_read_byte(21), 0x00) # Should be unmodified.
        
    def test_stosb_decrementing(self):
        """
        stosb
        hlt
        """
        self.cpu.flags.direction = True
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AH = 0xFF
        self.cpu.regs.AL = 0x77
        self.load_code_string("AA F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x77) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AH, 0xFF) # Should be unmodified.
        self.assertEqual(self.cpu.regs.ES, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DI, 0x0003)
        self.assertEqual(self.memory.mem_read_byte(19), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x77)
        self.assertEqual(self.memory.mem_read_byte(21), 0x00) # Should be unmodified.
        
    def test_stosw_incrementing(self):
        """
        stosw
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AH = 0xFF
        self.cpu.regs.AL = 0x77
        self.load_code_string("AB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x77) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AH, 0xFF) # Should be unmodified.
        self.assertEqual(self.cpu.regs.ES, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DI, 0x0006)
        self.assertEqual(self.memory.mem_read_byte(19), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x77)
        self.assertEqual(self.memory.mem_read_byte(21), 0xFF)
        self.assertEqual(self.memory.mem_read_byte(22), 0x00) # Should be unmodified.
        
    def test_stosw_decrementing(self):
        """
        stosw
        hlt
        """
        self.cpu.flags.direction = True
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AH = 0xFF
        self.cpu.regs.AL = 0x77
        self.load_code_string("AB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x77) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AH, 0xFF) # Should be unmodified.
        self.assertEqual(self.cpu.regs.ES, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DI, 0x0002)
        self.assertEqual(self.memory.mem_read_byte(19), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x77)
        self.assertEqual(self.memory.mem_read_byte(21), 0xFF)
        self.assertEqual(self.memory.mem_read_byte(22), 0x00) # Should be unmodified.
        
class RepPrefixTests(BaseOpcodeAcceptanceTests):
    def test_rep_stosb(self):
        """
        rep stosb
        hlt
        """
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 4
        self.cpu.regs.AL = 0xAA
        self.cpu.regs.CX = 3
        self.load_code_string("F3 AA F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DI, 7)
        self.assertEqual(self.cpu.regs.CX, 0)
        self.assertEqual(self.memory.mem_read_byte(19), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0xAA)
        self.assertEqual(self.memory.mem_read_byte(21), 0xAA)
        self.assertEqual(self.memory.mem_read_byte(22), 0xAA)
        self.assertEqual(self.memory.mem_read_byte(23), 0x00) # Should be unmodified.
        
    def test_rep_stosw(self):
        """
        rep stosw
        hlt
        """
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 4
        self.cpu.regs.AX = 0xAA55
        self.cpu.regs.CX = 2
        self.load_code_string("F3 AB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DI, 8)
        self.assertEqual(self.cpu.regs.CX, 0)
        self.assertEqual(self.memory.mem_read_byte(19), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x55)
        self.assertEqual(self.memory.mem_read_byte(21), 0xAA)
        self.assertEqual(self.memory.mem_read_byte(22), 0x55)
        self.assertEqual(self.memory.mem_read_byte(23), 0xAA)
        self.assertEqual(self.memory.mem_read_byte(24), 0x00) # Should be unmodified.
        
    def test_rep_lodsb(self):
        """
        rep lodsb
        hlt
        """
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.SI = 4
        self.cpu.regs.AX = 0x0000
        self.cpu.regs.CX = 2
        self.memory.mem_write_byte(19, 0xF0)
        self.memory.mem_write_byte(20, 0x77)
        self.memory.mem_write_byte(21, 0x0F)
        self.load_code_string("F3 AC F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SI, 6)
        self.assertEqual(self.cpu.regs.CX, 0)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0x0F) # It was the last one.
        
    def test_rep_lodsw(self):
        """
        rep lodsw
        hlt
        """
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.SI = 4
        self.cpu.regs.AX = 0x0000
        self.cpu.regs.CX = 3
        self.memory.mem_write_byte(19, 0x11)
        self.memory.mem_write_byte(20, 0x22)
        self.memory.mem_write_byte(21, 0x33)
        self.memory.mem_write_byte(22, 0x44)
        self.memory.mem_write_byte(23, 0x55)
        self.memory.mem_write_byte(24, 0x66)
        self.memory.mem_write_byte(25, 0x77)
        self.load_code_string("F3 AD F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SI, 10)
        self.assertEqual(self.cpu.regs.CX, 0)
        self.assertEqual(self.cpu.regs.AX, 0x7766) # It was the last one.
        
    def test_rep_cancels_after_one(self):
        """
        rep stosb
        stosb
        hlt
        """
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 4
        self.cpu.regs.AL = 0xAA
        self.cpu.regs.CX = 3
        self.load_code_string("F3 AA AA F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.DI, 8)
        self.assertEqual(self.cpu.regs.CX, 0)
        self.assertEqual(self.memory.mem_read_byte(19), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0xAA) # Three from rep stosb.
        self.assertEqual(self.memory.mem_read_byte(21), 0xAA)
        self.assertEqual(self.memory.mem_read_byte(22), 0xAA)
        self.assertEqual(self.memory.mem_read_byte(23), 0xAA) # One from the second stosb, shouldn't skip on CX == 0.
        self.assertEqual(self.memory.mem_read_byte(24), 0x00) # Should be unmodified.
        
    def test_rep_skips_if_cx_equals_zero(self):
        """
        rep stosb
        hlt
        """
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 4
        self.cpu.regs.AL = 0xAA
        self.cpu.regs.CX = 0
        self.load_code_string("F3 AA F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DI, 4)
        self.assertEqual(self.cpu.regs.CX, 0)
        self.assertEqual(self.memory.mem_read_byte(19), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(21), 0x00) # Should be unmodified.
        
    @unittest.skip("The jury is still out on if this is useful...")
    def test_rep_doesnt_hop_instructions_that_dont_support_it(self):
        """
        rep inc bx
        stosb
        hlt
        """
        # I'm not even sure why this assembles, it seems invalid.
        # This crashes in a FreeDOS VM, so this test only exists so the behaviour is consistent.
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 4
        self.cpu.regs.AL = 0xAA
        self.cpu.regs.BX = 0
        self.cpu.regs.CX = 2
        self.load_code_string("F3 43 AA F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.BX, 1) # Only one time.
        self.assertEqual(self.cpu.regs.DI, 5)
        self.assertEqual(self.cpu.regs.CX, 2) # Invalid opcode/prefix combination ignored.
        self.assertEqual(self.memory.mem_read_byte(19), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0xAA) # Only one time.
        self.assertEqual(self.memory.mem_read_byte(21), 0x00) # Should be unmodified.
        
    def test_rep_halts_on_invalid_instruction(self):
        """
        rep inc bx
        stosb
        hlt
        """
        # I'm not even sure why this assembles, it seems invalid.
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 4
        self.cpu.regs.AL = 0xAA
        self.cpu.regs.BX = 0
        self.cpu.regs.CX = 2
        self.load_code_string("F3 43 AA F4")
        self.assertEqual(self.run_to_halt(), 1)
        self.assertEqual(self.cpu.regs.BX, 1) # Only one time.
        self.assertEqual(self.cpu.regs.DI, 4) # We halted before executing this.
        self.assertEqual(self.cpu.regs.CX, 2) # Invalid opcode/prefix combination ignored.
        self.assertEqual(self.memory.mem_read_byte(20), 0x00) # We halted before executing this.
        
    def test_rep_movsb(self):
        """
        rep movsb
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.SI = 0x0004
        self.cpu.regs.ES = 0x0002
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.CX = 3
        self.memory.mem_write_byte(19, 0x11)
        self.memory.mem_write_byte(20, 0x22)
        self.memory.mem_write_byte(21, 0x33)
        self.memory.mem_write_byte(22, 0x44)
        self.memory.mem_write_byte(23, 0x55)
        self.load_code_string("F3 A4 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.CX, 0)
        self.assertEqual(self.cpu.regs.DI, 0x0007)
        self.assertEqual(self.cpu.regs.DI, 0x0007)
        self.assertEqual(self.memory.mem_read_byte(35), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(36), 0x22)
        self.assertEqual(self.memory.mem_read_byte(37), 0x33)
        self.assertEqual(self.memory.mem_read_byte(38), 0x44)
        self.assertEqual(self.memory.mem_read_byte(39), 0x00) # Should be unmodified.
        
    def test_rep_movsw(self):
        """
        rep movsw
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.SI = 0x0004
        self.cpu.regs.ES = 0x0002
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.CX = 2
        self.memory.mem_write_byte(19, 0x11)
        self.memory.mem_write_byte(20, 0x22)
        self.memory.mem_write_byte(21, 0x33)
        self.memory.mem_write_byte(22, 0x44)
        self.memory.mem_write_byte(23, 0x55)
        self.memory.mem_write_byte(24, 0x66)
        self.load_code_string("F3 A5 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.CX, 0)
        self.assertEqual(self.cpu.regs.DI, 0x0008)
        self.assertEqual(self.cpu.regs.DI, 0x0008)
        self.assertEqual(self.memory.mem_read_byte(35), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(36), 0x22)
        self.assertEqual(self.memory.mem_read_byte(37), 0x33)
        self.assertEqual(self.memory.mem_read_byte(38), 0x44)
        self.assertEqual(self.memory.mem_read_byte(39), 0x55)
        self.assertEqual(self.memory.mem_read_byte(40), 0x00) # Should be unmodified.
        
class SegmentOverrideTests(BaseOpcodeAcceptanceTests):
    def test_get_data_segment_with_override(self):
        self.cpu.regs.DS = 0x1122
        self.cpu.regs.ES = 0x3344
        self.cpu.regs.CS = 0x5566
        self.cpu.regs.SS = 0x7788
        
        self.cpu.segment_override = None
        self.assertEqual(self.cpu.get_data_segment(), 0x1122)
        
        self.cpu.segment_override = "DS"
        self.assertEqual(self.cpu.get_data_segment(), 0x1122)
        self.cpu.segment_override = "ES"
        self.assertEqual(self.cpu.get_data_segment(), 0x3344)
        self.cpu.segment_override = "CS"
        self.assertEqual(self.cpu.get_data_segment(), 0x5566)
        self.cpu.segment_override = "SS"
        self.assertEqual(self.cpu.get_data_segment(), 0x7788)
        
    def test_get_extra_segment_with_override(self):
        self.cpu.regs.DS = 0x1122
        self.cpu.regs.ES = 0x3344
        self.cpu.regs.CS = 0x5566
        self.cpu.regs.SS = 0x7788
        
        self.cpu.segment_override = None
        self.assertEqual(self.cpu.get_extra_segment(), 0x3344)
        
        self.cpu.segment_override = "DS"
        self.assertEqual(self.cpu.get_extra_segment(), 0x1122)
        self.cpu.segment_override = "ES"
        self.assertEqual(self.cpu.get_extra_segment(), 0x3344)
        self.cpu.segment_override = "CS"
        self.assertEqual(self.cpu.get_extra_segment(), 0x5566)
        self.cpu.segment_override = "SS"
        self.assertEqual(self.cpu.get_extra_segment(), 0x7788)
        
    def test_es_override(self):
        """
        mov [es:bx], al
        mov [bx], ah
        hlt
        """
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.ES = 0x0002
        self.cpu.regs.AH = 0x55
        self.cpu.regs.AL = 0xAA
        self.cpu.regs.BX = 0
        self.load_code_string("26 88 07 88 27 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.memory.mem_read_byte(16), 0x55) # Normally uses DS.
        self.assertEqual(self.memory.mem_read_byte(32), 0xAA) # Overridden to use ES.
        
    def test_cs_override(self):
        """
        mov [cs:bx], al
        mov [bx], ah
        hlt
        """
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.AH = 0x55
        self.cpu.regs.AL = 0xAA
        self.cpu.regs.BX = 0
        self.load_code_string("2E 88 07 88 27 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.memory.mem_read_byte(0), 0xAA) # Overridden to use CS.
        self.assertEqual(self.memory.mem_read_byte(16), 0x55) # Normally uses DS.
        
class MovsOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_movsb_incrementing(self):
        """
        movsb
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.SI = 0x0004
        self.cpu.regs.ES = 0x0002
        self.cpu.regs.DI = 0x0004
        self.memory.mem_write_byte(19, 0x11)
        self.memory.mem_write_byte(20, 0x22)
        self.memory.mem_write_byte(21, 0x33)
        self.load_code_string("A4 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DS, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SI, 0x0005)
        self.assertEqual(self.cpu.regs.ES, 0x0002) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DI, 0x0005)
        self.assertEqual(self.memory.mem_read_byte(19), 0x11) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x22) # Should be unmodified
        self.assertEqual(self.memory.mem_read_byte(21), 0x33) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(35), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(36), 0x22)
        self.assertEqual(self.memory.mem_read_byte(37), 0x00) # Should be unmodified.
        
    def test_movsb_decrementing(self):
        """
        movsb
        hlt
        """
        self.cpu.flags.direction = True
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.SI = 0x0004
        self.cpu.regs.ES = 0x0002
        self.cpu.regs.DI = 0x0004
        self.memory.mem_write_byte(19, 0x11)
        self.memory.mem_write_byte(20, 0x22)
        self.memory.mem_write_byte(21, 0x33)
        self.load_code_string("A4 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DS, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SI, 0x0003)
        self.assertEqual(self.cpu.regs.ES, 0x0002) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DI, 0x0003)
        self.assertEqual(self.memory.mem_read_byte(19), 0x11) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x22) # Should be unmodified
        self.assertEqual(self.memory.mem_read_byte(21), 0x33) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(35), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(36), 0x22)
        self.assertEqual(self.memory.mem_read_byte(37), 0x00) # Should be unmodified.
        
    def test_movsw_incrementing(self):
        """
        movsw
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.SI = 0x0004
        self.cpu.regs.ES = 0x0002
        self.cpu.regs.DI = 0x0004
        self.memory.mem_write_byte(19, 0x11)
        self.memory.mem_write_byte(20, 0x22)
        self.memory.mem_write_byte(21, 0x33)
        self.load_code_string("A5 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DS, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SI, 0x0006)
        self.assertEqual(self.cpu.regs.ES, 0x0002) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DI, 0x0006)
        self.assertEqual(self.memory.mem_read_byte(19), 0x11) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x22) # Should be unmodified
        self.assertEqual(self.memory.mem_read_byte(21), 0x33) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(35), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(36), 0x22)
        self.assertEqual(self.memory.mem_read_byte(37), 0x33)
        
    def test_movsw_decrementing(self):
        """
        movsw
        hlt
        """
        self.cpu.flags.direction = True
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.SI = 0x0004
        self.cpu.regs.ES = 0x0002
        self.cpu.regs.DI = 0x0004
        self.memory.mem_write_byte(19, 0x11)
        self.memory.mem_write_byte(20, 0x22)
        self.memory.mem_write_byte(21, 0x33)
        self.load_code_string("A5 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DS, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SI, 0x0002)
        self.assertEqual(self.cpu.regs.ES, 0x0002) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DI, 0x0002)
        self.assertEqual(self.memory.mem_read_byte(19), 0x11) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x22) # Should be unmodified
        self.assertEqual(self.memory.mem_read_byte(21), 0x33) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(35), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(36), 0x22)
        self.assertEqual(self.memory.mem_read_byte(37), 0x33)
        
class PushOpcodeTests(BaseOpcodeAcceptanceTests):
    def setUp(self):
        super(PushOpcodeTests, self).setUp()
        
        # SS:SP => 0010:0100 => 0x00200
        self.cpu.regs.SS = 0x0010
        self.cpu.regs.SP = 0x0100
        
    def test_push_rm16(self):
        """
        push word [value]
        hlt
        value:
            dw 0xCAFE
        """
        self.load_code_string("FF 36 05 00 F4 FE CA")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0010) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x00FE)
        self.assertEqual(self.memory.mem_read_word(0x001FE), 0xCAFE)
        
    def test_push_es(self):
        """
        push es
        hlt
        """
        self.cpu.regs.ES = 0x1234
        self.load_code_string("06 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0010) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x00FE)
        self.assertEqual(self.memory.mem_read_word(0x001FE), 0x1234)
        
    def test_push_cs(self):
        """
        push cs
        hlt
        """
        self.memory.mem_write_word(0x001FE, 0x1234)
        self.load_code_string("0E F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0010) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x00FE)
        # CS is 0x0000 but it's where the code is running from, so we can't touch it.
        self.assertEqual(self.memory.mem_read_word(0x001FE), 0x0000)
        
    def test_push_ds(self):
        """
        push ds
        hlt
        """
        self.cpu.regs.DS = 0x5643
        self.load_code_string("1E F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0010) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x00FE)
        self.assertEqual(self.memory.mem_read_word(0x001FE), 0x5643)
        
    def test_push_ss(self):
        """
        push ss
        hlt
        """
        self.load_code_string("16 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0010) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x00FE)
        # SS is 0x0010 from the common setUp().
        self.assertEqual(self.memory.mem_read_word(0x001FE), 0x0010)
        
class PopOpcodeTests(BaseOpcodeAcceptanceTests):
    def setUp(self):
        super(PopOpcodeTests, self).setUp()
        
        # SS:SP => 0010:0100 => 0x00200
        self.cpu.regs.SS = 0x0010
        self.cpu.regs.SP = 0x0100
        
    def test_pop_es(self):
        """
        pop es
        hlt
        """
        self.memory.mem_write_word(0x00200, 0x1234)
        self.load_code_string("07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0010) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x0102)
        self.assertEqual(self.cpu.regs.ES, 0x1234)
        
    def test_pop_ds(self):
        """
        pop ds
        hlt
        """
        self.memory.mem_write_word(0x00200, 0x9876)
        self.load_code_string("1F F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0010) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x0102)
        self.assertEqual(self.cpu.regs.DS, 0x9876)
        
    def test_pop_ss(self):
        """
        pop ss
        hlt
        """
        self.memory.mem_write_word(0x00200, 0x0030)
        self.load_code_string("17 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0030)
        self.assertEqual(self.cpu.regs.SP, 0x0102)
        
    def test_pop_rm16(self):
        """
        pop word [value]
        hlt
        value:
            dw 0xCAFE
        """
        self.memory.mem_write_word(0x00200, 0xBEEF)
        self.load_code_string("8F 06 05 00 F4 FE CA")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0010) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x0102)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xBEEF)
        
class XchgOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_xchg_r8_rm8(self):
        """
        xchg al, [value]
        hlt
        value:
            db 0xAA
        """
        self.cpu.regs.AL = 0x55
        self.load_code_string("86 06 05 00 F4 AA")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.memory.mem_read_byte(0x05), 0x55)
        self.assertEqual(self.cpu.regs.AL, 0xAA)
        
    def test_xchg_r16_rm16(self):
        """
        xchg ax, [value]
        hlt
        value:
            dw 0xCAFE
        """
        self.cpu.regs.AX = 0xFACE
        self.load_code_string("87 06 05 00 F4 FE CA")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFACE)
        self.assertEqual(self.cpu.regs.AX, 0xCAFE)
        
class NotOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_not_rm8(self):
        """
        not al
        hlt
        """
        self.cpu.regs.AX = 0xAA50
        self.load_code_string("F6 D0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xAAAF) # AH unmodified
        
    def test_not_rm16(self):
        """
        not ax
        hlt
        """
        self.cpu.regs.AX = 0xAF05
        self.load_code_string("F7 D0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x50FA)
        
class ModRMTests(BaseOpcodeAcceptanceTests):
    def setUp(self):
        super(ModRMTests, self).setUp()
        
        # Set these up for testing.
        self.cpu.regs.BX = 0x1000
        self.cpu.regs.BP = 0x8000
        self.cpu.regs.SI = 0x0200
        self.cpu.regs.DI = 0x0400
        
        # All of these tests will be either NOT or ADD instructions,
        # so we move IP to 1 to skip past it.
        self.cpu.regs.IP = 1
        
    def test_reg_field_word(self):
        """ Test the register field for a word instruction. """
        def run_test(code, expected):
            # Reset IP to 1 so we can run multiple checks in the same test.
            self.cpu.regs.IP = 1
            self.load_code_string(code)
            self.assertEqual(self.cpu.get_modrm_operands(16), (expected, ADDRESS, 0))
            
        run_test("03 06 00 00", "AX") # add ax, [0x0000]
        run_test("03 0E 00 00", "CX") # add cx, [0x0000]
        run_test("03 16 00 00", "DX") # add dx, [0x0000]
        run_test("03 1E 00 00", "BX") # add bx, [0x0000]
        run_test("03 26 00 00", "SP") # add sp, [0x0000]
        run_test("03 2E 00 00", "BP") # add bp, [0x0000]
        run_test("03 36 00 00", "SI") # add si, [0x0000]
        run_test("03 3E 00 00", "DI") # add di, [0x0000]
        
    def test_reg_field_byte(self):
        """ Test the register field for a byte instruction. """
        def run_test(code, expected):
            # Reset IP to 1 so we can run multiple checks in the same test.
            self.cpu.regs.IP = 1
            self.load_code_string(code)
            self.assertEqual(self.cpu.get_modrm_operands(8), (expected, ADDRESS, 0))
            
        run_test("02 06 00 00", "AL") # add al, [0x0000]
        run_test("02 0E 00 00", "CL") # add cl, [0x0000]
        run_test("02 16 00 00", "DL") # add dl, [0x0000]
        run_test("02 1E 00 00", "BL") # add bl, [0x0000]
        run_test("02 26 00 00", "AH") # add ah, [0x0000]
        run_test("02 2E 00 00", "CH") # add ch, [0x0000]
        run_test("02 36 00 00", "DH") # add dh, [0x0000]
        run_test("02 3E 00 00", "BH") # add bh, [0x0000]
        
    def test_mod_11_rm_is_word_reg(self):
        """ Test the case where r/m is a second word register. """
        def run_test(code, expected):
            # Reset IP to 1 so we can run multiple checks in the same test.
            self.cpu.regs.IP = 1
            self.load_code_string(code)
            # The 2 is for the NOT sub-opcode.
            self.assertEqual(self.cpu.get_modrm_operands(16, decode_register = False), (2, REGISTER, expected))
            
        run_test("F7 D0", "AX") # not ax
        run_test("F7 D1", "CX") # not cx
        run_test("F7 D2", "DX") # not dx
        run_test("F7 D3", "BX") # not bx
        run_test("F7 D4", "SP") # not sp
        run_test("F7 D5", "BP") # not bp
        run_test("F7 D6", "SI") # not si
        run_test("F7 D7", "DI") # not di
        
    def test_mod_11_rm_is_byte_reg(self):
        """ Test the case where r/m is a second byte register. """
        def run_test(code, expected):
            # Reset IP to 1 so we can run multiple checks in the same test.
            self.cpu.regs.IP = 1
            self.load_code_string(code)
            # The 2 is for the NOT sub-opcode.
            self.assertEqual(self.cpu.get_modrm_operands(8, decode_register = False), (2, REGISTER, expected))
            
        run_test("F6 D0", "AL") # not al
        run_test("F6 D1", "CL") # not cl
        run_test("F6 D2", "DL") # not dl
        run_test("F6 D3", "BL") # not bl
        run_test("F6 D4", "AH") # not ah
        run_test("F6 D5", "CH") # not ch
        run_test("F6 D6", "DH") # not dh
        run_test("F6 D7", "BH") # not bh
        
    def run_address_test(self, code, expected_address):
        """ Decode the ModRM field and check that the address matches. """
        # Reset IP to 1 so we can run multiple checks in the same test.
        self.cpu.regs.IP = 1
        # Track the number of bytes loaded so we can check that IP is correct at the end.
        expected_ip = self.load_code_string(code)
        # We aren't doing register testing so we will just assume 16 bits and toss the register.
        self.assertEqual(self.cpu.get_modrm_operands(16)[1:], (ADDRESS, expected_address))
        # Ensure that IP matches the number of bytes loaded.
        self.assertEqual(self.cpu.regs.IP, expected_ip)
        
    def test_mod_00_rm_110_absolute_address(self):
        self.run_address_test("F7 16 43 56", 0x5643) # not word [0x5643]
        self.run_address_test("F7 16 01 00", 0x0001) # not word [0x0001]
        self.run_address_test("F7 16 00 00", 0x0000) # not word [0x0000]
        
    def test_mod_00_all_modes_no_displacement(self):
        self.run_address_test("F7 10", 0x1200) # not word [bx + si]
        self.run_address_test("F7 11", 0x1400) # not word [bx + di]
        self.run_address_test("F7 12", 0x8200) # not word [bp + si]
        self.run_address_test("F7 13", 0x8400) # not word [bp + di]
        self.run_address_test("F7 14", 0x0200) # not word [si]
        self.run_address_test("F7 15", 0x0400) # not word [di]
        # This is not a mod 00 test, mod 00 rm 110 is handled above.
        # self.run_address_test("F7 56 00", 0x8000) # not word [bp]
        self.run_address_test("F7 17", 0x1000) # not word [bx]
        
    def test_mod_01_all_modes_byte_displacement(self):
        self.run_address_test("F7 50 01", 0x1200 + 1) # not word [bx + si + 1]
        self.run_address_test("F7 51 01", 0x1400 + 1) # not word [bx + di + 1]
        self.run_address_test("F7 52 01", 0x8200 + 1) # not word [bp + si + 1]
        self.run_address_test("F7 53 01", 0x8400 + 1) # not word [bp + di + 1]
        self.run_address_test("F7 54 01", 0x0200 + 1) # not word [si + 1]
        self.run_address_test("F7 55 01", 0x0400 + 1) # not word [di + 1]
        self.run_address_test("F7 56 01", 0x8000 + 1) # not word [bp + 1]
        self.run_address_test("F7 57 01", 0x1000 + 1) # not word [bx + 1]
        
    def test_mod_01_all_modes_byte_negative_displacement(self):
        self.run_address_test("F7 50 FF", 0x1200 - 1) # not word [bx + si - 1]
        self.run_address_test("F7 51 FF", 0x1400 - 1) # not word [bx + di - 1]
        self.run_address_test("F7 52 FF", 0x8200 - 1) # not word [bp + si - 1]
        self.run_address_test("F7 53 FF", 0x8400 - 1) # not word [bp + di - 1]
        self.run_address_test("F7 54 FF", 0x0200 - 1) # not word [si - 1]
        self.run_address_test("F7 55 FF", 0x0400 - 1) # not word [di - 1]
        self.run_address_test("F7 56 FF", 0x8000 - 1) # not word [bp - 1]
        self.run_address_test("F7 57 FF", 0x1000 - 1) # not word [bx - 1]
        
    def test_mod_10_all_modes_word_displacement(self):
        self.run_address_test("F7 90 00 01", 0x1200 + 0x100) # not word [bx + si]
        self.run_address_test("F7 91 00 01", 0x1400 + 0x100) # not word [bx + di]
        self.run_address_test("F7 92 00 01", 0x8200 + 0x100) # not word [bp + si]
        self.run_address_test("F7 93 00 01", 0x8400 + 0x100) # not word [bp + di]
        self.run_address_test("F7 94 00 01", 0x0200 + 0x100) # not word [si]
        self.run_address_test("F7 95 00 01", 0x0400 + 0x100) # not word [di]
        self.run_address_test("F7 96 00 01", 0x8000 + 0x100) # not word [bp]
        self.run_address_test("F7 97 00 01", 0x1000 + 0x100) # not word [bx]
        
    def test_mod_10_all_modes_word_negative_displacement(self):
        self.run_address_test("F7 90 00 FF", 0x1200 - 0x100) # not word [bx + si]
        self.run_address_test("F7 91 00 FF", 0x1400 - 0x100) # not word [bx + di]
        self.run_address_test("F7 92 00 FF", 0x8200 - 0x100) # not word [bp + si]
        self.run_address_test("F7 93 00 FF", 0x8400 - 0x100) # not word [bp + di]
        self.run_address_test("F7 94 00 FF", 0x0200 - 0x100) # not word [si]
        self.run_address_test("F7 95 00 FF", 0x0400 - 0x100) # not word [di]
        self.run_address_test("F7 96 00 FF", 0x8000 - 0x100) # not word [bp]
        self.run_address_test("F7 97 00 FF", 0x1000 - 0x100) # not word [bx]
        
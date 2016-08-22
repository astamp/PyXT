import unittest
import binascii

import six
from six.moves import range # pylint: disable=redefined-builtin 

from pyxt.constants import *
from pyxt.cpu import *
from pyxt.bus import Device
from pyxt.tests.utils import SystemBusTestable
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
        self.assertEqual(self.flags.value & 0x0FFF, 0)
        
    # Property tests.
    def test_carry_flag_property_get(self):
        self.assertFalse(self.flags.carry)
        self.flags.value |= FLAGS.CARRY
        self.assertTrue(self.flags.carry)
        
    def test_carry_flag_property_set(self):
        self.assertEqual(self.flags.value & 0x0FFF, 0)
        self.flags.carry = True
        self.assertEqual(self.flags.value & 0x0FFF, FLAGS.CARRY)
        self.flags.carry = False
        self.assertEqual(self.flags.value & 0x0FFF, 0)
        
    def test_parity_flag_property_get(self):
        self.assertFalse(self.flags.parity)
        self.flags.value |= FLAGS.PARITY
        self.assertTrue(self.flags.parity)
        
    def test_parity_flag_property_set(self):
        self.assertEqual(self.flags.value & 0x0FFF, 0)
        self.flags.parity = True
        self.assertEqual(self.flags.value & 0x0FFF, FLAGS.PARITY)
        self.flags.parity = False
        self.assertEqual(self.flags.value & 0x0FFF, 0)
        
    def test_adjust_flag_property_get(self):
        self.assertFalse(self.flags.adjust)
        self.flags.value |= FLAGS.ADJUST
        self.assertTrue(self.flags.adjust)
        
    def test_adjust_flag_property_set(self):
        self.assertEqual(self.flags.value & 0x0FFF, 0)
        self.flags.adjust = True
        self.assertEqual(self.flags.value & 0x0FFF, FLAGS.ADJUST)
        self.flags.adjust = False
        self.assertEqual(self.flags.value & 0x0FFF, 0)
        
    def test_zero_flag_property_get(self):
        self.assertFalse(self.flags.zero)
        self.flags.value |= FLAGS.ZERO
        self.assertTrue(self.flags.zero)
        
    def test_zero_flag_property_set(self):
        self.assertEqual(self.flags.value & 0x0FFF, 0)
        self.flags.zero = True
        self.assertEqual(self.flags.value & 0x0FFF, FLAGS.ZERO)
        self.flags.zero = False
        self.assertEqual(self.flags.value & 0x0FFF, 0)
        
    def test_sign_flag_property_get(self):
        self.assertFalse(self.flags.sign)
        self.flags.value |= FLAGS.SIGN
        self.assertTrue(self.flags.sign)
        
    def test_sign_flag_property_set(self):
        self.assertEqual(self.flags.value & 0x0FFF, 0)
        self.flags.sign = True
        self.assertEqual(self.flags.value & 0x0FFF, FLAGS.SIGN)
        self.flags.sign = False
        self.assertEqual(self.flags.value & 0x0FFF, 0)
        
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
            (0x10000,   True,   False,  True,   None),  # Carry
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
            (0x10000,   True,   False,  False,  None),  # Carry NOT MODIFIED
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
            (0x10000,   True,   False,  True,  None),   # Carry NOT MODIFIED
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
            (0x100,   True,   False,  True,   None),  # Carry
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
            (0x100,   True,   False,  False,  None),  # Carry NOT MODIFIED
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
            (0x100,   True,   False,  True,  None),   # Carry NOT MODIFIED
            (0x03,    False,  False,  True,  True),   # Even parity
            (0x07,    False,  False,  True,  False),  # Odd parity
        ]
        
        self.flags.carry = True
        for args in data:
            self.run_set_from_alu_test(self.flags.set_from_alu_no_carry_byte, *args)
            
    def test_clear_logical(self):
        # Not all can be set.
        self.flags.value = 0xFFFF
        original_flags = self.flags.value
        
        self.flags.clear_logical()
        # Make sure it does what it says.
        self.assertFalse(self.flags.carry)
        self.assertFalse(self.flags.overflow)
        
        # And only changed those flags.
        changed_flags = original_flags ^ self.flags.value
        self.assertEqual(changed_flags, FLAGS.CARRY | FLAGS.OVERFLOW)
        
    def test_808x_reserved_bits(self):
        # Try to clear all flags.
        self.flags.value = 0x0000
        
        # These should not be able to be cleared:
        self.assertEqual(self.flags.value, FLAGS.RESERVED_4 | FLAGS.NESTED | FLAGS.IOPL_1 | FLAGS.IOPL_0)
        
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
        
    def test_initial_values(self):
        self.assertEqual(self.regs.AX, 0)
        self.assertEqual(self.regs.BX, 0)
        self.assertEqual(self.regs.CX, 0)
        self.assertEqual(self.regs.DX, 0)
        
        self.assertEqual(self.regs.SI, 0)
        self.assertEqual(self.regs.DI, 0)
        self.assertEqual(self.regs.BP, 0)
        self.assertEqual(self.regs.SP, 0)
        
        self.assertEqual(self.regs.IP, 0)
        
        self.assertEqual(self.regs.CS, 0xFFFF)
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
        
    def run_to_halt(self, max_instructions = 1000, starting_ip = 0):
        """
        Run the CPU until it halts, returning the number of instructions executed.
        
        If it runs for more than max_instructions the test immediately fails.
        """
        # Reset these in case there are multiple runs in the same test.
        self.cpu.regs.IP = starting_ip
        self.cpu.hlt = False
        
        instruction_count = 0
        while not self.cpu.hlt:
            self.cpu.fetch()
            instruction_count += 1
            if instruction_count > max_instructions:
                self.fail("Runaway detected, terminated after %d instructions." % max_instructions)
                
        return instruction_count
        
    def assert_flags(self, flags):
        """ Pass in a string of oditszapc asserting the lowercase are clear and the uppercase are set. """
        for char in flags:
            if char == "o":
                self.assertFalse(self.cpu.flags.overflow)
            elif char == "O":
                self.assertTrue(self.cpu.flags.overflow)
                
            elif char == "d":
                self.assertFalse(self.cpu.flags.direction)
            elif char == "D":
                self.assertTrue(self.cpu.flags.direction)
                
            elif char == "i":
                self.assertFalse(self.cpu.flags.interrupt_enable)
            elif char == "I":
                self.assertTrue(self.cpu.flags.interrupt_enable)
                
            elif char == "t":
                self.assertFalse(self.cpu.flags.trap)
            elif char == "T":
                self.assertTrue(self.cpu.flags.trap)
                
            elif char == "s":
                self.assertFalse(self.cpu.flags.sign)
            elif char == "S":
                self.assertTrue(self.cpu.flags.sign)
                
            elif char == "z":
                self.assertFalse(self.cpu.flags.zero)
            elif char == "Z":
                self.assertTrue(self.cpu.flags.zero)
                
            elif char == "a":
                self.assertFalse(self.cpu.flags.adjust)
            elif char == "A":
                self.assertTrue(self.cpu.flags.adjust)
                
            elif char == "p":
                self.assertFalse(self.cpu.flags.parity)
            elif char == "P":
                self.assertTrue(self.cpu.flags.parity)
                
            elif char == "c":
                self.assertFalse(self.cpu.flags.carry)
            elif char == "C":
                self.assertTrue(self.cpu.flags.carry)
                
            else:
                self.fail("Invalid char for FLAGS: %r" % char)
                
class AddOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_add_rm8_r8(self):
        """
        add [value], al
        hlt
        value:
            db 1
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("00 06 05 00 F4 01")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 7)
        self.assertEqual(self.memory.mem_read_byte(0x05), 8)
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_add_rm16_r16(self):
        """
        add [value], ax
        hlt
        value:
            dw 0xFF
        """
        self.cpu.regs.AX = 7
        self.load_code_string("01 06 05 00 F4 FF 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 7)
        self.assertEqual(self.memory.mem_read_word(0x05), 0x0106)
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_add_r8_rm8(self):
        """
        add al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("02 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 29)
        self.assertEqual(self.memory.mem_read_byte(0x05), 22)
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_add_r16_rm16(self):
        """
        add ax, [value]
        hlt
        value:
            dw 0xFF
        """
        self.cpu.regs.AX = 7
        self.load_code_string("03 06 05 00 F4 FF 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0106)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFF)
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_add_al_imm8(self):
        """
        add al, 7
        hlt
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("04 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 14)
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_add_ax_imm16(self):
        """
        add ax, word 2222
        hlt
        """
        self.cpu.regs.AX = 1234
        self.load_code_string("05 AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 3456)
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_add_overflow_8_bit(self):
        """
        add al, 100
        hlt
        """
        self.cpu.regs.AL = 100
        self.load_code_string("04 64 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 200)
        self.assert_flags("OSzpc") # ODITSZAPC
        
    def test_add_underflow_8_bit(self):
        """
        add al, -100
        hlt
        """
        self.cpu.regs.AL = -100
        self.load_code_string("04 9C F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 56) # -200
        self.assert_flags("OszpC") # ODITSZAPC
        
    def test_add_positive_no_overflow_8_bit(self):
        """
        add al, 100
        hlt
        """
        self.cpu.regs.AL = 10
        self.load_code_string("04 64 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 110)
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_add_negative_no_underflow_8_bit(self):
        """
        add al, -100
        hlt
        """
        self.cpu.regs.AL = -10
        self.load_code_string("04 9C F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 146) # -110
        self.assert_flags("oSzpC") # ODITSZAPC
        
    def test_add_overflow_16_bit(self):
        """
        add ax, 20000
        hlt
        """
        self.cpu.regs.AX = 20000
        self.load_code_string("05 20 4E F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 40000)
        self.assert_flags("OSzpc") # ODITSZAPC
        
    def test_add_underflow_16_bit(self):
        """
        add ax, -20000
        hlt
        """
        self.cpu.regs.AX = -20000
        self.load_code_string("05 E0 B1 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 25536) # -40000
        self.assert_flags("OszPC") # ODITSZAPC
        
    def test_add_positive_no_overflow_16_bit(self):
        """
        add ax, 20000
        hlt
        """
        self.cpu.regs.AX = 10000
        self.load_code_string("05 20 4E F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 30000)
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_add_negative_no_underflow_16_bit(self):
        """
        add ax, -20000
        hlt
        """
        self.cpu.regs.AX = -10000
        self.load_code_string("05 E0 B1 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 35536) # -30000
        self.assert_flags("oSzpC") # ODITSZAPC
        
class AdcOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_adc_operator_carry_clear(self):
        self.assertFalse(self.cpu.flags.carry)
        self.assertEqual(self.cpu.operator_adc_8(7, 5), 12)
        self.assertFalse(self.cpu.flags.carry)
        self.assertEqual(self.cpu.operator_adc_16(7, 5), 12)
        
    def test_adc_operator_carry_set(self):
        self.cpu.flags.carry = True
        self.assertTrue(self.cpu.flags.carry)
        self.assertEqual(self.cpu.operator_adc_8(7, 5), 13)
        self.assertTrue(self.cpu.flags.carry)
        self.assertEqual(self.cpu.operator_adc_16(7, 5), 13)
        
    def test_adc_rm8_r8_carry_clear(self):
        """
        adc [value], al
        hlt
        value:
            db 1
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("10 06 05 00 F4 01")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 7)
        self.assertEqual(self.memory.mem_read_byte(0x05), 8)
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_adc_rm8_r8_carry_set(self):
        """
        adc [value], al
        hlt
        value:
            db 1
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("10 06 05 00 F4 01")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 7)
        self.assertEqual(self.memory.mem_read_byte(0x05), 9)
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_adc_rm16_r16_carry_clear(self):
        """
        adc [value], ax
        hlt
        value:
            dw 0xFF
        """
        self.cpu.regs.AX = 7
        self.load_code_string("11 06 05 00 F4 FF 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 7)
        self.assertEqual(self.memory.mem_read_word(0x05), 0x0106)
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_adc_rm16_r16_carry_set(self):
        """
        adc [value], ax
        hlt
        value:
            dw 0xFF
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AX = 7
        self.load_code_string("11 06 05 00 F4 FF 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 7)
        self.assertEqual(self.memory.mem_read_word(0x05), 0x0107)
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_adc_r8_rm8_carry_clear(self):
        """
        adc al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("12 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 29)
        self.assertEqual(self.memory.mem_read_byte(0x05), 22)
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_adc_r8_rm8_carry_set(self):
        """
        adc al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("12 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 30)
        self.assertEqual(self.memory.mem_read_byte(0x05), 22)
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_adc_r16_rm16_carry_clear(self):
        """
        adc ax, [value]
        hlt
        value:
            dw 0xFF
        """
        self.cpu.regs.AX = 7
        self.load_code_string("13 06 05 00 F4 FF 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0106)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFF)
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_adc_r16_rm16_carry_set(self):
        """
        adc ax, [value]
        hlt
        value:
            dw 0xFF
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AX = 7
        self.load_code_string("13 06 05 00 F4 FF 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0107)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFF)
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_adc_al_imm8_carry_clear(self):
        """
        adc al, 7
        hlt
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("14 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 14)
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_adc_al_imm8_carry_set(self):
        """
        adc al, 7
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("14 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 15)
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_adc_ax_imm16_carry_clear(self):
        """
        adc ax, word 2222
        hlt
        """
        self.cpu.regs.AX = 1234
        self.load_code_string("15 AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 3456)
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_adc_ax_imm16_carry_set(self):
        """
        adc ax, word 2222
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AX = 1234
        self.load_code_string("15 AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 3457)
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_adc_overflow_8_bit(self):
        """
        adc al, 100
        hlt
        """
        self.cpu.regs.AL = 100
        self.load_code_string("14 64 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 200)
        self.assert_flags("OSzpc") # ODITSZAPC
        
    def test_adc_underflow_8_bit(self):
        """
        adc al, -100
        hlt
        """
        self.cpu.regs.AL = -100
        self.load_code_string("14 9C F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 56) # -200
        self.assert_flags("OszpC") # ODITSZAPC
        
    def test_adc_positive_no_overflow_8_bit(self):
        """
        adc al, 100
        hlt
        """
        self.cpu.regs.AL = 10
        self.load_code_string("14 64 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 110)
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_adc_negative_no_underflow_8_bit(self):
        """
        adc al, -100
        hlt
        """
        self.cpu.regs.AL = -10
        self.load_code_string("14 9C F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 146) # -110
        self.assert_flags("oSzpC") # ODITSZAPC
        
    def test_adc_overflow_16_bit(self):
        """
        adc ax, 20000
        hlt
        """
        self.cpu.regs.AX = 20000
        self.load_code_string("15 20 4E F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 40000)
        self.assert_flags("OSzpc") # ODITSZAPC
        
    def test_adc_underflow_16_bit(self):
        """
        adc ax, -20000
        hlt
        """
        self.cpu.regs.AX = -20000
        self.load_code_string("15 E0 B1 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 25536) # -40000
        self.assert_flags("OszPC") # ODITSZAPC
        
    def test_adc_positive_no_overflow_16_bit(self):
        """
        adc ax, 20000
        hlt
        """
        self.cpu.regs.AX = 10000
        self.load_code_string("15 20 4E F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 30000)
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_adc_negative_no_underflow_16_bit(self):
        """
        adc ax, -20000
        hlt
        """
        self.cpu.regs.AX = -10000
        self.load_code_string("15 E0 B1 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 35536) # -30000
        self.assert_flags("oSzpC") # ODITSZAPC
        
class SubOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_sub_rm8_r8(self):
        """
        sub [value], al
        hlt
        value:
            db 50
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("28 06 05 00 F4 32")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 7)
        self.assertEqual(self.memory.mem_read_byte(0x05), 43)
        
    def test_sub_rm16_r16(self):
        """
        sub [value], ax
        hlt
        value:
            dw 10
        """
        self.cpu.regs.AX = 11
        self.load_code_string("29 06 05 00 F4 0A 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 11)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFFFF)
        
    def test_sub_r8_rm8(self):
        """
        sub al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("2A 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 241)
        self.assertEqual(self.memory.mem_read_byte(0x05), 22)
        
    def test_sub_r16_rm16(self):
        """
        sub ax, [value]
        hlt
        value:
            dw 1111
        """
        self.cpu.regs.AX = 2345
        self.load_code_string("2B 06 05 00 F4 57 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 1234)
        self.assertEqual(self.memory.mem_read_word(0x05), 1111)
        
    def test_sub_al_imm8(self):
        """
        sub al, 7
        hlt
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("2C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_sub_ax_imm16(self):
        """
        sub ax, word 2222
        hlt
        """
        self.cpu.regs.AX = 5643
        self.load_code_string("2D AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 3421)
        
    def test_sub_overflow_8_bit(self):
        """
        sub al, -100
        hlt
        """
        self.cpu.regs.AL = 100
        self.load_code_string("2C 9C F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 200)
        self.assert_flags("OSzpC") # ODITSZAPC
        
    def test_sub_underflow_8_bit(self):
        """
        sub al, 100
        hlt
        """
        self.cpu.regs.AL = -100
        self.load_code_string("2C 64 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 56) # -200
        self.assert_flags("Oszpc") # ODITSZAPC
        
    def test_sub_negative_no_overflow_8_bit(self):
        """
        sub al, -100
        hlt
        """
        self.cpu.regs.AL = 10
        self.load_code_string("2C 9C F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 110)
        self.assert_flags("oszpC") # ODITSZAPC
        # Note sure why carry is set above, but DEBUG.COM confirms...
        
    def test_sub_positive_no_underflow_8_bit(self):
        """
        sub al, 100
        hlt
        """
        self.cpu.regs.AL = -10
        self.load_code_string("2C 64 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 146) # -110
        self.assert_flags("oSzpc") # ODITSZAPC
        # Note sure why carry is clear above, but DEBUG.COM confirms...
        
    def test_sub_overflow_16_bit(self):
        """
        sub ax, -20000
        hlt
        """
        self.cpu.regs.AX = 20000
        self.load_code_string("2D E0 B1 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 40000)
        self.assert_flags("OSzpC") # ODITSZAPC
        
    def test_sub_underflow_16_bit(self):
        """
        sub ax, 20000
        hlt
        """
        self.cpu.regs.AX = -20000
        self.load_code_string("2D 20 4E F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 25536) # -40000
        self.assert_flags("OszPc") # ODITSZAPC
        
    def test_sub_negative_no_overflow_16_bit(self):
        """
        sub ax, -10000
        hlt
        """
        self.cpu.regs.AX = 20000
        self.load_code_string("2D F0 D8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 30000)
        self.assert_flags("oszPC") # ODITSZAPC
        # Note sure why carry is set above, but DEBUG.COM confirms...
        
    def test_sub_positive_no_underflow_16_bit(self):
        """
        sub ax, 10000
        hlt
        """
        self.cpu.regs.AX = -20000
        self.load_code_string("2D 10 27 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 35536) # -30000
        self.assert_flags("oSzpc") # ODITSZAPC
        # Note sure why carry is clear above, but DEBUG.COM confirms...
        
class SbbOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_sbb_operator_carry_clear(self):
        self.assertFalse(self.cpu.flags.carry)
        self.assertEqual(self.cpu.operator_sbb_8(7, 5), 2)
        self.assertFalse(self.cpu.flags.carry)
        self.assertEqual(self.cpu.operator_sbb_16(7, 5), 2)
        
    def test_sbb_operator_carry_set(self):
        self.cpu.flags.carry = True
        self.assertTrue(self.cpu.flags.carry)
        self.assertEqual(self.cpu.operator_sbb_8(7, 5), 1)
        self.assertTrue(self.cpu.flags.carry)
        self.assertEqual(self.cpu.operator_sbb_16(7, 5), 1)
        
    def test_sbb_rm8_r8_carry_clear(self):
        """
        sbb [value], al
        hlt
        value:
            db 50
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("18 06 05 00 F4 32")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 7)
        self.assertEqual(self.memory.mem_read_byte(0x05), 43)
        
    def test_sbb_rm8_r8_carry_set(self):
        """
        sbb [value], al
        hlt
        value:
            db 50
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("18 06 05 00 F4 32")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 7)
        self.assertEqual(self.memory.mem_read_byte(0x05), 42)
        
    def test_sbb_rm16_r16_carry_clear(self):
        """
        sbb [value], ax
        hlt
        value:
            dw 10
        """
        self.cpu.regs.AX = 11
        self.load_code_string("19 06 05 00 F4 0A 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 11)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFFFF)
        
    def test_sbb_rm16_r16_carry_set(self):
        """
        sbb [value], ax
        hlt
        value:
            dw 10
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AX = 11
        self.load_code_string("19 06 05 00 F4 0A 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 11)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFFFE)
        
    def test_sbb_r8_rm8_carry_clear(self):
        """
        sbb al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("1A 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 241)
        self.assertEqual(self.memory.mem_read_byte(0x05), 22)
        
    def test_sbb_r8_rm8_carry_set(self):
        """
        sbb al, [value]
        hlt
        value:
            db 22
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("1A 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 240)
        self.assertEqual(self.memory.mem_read_byte(0x05), 22)
        
    def test_sbb_r16_rm16_carry_clear(self):
        """
        sbb ax, [value]
        hlt
        value:
            dw 1111
        """
        self.cpu.regs.AX = 2345
        self.load_code_string("1B 06 05 00 F4 57 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 1234)
        self.assertEqual(self.memory.mem_read_word(0x05), 1111)
        
    def test_sbb_r16_rm16_carry_set(self):
        """
        sbb ax, [value]
        hlt
        value:
            dw 1111
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AX = 2345
        self.load_code_string("1B 06 05 00 F4 57 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 1233)
        self.assertEqual(self.memory.mem_read_word(0x05), 1111)
        
    def test_sbb_al_imm8_carry_clear(self):
        """
        sbb al, 7
        hlt
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("1C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_sbb_al_imm8_carry_set(self):
        """
        sbb al, 7
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("1C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0xFF)
        
    def test_sbb_ax_imm16_carry_clear(self):
        """
        sbb ax, word 2222
        hlt
        """
        self.cpu.regs.AX = 5643
        self.load_code_string("1D AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 3421)
        
    def test_sbb_ax_imm16_carry_set(self):
        """
        sbb ax, word 2222
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AX = 5643
        self.load_code_string("1D AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 3420)
        
    def test_sbb_overflow_8_bit(self):
        """
        sbb al, -100
        hlt
        """
        self.cpu.regs.AL = 100
        self.load_code_string("1C 9C F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 200)
        self.assert_flags("OSzpC") # ODITSZAPC
        
    def test_sbb_underflow_8_bit(self):
        """
        sbb al, 100
        hlt
        """
        self.cpu.regs.AL = -100
        self.load_code_string("1C 64 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 56) # -200
        self.assert_flags("Oszpc") # ODITSZAPC
        
    def test_sbb_negative_no_overflow_8_bit(self):
        """
        sbb al, -100
        hlt
        """
        self.cpu.regs.AL = 10
        self.load_code_string("1C 9C F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 110)
        self.assert_flags("oszpC") # ODITSZAPC
        # Note sure why carry is set above, but DEBUG.COM confirms...
        
    def test_sbb_positive_no_underflow_8_bit(self):
        """
        sbb al, 100
        hlt
        """
        self.cpu.regs.AL = -10
        self.load_code_string("1C 64 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 146) # -110
        self.assert_flags("oSzpc") # ODITSZAPC
        # Note sure why carry is clear above, but DEBUG.COM confirms...
        
    def test_sbb_overflow_16_bit(self):
        """
        sbb ax, -20000
        hlt
        """
        self.cpu.regs.AX = 20000
        self.load_code_string("1D E0 B1 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 40000)
        self.assert_flags("OSzpC") # ODITSZAPC
        
    def test_sbb_underflow_16_bit(self):
        """
        sbb ax, 20000
        hlt
        """
        self.cpu.regs.AX = -20000
        self.load_code_string("1D 20 4E F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 25536) # -40000
        self.assert_flags("OszPc") # ODITSZAPC
        
    def test_sbb_negative_no_overflow_16_bit(self):
        """
        sbb ax, -10000
        hlt
        """
        self.cpu.regs.AX = 20000
        self.load_code_string("1D F0 D8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 30000)
        self.assert_flags("oszPC") # ODITSZAPC
        # Note sure why carry is set above, but DEBUG.COM confirms...
        
    def test_sbb_positive_no_underflow_16_bit(self):
        """
        sbb ax, 10000
        hlt
        """
        self.cpu.regs.AX = -20000
        self.load_code_string("1D 10 27 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 35536) # -30000
        self.assert_flags("oSzpc") # ODITSZAPC
        # Note sure why carry is clear above, but DEBUG.COM confirms...
        
    def test_sbb_8x_8_bit(self):
        """
        sbb bl, 20
        hlt
        """
        self.cpu.regs.BL = 50
        self.load_code_string("80 DB 14 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BL, 30)
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_sbb_8x_16_bit(self):
        """
        sbb bx, 2000
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs.BX = 5000
        self.load_code_string("81 DB D0 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 2999)
        self.assert_flags("oszPc") # ODITSZAPC
        
class CmpOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_cmp_rm8_r8_none(self):
        """
        cmp [value], al
        hlt
        value:
            db 50
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("38 06 05 00 F4 32")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 7) # Should be unmodified.
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
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 50
        self.load_code_string("38 06 05 00 F4 32")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 50) # Should be unmodified.
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
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 51
        self.load_code_string("38 06 05 00 F4 32")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 51) # Should be unmodified.
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
        self.cpu.regs.AX = 11
        self.load_code_string("39 06 05 00 F4 E8 03")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 11) # Should be unmodified.
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
        self.cpu.regs.AX = 1000
        self.load_code_string("39 06 05 00 F4 E8 03")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 1000) # Should be unmodified.
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
        self.cpu.regs.AX = 1001
        self.load_code_string("39 06 05 00 F4 E8 03")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 1001) # Should be unmodified.
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
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 23
        self.load_code_string("3A 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 23) # Should be unmodified.
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
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 22
        self.load_code_string("3A 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 22) # Should be unmodified.
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
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 21
        self.load_code_string("3A 06 05 00 F4 16")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 21) # Should be unmodified.
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
        self.cpu.regs.AX = 2000
        self.load_code_string("3B 06 05 00 F4 57 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 2000) # Should be unmodified.
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
        self.cpu.regs.AX = 1111
        self.load_code_string("3B 06 05 00 F4 57 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 1111) # Should be unmodified.
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
        self.cpu.regs.AX = 500
        self.load_code_string("3B 06 05 00 F4 57 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 500) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_word(0x05), 1111) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_cmp_al_imm8_none(self):
        """
        cmp al, 7
        hlt
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 8
        self.load_code_string("3C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 8) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_al_imm8_zero(self):
        """
        cmp al, 7
        hlt
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 7
        self.load_code_string("3C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 7) # Should be unmodified.
        
        self.assertTrue(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_al_imm8_sign_carry(self):
        """
        cmp al, 7
        hlt
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 6
        self.load_code_string("3C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 6) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_cmp_ax_imm16_none(self):
        """
        cmp ax, word 2222
        hlt
        """
        self.cpu.regs.AX = 5643
        self.load_code_string("3D AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 5643) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_ax_imm16_zero(self):
        """
        cmp ax, word 2222
        hlt
        """
        self.cpu.regs.AX = 2222
        self.load_code_string("3D AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 2222) # Should be unmodified.
        
        self.assertTrue(self.cpu.flags.zero)
        self.assertFalse(self.cpu.flags.sign)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_cmp_ax_imm16_sign_carry(self):
        """
        cmp ax, word 2222
        hlt
        """
        self.cpu.regs.AX = 0
        self.load_code_string("3D AE 08 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0) # Should be unmodified.
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_cmp_overflow_8_bit(self):
        """
        cmp al, -100
        hlt
        """
        self.cpu.regs.AL = 100
        self.load_code_string("3C 9C F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 100) # Should be unmodified.
        self.assert_flags("OSzpC") # ODITSZAPC
        
    def test_cmp_underflow_8_bit(self):
        """
        cmp al, 100
        hlt
        """
        self.cpu.regs.AL = -100
        self.load_code_string("3C 64 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 156) # -100 Should be unmodified.
        self.assert_flags("Oszpc") # ODITSZAPC
        
    def test_cmp_negative_no_overflow_8_bit(self):
        """
        cmp al, -100
        hlt
        """
        self.cpu.regs.AL = 10
        self.load_code_string("3C 9C F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 10) # Should be unmodified.
        self.assert_flags("oszpC") # ODITSZAPC
        # Note sure why carry is set above, but DEBUG.COM confirms...
        
    def test_cmp_positive_no_underflow_8_bit(self):
        """
        cmp al, 100
        hlt
        """
        self.cpu.regs.AL = -10
        self.load_code_string("3C 64 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 246) # -10 Should be unmodified.
        self.assert_flags("oSzpc") # ODITSZAPC
        # Note sure why carry is clear above, but DEBUG.COM confirms...
        
    def test_cmp_overflow_16_bit(self):
        """
        cmp ax, -20000
        hlt
        """
        self.cpu.regs.AX = 20000
        self.load_code_string("3D E0 B1 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 20000) # Should be unmodified.
        self.assert_flags("OSzpC") # ODITSZAPC
        
    def test_cmp_underflow_16_bit(self):
        """
        cmp ax, 20000
        hlt
        """
        self.cpu.regs.AX = -20000
        self.load_code_string("3D 20 4E F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 45536) # -20000 Should be unmodified.
        self.assert_flags("OszPc") # ODITSZAPC
        
    def test_cmp_negative_no_overflow_16_bit(self):
        """
        cmp ax, -10000
        hlt
        """
        self.cpu.regs.AX = 20000
        self.load_code_string("3D F0 D8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 20000) # Should be unmodified.
        self.assert_flags("oszPC") # ODITSZAPC
        # Note sure why carry is set above, but DEBUG.COM confirms...
        
    def test_cmp_positive_no_underflow_16_bit(self):
        """
        cmp ax, 10000
        hlt
        """
        self.cpu.regs.AX = -20000
        self.load_code_string("3D 10 27 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 45536) # -20000 Should be unmodified.
        self.assert_flags("oSzpc") # ODITSZAPC
        # Note sure why carry is clear above, but DEBUG.COM confirms...
        
        
    def test_rm8_imm8_none(self):
        """
        cmp dl, 0x10
        hlt
        """
        self.cpu.regs.DL = 0x70
        self.load_code_string("80 FA 10 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DL, 0x70) # Should be unmodified.
        self.assert_flags("oszPc")
        
    def test_rm8_imm8_zero(self):
        """
        cmp dl, 0x10
        hlt
        """
        self.cpu.regs.DL = 0x10
        self.load_code_string("80 FA 10 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DL, 0x10) # Should be unmodified.
        self.assert_flags("osZPc")
        
    def test_rm8_imm8_sign_carry(self):
        """
        cmp dl, 0x10
        hlt
        """
        self.cpu.regs.DL = 0x0F
        self.load_code_string("80 FA 10 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DL, 0x0F) # Should be unmodified.
        self.assert_flags("oSzPC")
        
    # Not testing all cases with 8x just one to make sure it's connected.
    def test_rm8_imm8_overflow(self):
        """
        cmp dl, -100
        hlt
        """
        self.cpu.regs.DL = 100
        self.load_code_string("80 FA 9C F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DL, 100) # Should be unmodified.
        self.assert_flags("OSzpC")
        
    def test_rm16_imm16_none(self):
        """
        cmp dx, 0x1000
        hlt
        """
        self.cpu.regs.DX = 0x7000
        self.load_code_string("81 FA 00 10 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DX, 0x7000) # Should be unmodified.
        self.assert_flags("oszPc")
        
    def test_rm16_imm16_zero(self):
        """
        cmp dx, 0x1000
        hlt
        """
        self.cpu.regs.DX = 0x1000
        self.load_code_string("81 FA 00 10 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DX, 0x1000) # Should be unmodified.
        self.assert_flags("osZPc")
        
    def test_rm16_imm16_sign_carry(self):
        """
        cmp dx, 0x1000
        hlt
        """
        self.cpu.regs.DX = 0x0FFF
        self.load_code_string("81 FA 00 10 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DX, 0x0FFF) # Should be unmodified.
        self.assert_flags("oSzPC")
        
    # Not testing all cases with 8x just one to make sure it's connected.
    def test_rm16_imm16_overflow(self):
        """
        cmp dx, -20000
        hlt
        """
        self.cpu.regs.DX = 20000
        self.load_code_string("81 FA E0 B1 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DX, 20000) # Should be unmodified.
        self.assert_flags("OSzpC")
        
class OrOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_or_rm8_r8(self):
        """
        or [value], al
        hlt
        value:
            db 0x0F
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 0x18
        self.load_code_string("08 06 05 00 F4 0F")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0x18)
        self.assertEqual(self.memory.mem_read_byte(0x05), 0x1F)
        
    def test_or_rm16_r16(self):
        """
        or [value], ax
        hlt
        value:
            dw 0x01A5
        """
        self.cpu.regs.AX = 0x015A
        self.load_code_string("09 06 05 00 F4 A5 01")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x015A)
        self.assertEqual(self.memory.mem_read_word(0x05), 0x01FF)
        
    def test_or_r8_rm8(self):
        """
        or al, [value]
        hlt
        value:
            db 0x04
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 0x08
        self.load_code_string("0A 06 05 00 F4 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0x0C)
        self.assertEqual(self.memory.mem_read_byte(0x05), 0x04)
        
    def test_or_r16_rm16(self):
        """
        or bx, [value]
        hlt
        value:
            dw 0xF000
        """
        self.cpu.regs.BX = 0x0ACE
        self.load_code_string("0B 1E 05 00 F4 00 F0")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 0xFACE)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xF000)
        
    def test_or_al_imm8(self):
        """
        or al, 0x07
        hlt
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 0x1E
        self.load_code_string("0C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0x1F)
        
    def test_or_ax_imm16(self):
        """
        or ax, 0xC0F0
        hlt
        """
        self.cpu.regs.AX = 0x0A0E
        self.load_code_string("0D F0 C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xCAFE)
        
    def test_or_clears_carry_overflow(self):
        """
        or al, 0x07
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.load_code_string("0C 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_or_8x_8_bit(self):
        """
        or bl, 0x07
        hlt
        """
        self.cpu.regs.BH = 0xA5
        self.cpu.regs.BL = 0x18
        self.load_code_string("80 CB 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.BL, 0x1F)
        
    def test_or_8x_16_bit(self):
        """
        or bx, 0xC0F0
        hlt
        """
        self.cpu.regs.BX = 0x0A0E
        self.load_code_string("81 CB F0 C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 0xCAFE)
        
    def test_or_8x_clears_carry_overflow(self):
        """
        or bx, 0xC0F0
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.cpu.regs.BX = 0x0A0E
        self.load_code_string("81 CB F0 C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 0xCAFE)
        self.assert_flags("oSzpc") # ODITSZAPC
        
class AndOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_and_rm8_r8(self):
        """
        and [value], al
        hlt
        value:
            db 0x0F
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 0x7E
        self.load_code_string("20 06 05 00 F4 0F")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0x7E)
        self.assertEqual(self.memory.mem_read_byte(0x05), 0x0E)
        
    def test_and_rm16_r16(self):
        """
        and [value], ax
        hlt
        value:
            dw 0xFACE
        """
        self.cpu.regs.AX = 0x0FF0
        self.load_code_string("21 06 05 00 F4 CE FA")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0FF0)
        self.assertEqual(self.memory.mem_read_word(0x05), 0x0AC0)
        
    def test_and_r8_rm8(self):
        """
        and al, [value]
        hlt
        value:
            db 0x3C
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 0xA5
        self.load_code_string("22 06 05 00 F4 3C")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0x24)
        self.assertEqual(self.memory.mem_read_byte(0x05), 0x3C)
        
    def test_and_r16_rm16(self):
        """
        and bx, [value]
        hlt
        value:
            dw 0xF000
        """
        self.cpu.regs.BX = 0xFACE
        self.load_code_string("23 1E 05 00 F4 00 F0")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 0xF000)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xF000)
        
    def test_and_al_imm8(self):
        """
        and al, 0x07
        hlt
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 0x1E
        self.load_code_string("24 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0x06)
        
    def test_and_ax_imm16(self):
        """
        and ax, 0xF00F
        hlt
        """
        self.cpu.regs.AX = 0xBEEF
        self.load_code_string("25 0F F0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xB00F)
        
    def test_and_clears_carry_overflow(self):
        """
        and al, 0x07
        hlt
        """
        self.cpu.regs.AL = 0x02
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.load_code_string("24 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_and_8x_8_bit(self):
        """
        and bl, 0x07
        hlt
        """
        self.cpu.regs.BH = 0xA5
        self.cpu.regs.BL = 0x1E
        self.load_code_string("80 E3 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.BL, 0x06)
        
    def test_and_8x_16_bit(self):
        """
        and bx, 0x7777
        hlt
        """
        self.cpu.regs.BX = 0x9ABC
        self.load_code_string("81 E3 77 77 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 0x1234)
        
    def test_and_8x_clears_carry_overflow(self):
        """
        and bx, 0x7777
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.cpu.regs.BX = 0x9ABC
        self.load_code_string("81 E3 77 77 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 0x1234)
        self.assert_flags("oszpc") # ODITSZAPC
        
class MovOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_mov_sreg_rm16(self):
        """
        mov es, [value]
        hlt
        value:
            dw 0xBEEF
        """
        self.cpu.regs.ES = 0x0000
        self.load_code_string("8E 06 05 00 F4 EF BE")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.ES, 0xBEEF)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xBEEF)
        
    def test_mov_rm16_sreg(self):
        """
        mov [value], es
        hlt
        value:
            dw 0x0000
        """
        self.cpu.regs.ES = 0xCAFE
        self.load_code_string("8C 06 05 00 F4 00 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.ES, 0xCAFE)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xCAFE)
        
    def test_mov_r16_rm16(self):
        """
        mov bx, [value]
        hlt
        value:
            dw 0x1234
        """
        self.cpu.regs.BX = 0x0000
        self.load_code_string("8B 1E 05 00 F4 34 12")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 0x1234)
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
        
    def test_cmc_was_clear(self):
        """
        cmc
        hlt
        """
        self.assertFalse(self.cpu.flags.carry)
        self.load_code_string("F5 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_cmc_was_set(self):
        """
        cmc
        hlt
        """
        self.cpu.flags.carry = True
        self.assertTrue(self.cpu.flags.carry)
        self.load_code_string("F5 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertFalse(self.cpu.flags.carry)
        
class LoopOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_loop(self):
        """
        again:
            loop again
        hlt
        """
        self.cpu.regs.CX = 3
        self.load_code_string("E2 FE F4")
        self.assertEqual(self.run_to_halt(), 4)
        self.assertEqual(self.cpu.regs.CX, 0x00)
        
    def test_loop_with_body(self):
        """
        again:
            inc ax
            loop again
        hlt
        """
        self.cpu.regs.CX = 3
        self.load_code_string("40 E2 FD F4")
        self.assertEqual(self.run_to_halt(), 7)
        self.assertEqual(self.cpu.regs.AX, 3)
        self.assertEqual(self.cpu.regs.CX, 0x00)
        
    def test_loop_does_not_modify_flags(self):
        """
        again:
            loop again
        hlt
        """
        self.cpu.flags.zero = False
        self.cpu.flags.sign = True
        self.cpu.flags.carry = True
        
        self.cpu.regs.CX = 3
        self.load_code_string("E2 FE F4")
        self.assertEqual(self.run_to_halt(), 4)
        
        self.assertFalse(self.cpu.flags.zero)
        self.assertTrue(self.cpu.flags.sign)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_loop_collapsed(self):
        """
        again:
            loop again
        hlt
        """
        self.cpu.collapse_delay_loops(True)
        
        self.cpu.regs.CX = 3
        self.load_code_string("E2 FE F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.CX, 0x00)
        
    def test_loop_with_body_cant_be_collapsed(self):
        """
        again:
            inc ax
            loop again
        hlt
        """
        self.cpu.collapse_delay_loops(True)
        
        self.cpu.regs.CX = 3
        self.load_code_string("40 E2 FD F4")
        self.assertEqual(self.run_to_halt(), 7)
        self.assertEqual(self.cpu.regs.AX, 3)
        self.assertEqual(self.cpu.regs.CX, 0x00)
        
    def test_loop_does_not_modify_flags_collapsed(self):
        """
        again:
            loop again
        hlt
        """
        self.cpu.collapse_delay_loops(True)
        
        self.cpu.flags.zero = False
        self.cpu.flags.sign = True
        self.cpu.flags.carry = True
        
        self.cpu.regs.CX = 3
        self.load_code_string("E2 FE F4")
        self.assertEqual(self.run_to_halt(), 2)
        
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
        return [port for port in range(1024)]
        
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
        self.assertEqual(self.cpu.regs.AL, 77)
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
        self.assertEqual(self.cpu.regs.AL, 77)
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
            self.assertFalse(self.cpu.flags.carry) # Should be unmodified.
            
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
        
    def test_inc_rm8_register(self):
        """
        inc al
        hlt
        """
        self.load_code_string("FE C0 F4")
        
        test_data = (
            (0, 1), # Start from zero.
            (0xFF, 0x00), # Byte rollover.
            (77, 78), # Random value.
        )
        
        self.cpu.regs.AH = 0xA5
        for (before, after) in test_data:
            self.cpu.regs.AL = before
            self.assertEqual(self.run_to_halt(), 2)
            self.assertEqual(self.cpu.regs.AL, after)
            self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
            self.assertFalse(self.cpu.flags.carry) # Should be unmodified.
            
    def test_inc_rm8_memory(self):
        """
        inc byte [foo]
        hlt
        foo:
            db 0x99
        """
        self.load_code_string("FE 06 05 00 F4 99")
        
        test_data = (
            (0, 1), # Start from zero.
            (0xFF, 0x00), # Byte rollover.
            (77, 78), # Random value.
        )
        
        for (before, after) in test_data:
            self.memory.mem_write_byte(5, before)
            self.assertEqual(self.run_to_halt(), 2)
            self.assertEqual(self.memory.mem_read_byte(5), after)
            self.assertFalse(self.cpu.flags.carry) # Should be unmodified.
            
    def test_inc_rm16_register(self):
        """
        db 0xFF, 0xC0 ; Extended form of inc AX.
        hlt
        """
        self.load_code_string("FF C0 F4")
        
        test_data = (
            (0, 1), # Start from zero.
            (0xFF, 0x0100), # Byte rollover.
            (5643, 5644), # Random value.
            (0xFFFF, 0), # Word rollover.
        )
        
        for (before, after) in test_data:
            self.cpu.regs.AX = before
            self.assertEqual(self.run_to_halt(), 2)
            self.assertEqual(self.cpu.regs.AX, after)
            self.assertFalse(self.cpu.flags.carry) # Should be unmodified.
            
    def test_inc_rm16_memory(self):
        """
        inc word [foo]
        hlt
        foo:
            dw 0x9999
        """
        self.load_code_string("FF 06 05 00 F4 99 99")
        
        test_data = (
            (0, 1), # Start from zero.
            (0xFF, 0x0100), # Byte rollover.
            (5643, 5644), # Random value.
            (0xFFFF, 0), # Word rollover.
        )
        
        for (before, after) in test_data:
            self.memory.mem_write_word(5, before)
            self.assertEqual(self.run_to_halt(), 2)
            self.assertEqual(self.memory.mem_read_word(5), after)
            self.assertFalse(self.cpu.flags.carry) # Should be unmodified.
            
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
            self.assertFalse(self.cpu.flags.carry) # Should be unmodified.
            
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
        
    def test_dec_rm8_register(self):
        """
        dec al
        hlt
        """
        self.load_code_string("FE C8 F4")
        
        test_data = (
            (0, 0xFF), # Byte rollover.
            (77, 76), # Random value.
            (0xFF, 0xFE), # Start from "-1".
        )
        
        self.cpu.regs.AH = 0xA5
        for (before, after) in test_data:
            self.cpu.regs.AL = before
            self.assertEqual(self.run_to_halt(), 2)
            self.assertEqual(self.cpu.regs.AL, after)
            self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
            self.assertFalse(self.cpu.flags.carry) # Should be unmodified.
            
    def test_dec_rm8_memory(self):
        """
        dec byte [foo]
        hlt
        foo:
            db 0x99
        """
        self.load_code_string("FE 0E 05 00 F4 99")
        
        test_data = (
            (0, 0xFF), # Byte rollover.
            (77, 76), # Random value.
            (0xFF, 0xFE), # Start from "-1".
        )
        
        for (before, after) in test_data:
            self.memory.mem_write_byte(5, before)
            self.assertEqual(self.run_to_halt(), 2)
            self.assertEqual(self.memory.mem_read_byte(5), after)
            self.assertFalse(self.cpu.flags.carry) # Should be unmodified.
            
    def test_dec_rm16_register(self):
        """
        db 0xFF, 0xC8 ; Extended form of dec AX.
        hlt
        """
        self.load_code_string("FF C8 F4")
        
        test_data = (
            (0, 0xFFFF), # Word rollover.
            (0x0100, 0x00FF), # Byte rollover.
            (5643, 5642), # Random value.
            (0xFFFF, 0xFFFE), # Start from "-1".
        )
        
        for (before, after) in test_data:
            self.cpu.regs.AX = before
            self.assertEqual(self.run_to_halt(), 2)
            self.assertEqual(self.cpu.regs.AX, after)
            self.assertFalse(self.cpu.flags.carry) # Should be unmodified.
            
    def test_dec_rm16_memory(self):
        """
        dec word [foo]
        hlt
        foo:
            dw 0x9999
        """
        self.load_code_string("FF 0E 05 00 F4 99 99")
        
        test_data = (
            (0, 0xFFFF), # Word rollover.
            (0x0100, 0x00FF), # Byte rollover.
            (5643, 5642), # Random value.
            (0xFFFF, 0xFFFE), # Start from "-1".
        )
        
        for (before, after) in test_data:
            self.memory.mem_write_word(5, before)
            self.assertEqual(self.run_to_halt(), 2)
            self.assertEqual(self.memory.mem_read_word(5), after)
            self.assertFalse(self.cpu.flags.carry) # Should be unmodified.
            
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
        
    def test_test_rm8_r8_zero(self):
        """
        test bl, [value]
        hlt
        value:
            db 0x80
        """
        self.cpu.regs.BL = 0x7F
        self.load_code_string("84 1E 05 00 F4 80")
        self.assertEqual(self.run_to_halt(), 2)
        
        self.assert_flags("osZPc") # ODITSZAPC
        
    def test_test_rm8_r8_nonzero(self):
        """
        test bl, [value]
        hlt
        value:
            db 0x80
        """
        self.cpu.regs.BL = 0xF0
        self.load_code_string("84 1E 05 00 F4 80")
        self.assertEqual(self.run_to_halt(), 2)
        
        self.assert_flags("oSzpc") # ODITSZAPC
        
    def test_test_rm8_r8_clears_overflow_and_carry(self):
        """
        test bl, [value]
        hlt
        value:
            db 0x80
        """
        self.cpu.flags.overflow = True
        self.cpu.flags.carry = True
        self.load_code_string("84 1E 05 00 F4 80")
        self.assertEqual(self.run_to_halt(), 2)
        
        self.assert_flags("oc") # ODITSZAPC
        
    def test_test_ax_imm16_zero(self):
        """
        test ax, 0x8000
        hlt
        """
        self.cpu.regs.AX = 0x7FFF
        self.load_code_string("A9 00 80 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assert_flags("osZPc") # ODITSZAPC
        
    def test_test_ax_imm16_nonzero(self):
        """
        test ax, 0x8000
        hlt
        """
        self.cpu.regs.AX = 0xF000
        self.load_code_string("A9 00 80 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assert_flags("oSzPc") # ODITSZAPC
        # NOTE: Parity is set because it is only calculated over the lower byte.
        
    def test_test_ax_imm16_clears_overflow_and_carry(self):
        """
        test ax, 0x8000
        hlt
        """
        self.cpu.flags.overflow = True
        self.cpu.flags.carry = True
        self.load_code_string("A9 00 80 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assert_flags("oc") # ODITSZAPC
        
    def test_test_rm16_r16_zero(self):
        """
        test bx, [value]
        hlt
        value:
            dw 0x8000
        """
        self.cpu.regs.BX = 0x7FFF
        self.load_code_string("85 1E 05 00 F4 00 80")
        self.assertEqual(self.run_to_halt(), 2)
        self.assert_flags("osZPc") # ODITSZAPC
        
    def test_test_rm16_r16_nonzero(self):
        """
        test bx, [value]
        hlt
        value:
            dw 0x8000
        """
        self.cpu.regs.BX = 0xF000
        self.load_code_string("85 1E 05 00 F4 00 80")
        self.assertEqual(self.run_to_halt(), 2)
        self.assert_flags("oSzPc") # ODITSZAPC
        
    def test_test_rm16_r16_clears_overflow_and_carry(self):
        """
        test bx, [value]
        hlt
        value:
            dw 0x8000
        """
        self.cpu.flags.overflow = True
        self.cpu.flags.carry = True
        self.load_code_string("85 1E 05 00 F4 00 80")
        self.assertEqual(self.run_to_halt(), 2)
        self.assert_flags("oc") # ODITSZAPC
        
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
        
    def test_rol_rm8_cl(self):
        """
        rol al, cl
        hlt
        """
        self.cpu.regs.AL = 0x08
        self.cpu.regs.CL = 4
        self.load_code_string("D2 C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x80)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertFalse(self.cpu.flags.carry)
        
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
        
    def test_rol_rm16_cl(self):
        """
        rol ax, cl
        hlt
        """
        self.cpu.regs.AX = 0x0007
        self.cpu.regs.CL = 14
        self.load_code_string("D3 C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xC001)
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
        
    def test_sar_rm16_1_negative(self):
        """
        sar ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x8000
        self.load_code_string("D1 F8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xC000)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_sar_rm16_1_shift_out(self):
        """
        sar ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x0001
        self.load_code_string("D1 F8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0000)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_sar_rm16_1_cross_byte(self):
        """
        sar ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x0100
        self.load_code_string("D1 F8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0080)
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
        
        with self.assertRaises(InvalidOpcodeException) as context:
            self.run_to_halt()
            
        self.assertEqual(context.exception.opcode, 0x43)
        self.assertEqual(context.exception.cs, 0x0000)
        self.assertEqual(context.exception.ip, 0x0002) # Updated to point at the next instruction.
        
        # self.assertEqual(self.run_to_halt(), 1)
        # self.assertEqual(self.cpu.regs.BX, 1) # Only one time.
        # self.assertEqual(self.cpu.regs.DI, 4) # We halted before executing this.
        # self.assertEqual(self.cpu.regs.CX, 2) # Invalid opcode/prefix combination ignored.
        # self.assertEqual(self.memory.mem_read_byte(20), 0x00) # We halted before executing this.
        
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
        
    def test_ds_override(self):
        """
        ds stosb
        mov al, 0x55
        stosb
        hlt
        """
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.ES = 0x0002
        self.cpu.regs.DI = 0x0000
        self.cpu.regs.AL = 0xAA
        self.load_code_string("3E AA B0 55 AA F4")
        self.assertEqual(self.run_to_halt(), 4)
        self.assertEqual(self.memory.mem_read_byte(32 + 1), 0x55) # Normally uses ES.
        self.assertEqual(self.memory.mem_read_byte(16 + 0), 0xAA) # Overridden to use DS.
        
    def test_ss_override(self):
        """
        mov [ss:bx], al
        mov [bx], ah
        hlt
        """
        self.cpu.regs.DS = 0x0001
        self.cpu.regs.SS = 0x0002
        self.cpu.regs.AH = 0x55
        self.cpu.regs.AL = 0xAA
        self.cpu.regs.BX = 0
        self.load_code_string("36 88 07 88 27 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.memory.mem_read_byte(16), 0x55) # Normally uses DS.
        self.assertEqual(self.memory.mem_read_byte(32), 0xAA) # Overridden to use SS.
        
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
        
    def run_push_shortcut_test(self, code_string, register):
        """ Generic function for testing the PUSH [register] opcodes. """
        self.cpu.regs[register] = 0xCAFE
        self.load_code_string(code_string)
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0010) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x00FE)
        self.assertEqual(self.cpu.regs[register], 0xCAFE) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_word(0x001FE), 0xCAFE)
        
    def test_push_ax(self):
        """
        push ax
        hlt
        """
        self.run_push_shortcut_test("50 F4", "AX")
        
    def test_push_bx(self):
        """
        push bx
        hlt
        """
        self.run_push_shortcut_test("53 F4", "BX")
        
    def test_push_cx(self):
        """
        push cx
        hlt
        """
        self.run_push_shortcut_test("51 F4", "CX")
        
    def test_push_dx(self):
        """
        push dx
        hlt
        """
        self.run_push_shortcut_test("52 F4", "DX")
        
    def test_push_sp(self):
        """
        push sp
        hlt
        """
        self.load_code_string("54 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0010) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x00FE)
        # On 808x this pushes the new value, on 286+ this pushes the old value.
        self.assertEqual(self.memory.mem_read_word(0x001FE), 0x00FE)
        
    def test_push_bp(self):
        """
        push bp
        hlt
        """
        self.run_push_shortcut_test("55 F4", "BP")
        
    def test_push_si(self):
        """
        push si
        hlt
        """
        self.run_push_shortcut_test("56 F4", "SI")
        
    def test_push_di(self):
        """
        push di
        hlt
        """
        self.run_push_shortcut_test("57 F4", "DI")
        
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
        
    def run_pop_shortcut_test(self, code_string, register):
        """ Generic function for testing the POP [register] opcodes. """
        self.memory.mem_write_word(0x00200, 0xBEEF)
        self.load_code_string(code_string)
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0010) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x0102)
        self.assertEqual(self.cpu.regs[register], 0xBEEF)
        
    def test_pop_ax(self):
        """
        pop ax
        hlt
        """
        self.run_pop_shortcut_test("58 F4", "AX")
        
    def test_pop_bx(self):
        """
        pop bx
        hlt
        """
        self.run_pop_shortcut_test("5B F4", "BX")
        
    def test_pop_cx(self):
        """
        pop cx
        hlt
        """
        self.run_pop_shortcut_test("59 F4", "CX")
        
    def test_pop_dx(self):
        """
        pop dx
        hlt
        """
        self.run_pop_shortcut_test("5A F4", "DX")
        
    def test_pop_sp(self):
        """
        pop sp
        hlt
        """
        self.memory.mem_write_word(0x00200, 0x0300)
        self.load_code_string("5C F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0010) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x0302)
        
    def test_pop_bp(self):
        """
        pop bp
        hlt
        """
        self.run_pop_shortcut_test("5D F4", "BP")
        
    def test_pop_si(self):
        """
        pop si
        hlt
        """
        self.run_pop_shortcut_test("5E F4", "SI")
        
    def test_pop_di(self):
        """
        pop di
        hlt
        """
        self.run_pop_shortcut_test("5F F4", "DI")
        
class PushPopRoundTrip(BaseOpcodeAcceptanceTests):
    def test_push_pop_sp(self):
        """
        push sp
        pop sp
        hlt
        """
        # SS:SP => 0010:0100 => 0x00200
        self.cpu.regs.SS = 0x0010
        self.cpu.regs.SP = 0x0100
        self.load_code_string("54 5C F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.SS, 0x0010) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x0100) # Should be unmodified.
        
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
        
    def run_address_test(self, code, expected_address, segment_override = None):
        """ Decode the ModRM field and check that the address matches. """
        # Reset IP to 1 so we can run multiple checks in the same test.
        self.cpu.regs.IP = 1
        # Reset segment override to None so we don't affect subsequent tests.
        self.cpu.segment_override = None
        # Track the number of bytes loaded so we can check that IP is correct at the end.
        expected_ip = self.load_code_string(code)
        # We aren't doing register testing so we will just assume 16 bits and toss the register.
        self.assertEqual(self.cpu.get_modrm_operands(16)[1:], (ADDRESS, expected_address))
        # Ensure that IP matches the number of bytes loaded.
        self.assertEqual(self.cpu.regs.IP, expected_ip)
        # Ensure any segment override is expected.
        self.assertEqual(self.cpu.segment_override, segment_override)
        
    def test_mod_00_rm_110_absolute_address(self):
        self.run_address_test("F7 16 43 56", 0x5643) # not word [0x5643]
        self.run_address_test("F7 16 01 00", 0x0001) # not word [0x0001]
        self.run_address_test("F7 16 00 00", 0x0000) # not word [0x0000]
        
    def test_mod_00_all_modes_no_displacement(self):
        self.run_address_test("F7 10", 0x1200) # not word [bx + si]
        self.run_address_test("F7 11", 0x1400) # not word [bx + di]
        self.run_address_test("F7 12", 0x8200, "SS") # not word [bp + si]
        self.run_address_test("F7 13", 0x8400, "SS") # not word [bp + di]
        self.run_address_test("F7 14", 0x0200) # not word [si]
        self.run_address_test("F7 15", 0x0400) # not word [di]
        # This is not a mod 00 test, mod 00 rm 110 is handled above.
        # self.run_address_test("F7 56 00", 0x8000) # not word [bp]
        self.run_address_test("F7 17", 0x1000) # not word [bx]
        
    def test_mod_01_all_modes_byte_displacement(self):
        self.run_address_test("F7 50 01", 0x1200 + 1) # not word [bx + si + 1]
        self.run_address_test("F7 51 01", 0x1400 + 1) # not word [bx + di + 1]
        self.run_address_test("F7 52 01", 0x8200 + 1, "SS") # not word [bp + si + 1]
        self.run_address_test("F7 53 01", 0x8400 + 1, "SS") # not word [bp + di + 1]
        self.run_address_test("F7 54 01", 0x0200 + 1) # not word [si + 1]
        self.run_address_test("F7 55 01", 0x0400 + 1) # not word [di + 1]
        self.run_address_test("F7 56 01", 0x8000 + 1, "SS") # not word [bp + 1]
        self.run_address_test("F7 57 01", 0x1000 + 1) # not word [bx + 1]
        
    def test_mod_01_all_modes_byte_negative_displacement(self):
        self.run_address_test("F7 50 FF", 0x1200 - 1) # not word [bx + si - 1]
        self.run_address_test("F7 51 FF", 0x1400 - 1) # not word [bx + di - 1]
        self.run_address_test("F7 52 FF", 0x8200 - 1, "SS") # not word [bp + si - 1]
        self.run_address_test("F7 53 FF", 0x8400 - 1, "SS") # not word [bp + di - 1]
        self.run_address_test("F7 54 FF", 0x0200 - 1) # not word [si - 1]
        self.run_address_test("F7 55 FF", 0x0400 - 1) # not word [di - 1]
        self.run_address_test("F7 56 FF", 0x8000 - 1, "SS") # not word [bp - 1]
        self.run_address_test("F7 57 FF", 0x1000 - 1) # not word [bx - 1]
        
    def test_mod_10_all_modes_word_displacement(self):
        self.run_address_test("F7 90 00 01", 0x1200 + 0x100) # not word [bx + si]
        self.run_address_test("F7 91 00 01", 0x1400 + 0x100) # not word [bx + di]
        self.run_address_test("F7 92 00 01", 0x8200 + 0x100, "SS") # not word [bp + si]
        self.run_address_test("F7 93 00 01", 0x8400 + 0x100, "SS") # not word [bp + di]
        self.run_address_test("F7 94 00 01", 0x0200 + 0x100) # not word [si]
        self.run_address_test("F7 95 00 01", 0x0400 + 0x100) # not word [di]
        self.run_address_test("F7 96 00 01", 0x8000 + 0x100, "SS") # not word [bp]
        self.run_address_test("F7 97 00 01", 0x1000 + 0x100) # not word [bx]
        
    def test_mod_10_all_modes_word_negative_displacement(self):
        self.run_address_test("F7 90 00 FF", 0x1200 - 0x100) # not word [bx + si]
        self.run_address_test("F7 91 00 FF", 0x1400 - 0x100) # not word [bx + di]
        self.run_address_test("F7 92 00 FF", 0x8200 - 0x100, "SS") # not word [bp + si]
        self.run_address_test("F7 93 00 FF", 0x8400 - 0x100, "SS") # not word [bp + di]
        self.run_address_test("F7 94 00 FF", 0x0200 - 0x100) # not word [si]
        self.run_address_test("F7 95 00 FF", 0x0400 - 0x100) # not word [di]
        self.run_address_test("F7 96 00 FF", 0x8000 - 0x100, "SS") # not word [bp]
        self.run_address_test("F7 97 00 FF", 0x1000 - 0x100) # not word [bx]
        
    def test_bp_doesnt_override_existing_override(self):
        """
        mov ax, [ds:bp]
        hlt
        """
        self.cpu.regs.BP = 0x0100
        self.cpu.regs.DS = 0x0030
        self.memory.mem_write_word(0x0400, 0xCAFE)
        self.load_code_string("3E 8B 46 00 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xCAFE)
        
class IntOpcodeTests(BaseOpcodeAcceptanceTests):
    def setUp(self):
        super(IntOpcodeTests, self).setUp()
        
        # We need to leave room at the beginning of RAM for the vector table.
        self.cpu.regs.CS = 0x0040
        self.cpu.regs.SS = 0x0100
        self.cpu.regs.SP = 0x0100
        self.cpu.regs.DS = 0x0040
        self.cpu.regs.ES = 0x0040
        
    def test_int_acceptance_test(self):
        """
        ; Fill in the interrupt vector table.
        TIMES 32 dw 0x0000
        dw 0x0004
        dw 0x0050
        TIMES (0x400 - ($ - $$)) db 0x00

        ; Real code starts at CS:IP 0040:0000.
        int 0x10

        ; Halts all the way to the interrupt handler.
        TIMES (0x504 - ($ - $$)) hlt

        ; Interrupt handler at CS:IP 0050:0004
        int10h:
            mov bx, 0x5643
            hlt
        """
        # This is a ton of code, this fills in the relevant parts.
        self.memory.mem_write_byte(0x40, 0x04)
        self.memory.mem_write_byte(0x42, 0x50)
        
        self.memory.mem_write_byte(0x400, 0xCD)
        self.memory.mem_write_byte(0x401, 0x10)
        for offset in range(0x402, 0x504):
            self.memory.mem_write_byte(offset, 0xF4)
            
        self.memory.mem_write_byte(0x504, 0xBB)
        self.memory.mem_write_byte(0x505, 0x43)
        self.memory.mem_write_byte(0x506, 0x56)
        self.memory.mem_write_byte(0x507, 0xF4)
        
        # Actually run the tests.
        self.cpu.flags.trap = True
        self.cpu.flags.interrupt_enable = True
        self.cpu.flags.carry = True
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.CS, 0x0050)
        self.assertEqual(self.cpu.regs.IP, 0x0008) # One past the hlt.
        self.assertFalse(self.cpu.flags.interrupt_enable) # Should be cleared.
        self.assertFalse(self.cpu.flags.trap) # Should be cleared.
        self.assertTrue(self.cpu.flags.carry) # Should be unmodified.
        self.assertEqual(self.cpu.regs.BX, 0x5643)
        self.assertEqual(self.cpu.regs.SP, 0xFA)
        self.assertEqual(self.memory.mem_read_word(0x10FE), 0xF301) # Should contain original FLAGS.
        self.assertEqual(self.memory.mem_read_word(0x10FC), 0x0040) # Should contain original CS.
        self.assertEqual(self.memory.mem_read_word(0x10FA), 0x0002) # Should contain original IP.
    
class JmpOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jmp_r16(self):
        """
        jmp ax
        hlt
        inc bx
        hlt
        """
        self.cpu.regs.AX = 0x0003 # After first HLT.
        self.cpu.regs.SP = 0x0100
        self.load_code_string("FF E0 F4 43 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AX, 0x0003) # Should be unmodified.
        self.assertEqual(self.cpu.regs.BX, 0x0001) # Should have been incremented.
        self.assertEqual(self.cpu.regs.SP, 0x0100) # Should be unmodified.
        
    def test_jmp_m16(self):
        """
        jmp [value]
        hlt
        dec bx
        hlt
        value:
            dw 5
        """
        self.cpu.regs.SP = 0x0100
        self.load_code_string("FF 26 07 00 F4 4B F4 05 00")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.BX, 0xFFFF) # Should have been decremented.
        self.assertEqual(self.cpu.regs.SP, 0x0100) # Should be unmodified.
        
    def test_jmp_far_dword_pointer(self):
        """
        jmp far [cs : 0x0c]
        TIMES (0x0C - ($ - $$)) nop
        dw 0x0002 ; IP
        dw 0x0001 ; CS
        TIMES (0x12 - ($ - $$)) nop
        inc ax
        hlt
        """
        self.load_code_string("2E FF 2E 0C 00 F4 90 90 90 90 90 90 02 00 01 00 90 90 40 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AX, 0x0001)
        self.assertEqual(self.cpu.regs.CS, 0x0001)
        self.assertEqual(self.cpu.regs.IP, 0x0004) # Pointing after final hlt.
        
class IretOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_iret(self):
        """
        iret
        TIMES (0x12 - ($ - $$)) hlt
        inc bx
        hlt
        """
        self.cpu.regs.SS = 0x0000
        self.cpu.regs.SP = 0x0100
        self.memory.mem_write_word(0x0100, 0x0002) # IP
        self.memory.mem_write_word(0x0102, 0x0001) # CS
        self.memory.mem_write_word(0x0104, 0x0001) # FLAGS - Carry set.
        self.cpu.flags.carry = False
        self.load_code_string("CF F4 F4 F4 F4 F4 F4 F4 F4 F4 F4 F4 F4 F4 F4 F4 F4 F4 43 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.BX, 1)
        self.assertEqual(self.cpu.regs.SP, 0x0106)
        self.assertTrue(self.cpu.flags.carry)
        
class FarPointerOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_les_di(self):
        """
        les di, [value]
        hlt
        value:
            dw 0xCAFE
            dw 0xFACE
        """
        self.load_code_string("C4 3E 05 00 F4 FE CA CE FA")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.ES, 0xFACE)
        self.assertEqual(self.cpu.regs.DI, 0xCAFE)
        
    def test_les_other_register(self):
        """
        les ax, [value]
        hlt
        value:
            dw 0xCAFE
            dw 0xFACE
        """
        self.load_code_string("C4 06 05 00 F4 FE CA CE FA")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.ES, 0xFACE)
        self.assertEqual(self.cpu.regs.DI, 0x0000) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AX, 0xCAFE)
        
    def test_lds_si(self):
        """
        lds si, [value]
        hlt
        value:
            dw 0xCAFE
            dw 0xFACE
        """
        self.load_code_string("C5 36 05 00 F4 FE CA CE FA")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DS, 0xFACE)
        self.assertEqual(self.cpu.regs.SI, 0xCAFE)
        
    def test_lds_other_register(self):
        """
        lds ax, [value]
        hlt
        value:
            dw 0xCAFE
            dw 0xFACE
        """
        self.load_code_string("C5 06 05 00 F4 FE CA CE FA")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DS, 0xFACE)
        self.assertEqual(self.cpu.regs.SI, 0x0000) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AX, 0xCAFE)
        
class OperatorOverflowTests(unittest.TestCase):
    """ http://teaching.idallen.com/dat2343/10f/notes/040_overflow.txt """
    def setUp(self):
        self.cpu = CPU()
        
    def run_overflow_test(self, func, op1, op2, result, expected_overflow):
        self.assertEqual(func(op1, op2), result)
        self.assertEqual(self.cpu.flags.overflow, expected_overflow)
        
    def test_add_8_bit(self):
        data = [
            # op1,  op2,    result, expected_overflow
            (50,    50,     100,    False), # + + +
            (100,   100,    200,    True),  # + + - OVERFLOW
            (50,    -25,    25,     False), # + - +
            (50,    -100,   -50,    False), # + - -
            (-50,   100,    50,     False), # - + +
            (-50,   25,     -25,    False), # - + -
            (-100,  -100,   -200,   True),  # - - + OVERFLOW
            (-50,   -50,    -100,   False), # - - -
        ]
        for args in data:
            self.run_overflow_test(self.cpu.operator_add_8, *args)
            
    def test_add_16_bit(self):
        data = [
            # op1,  op2,    result, expected_overflow
            (10000, 20000,  30000,  False), # + + +
            (20000, 20000,  40000,  True),  # + + - OVERFLOW
            (20000, -10000, 10000,  False), # + - +
            (10000, -20000, -10000, False), # + - -
            (-10000, 20000, 10000,  False), # - + +
            (-20000, 10000, -10000, False), # - + -
            (-20000, -20000, -40000, True), # - - + OVERFLOW
            (-10000, -20000, -30000, False), # - - -
        ]
        for args in data:
            self.run_overflow_test(self.cpu.operator_add_16, *args)
            
    def test_adc_8_bit(self):
        data = [
            # op1,  op2,    result, expected_overflow
            (50,    50,     100,    False), # + + +
            (100,   100,    200,    True),  # + + - OVERFLOW
            (50,    -25,    25,     False), # + - +
            (50,    -100,   -50,    False), # + - -
            (-50,   100,    50,     False), # - + +
            (-50,   25,     -25,    False), # - + -
            (-100,  -100,   -200,   True),  # - - + OVERFLOW
            (-50,   -50,    -100,   False), # - - -
        ]
        for args in data:
            self.run_overflow_test(self.cpu.operator_adc_8, *args)
            
    def test_adc_16_bit(self):
        data = [
            # op1,  op2,    result, expected_overflow
            (10000, 20000,  30000,  False), # + + +
            (20000, 20000,  40000,  True),  # + + - OVERFLOW
            (20000, -10000, 10000,  False), # + - +
            (10000, -20000, -10000, False), # + - -
            (-10000, 20000, 10000,  False), # - + +
            (-20000, 10000, -10000, False), # - + -
            (-20000, -20000, -40000, True), # - - + OVERFLOW
            (-10000, -20000, -30000, False), # - - -
        ]
        for args in data:
            self.run_overflow_test(self.cpu.operator_adc_16, *args)
            
    def test_sub_8_bit(self):
        data = [
            # op1,  op2,    result, expected_overflow
            (100,   50,     50,     False), # + + +
            (50,    100,    -50,    False), # + + -
            (50,    -25,    75,     False), # + - +
            (50,    -100,   150,    True),  # + - - OVERFLOW
            (-50,   100,    -150,   True),  # - + + OVERFLOW
            (-50,   25,     -75,    False), # - + -
            (-50,   -100,   50,     False), # - - +
            (-50,   -25,    -25,    False), # - - -
        ]
        for args in data:
            self.run_overflow_test(self.cpu.operator_sub_8, *args)
            
    def test_sub_16_bit(self):
        data = [
            # op1,  op2,    result, expected_overflow
            (30000, 20000,  10000 , False), # + + +
            (20000, 30000,  -10000, False), # + + -
            (20000, -10000, 30000,  False), # + - +
            (20000, -20000, 40000,  True),  # + - - OVERFLOW
            (-20000, 20000, -40000, True),  # - + + OVERFLOW
            (-20000, 10000, -30000, False), # - + -
            (-10000, -20000, 10000, False), # - - +
            (-20000, -10000, -10000, False), # - - -
        ]
        for args in data:
            self.run_overflow_test(self.cpu.operator_sub_16, *args)
            
    def test_sbb_8_bit(self):
        data = [
            # op1,  op2,    result, expected_overflow
            (100,   50,     50,     False), # + + +
            (50,    100,    -50,    False), # + + -
            (50,    -25,    75,     False), # + - +
            (50,    -100,   150,    True),  # + - - OVERFLOW
            (-50,   100,    -150,   True),  # - + + OVERFLOW
            (-50,   25,     -75,    False), # - + -
            (-50,   -100,   50,     False), # - - +
            (-50,   -25,    -25,    False), # - - -
        ]
        for args in data:
            self.run_overflow_test(self.cpu.operator_sbb_8, *args)
            
    def test_sbb_16_bit(self):
        data = [
            # op1,  op2,    result, expected_overflow
            (30000, 20000,  10000 , False), # + + +
            (20000, 30000,  -10000, False), # + + -
            (20000, -10000, 30000,  False), # + - +
            (20000, -20000, 40000,  True),  # + - - OVERFLOW
            (-20000, 20000, -40000, True),  # - + + OVERFLOW
            (-20000, 10000, -30000, False), # - + -
            (-10000, -20000, 10000, False), # - - +
            (-20000, -10000, -10000, False), # - - -
        ]
        for args in data:
            self.run_overflow_test(self.cpu.operator_sbb_16, *args)
            
class JlOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_taken_only_overflow_set(self):
        """
        jl location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.overflow = True
        self.load_code_string("7C 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_taken_only_sign_set(self):
        """
        jl location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.sign = True
        self.load_code_string("7C 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken_both_clear(self):
        """
        jl location
        hlt
        location: inc al
        hlt
        """
        self.load_code_string("7C 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_not_taken_both_set(self):
        """
        jl location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.sign = True
        self.cpu.flags.overflow = True
        self.load_code_string("7C 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_can_be_backward(self):
        """
        location: inc ax
        hlt
        jl location
        hlt
        """
        self.cpu.flags.sign = True
        self.load_code_string("40 F4 7C FC F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0002), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JnlOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_not_taken_only_overflow_set(self):
        """
        jnl location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.overflow = True
        self.load_code_string("7D 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_not_taken_only_sign_set(self):
        """
        jnl location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.sign = True
        self.load_code_string("7D 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_taken_both_clear(self):
        """
        jnl location
        hlt
        location: inc al
        hlt
        """
        self.load_code_string("7D 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_taken_both_set(self):
        """
        jnl location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.sign = True
        self.cpu.flags.overflow = True
        self.load_code_string("7D 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_can_be_backward(self):
        """
        location: inc ax
        hlt
        jnl location
        hlt
        """
        self.load_code_string("40 F4 7D FC F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0002), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class CbwOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_cbw_zero(self):
        """
        cbw
        hlt
        """
        self.cpu.regs.AH = 0xAA
        self.cpu.regs.AL = 0x00
        self.load_code_string("98 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0000)
        
    def test_cbw_positive(self):
        """
        cbw
        hlt
        """
        self.cpu.regs.AH = 0xAA
        self.cpu.regs.AL = 0x72
        self.load_code_string("98 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0072)
        
    def test_cbw_negative(self):
        """
        cbw
        hlt
        """
        self.cpu.regs.AH = 0xAA
        self.cpu.regs.AL = 0x80
        self.load_code_string("98 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xFF80)
        
class MulOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_mul_al_rm8_small(self):
        """
        mul byte [value]
        hlt
        value:
            db 25
        """
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.cpu.regs.AH = 0xA5 # Should be ignored.
        self.cpu.regs.AL = 7
        self.load_code_string("F6 26 05 00 F4 19")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x00AF) # 175
        self.assertFalse(self.cpu.flags.carry)
        self.assertFalse(self.cpu.flags.overflow)
        
    def test_mul_al_rm8_large(self):
        """
        mul byte [value]
        hlt
        value:
            db 25
        """
        self.cpu.regs.AH = 0xA5 # Should be ignored.
        self.cpu.regs.AL = 0xFF
        self.load_code_string("F6 26 05 00 F4 19")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x18E7) # 6375
        self.assertTrue(self.cpu.flags.carry)
        self.assertTrue(self.cpu.flags.overflow)
        
    def test_mul_ax_rm16_small(self):
        """
        mul word [value]
        hlt
        value:
            dw 25
        """
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.cpu.regs.AX = 400
        self.load_code_string("F7 26 05 00 F4 19 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x2710) # 10000
        self.assertEqual(self.cpu.regs.DX, 0x0000)
        self.assertFalse(self.cpu.flags.carry)
        self.assertFalse(self.cpu.flags.overflow)
        
    def test_mul_ax_rm16_large(self):
        """
        mul word [value]
        hlt
        value:
            dw 25
        """
        self.cpu.regs.AX = 0xFFFF
        self.load_code_string("F7 26 05 00 F4 19 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xFFE7) # 1638375
        self.assertEqual(self.cpu.regs.DX, 0x0018)
        self.assertTrue(self.cpu.flags.carry)
        self.assertTrue(self.cpu.flags.overflow)
        
class XorOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_xor_rm8_r8(self):
        """
        xor [value], al
        hlt
        value:
            db 0x0F
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 0x18
        self.load_code_string("30 06 05 00 F4 0F")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0x18) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(0x05), 0x17)
        
    def test_xor_rm16_r16(self):
        """
        xor [value], ax
        hlt
        value:
            dw 0x01A5
        """
        self.cpu.regs.AX = 0x015A
        self.load_code_string("31 06 05 00 F4 A5 01")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x015A) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_word(0x05), 0x00FF)
        
    def test_xor_r8_rm8(self):
        """
        xor al, [value]
        hlt
        value:
            db 0x04
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 0x0F
        self.load_code_string("32 06 05 00 F4 04")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0x0B)
        self.assertEqual(self.memory.mem_read_byte(0x05), 0x04) # Should be unmodified.
        
    def test_xor_r16_rm16(self):
        """
        xor bx, [value]
        hlt
        value:
            dw 0xFFFF
        """
        self.cpu.regs.BX = 0x0ACE
        self.load_code_string("33 1E 05 00 F4 FF FF")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 0xF531)
        self.assertEqual(self.memory.mem_read_word(0x05), 0xFFFF) # Should be unmodified.
        
    def test_xor_al_imm8(self):
        """
        xor al, 0x07
        hlt
        """
        self.cpu.regs.AH = 0xA5
        self.cpu.regs.AL = 0x1E
        self.load_code_string("34 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0x19)
        
    def test_xor_ax_imm16(self):
        """
        xor ax, 0xCFFF
        hlt
        """
        self.cpu.regs.AX = 0x0501
        self.load_code_string("35 FF CF F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xCAFE)
        
    def test_xor_clears_carry_overflow(self):
        """
        xor al, 0x07
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.load_code_string("34 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_xor_8x_8_bit(self):
        """
        xor bl, 0x07
        hlt
        """
        self.cpu.regs.BH = 0xA5
        self.cpu.regs.BL = 0x1E
        self.load_code_string("80 F3 07 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BH, 0xA5) # Should be unmodified.
        self.assertEqual(self.cpu.regs.BL, 0x19)
        
    def test_xor_8x_16_bit(self):
        """
        xor bx, 0xCFFF
        hlt
        """
        self.cpu.regs.BX = 0x0501
        self.load_code_string("81 F3 FF CF F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 0xCAFE)
        
    def test_xor_8x_clears_carry_overflow(self):
        """
        xor bx, 0xCFFF
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.cpu.regs.BX = 0x0501
        self.load_code_string("81 F3 FF CF F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 0xCAFE)
        self.assert_flags("oSzpc") # ODITSZAPC
        
class FlagsOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_pushf_simple(self):
        """
        pushf
        hlt
        """
        self.cpu.regs.SS = 0x0030
        self.cpu.regs.SP = 0x0100
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.assertEqual(self.memory.mem_read_word(0x003FE), 0x0000)
        self.load_code_string("9C F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0030) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x00FE)
        self.assert_flags("OszpC") # ODITSZAPC # Should be unmodified.
        self.assertEqual(self.memory.mem_read_word(0x003FE), 0xF801)
        
    def test_popf_simple(self):
        """
        popf
        hlt
        """
        self.cpu.regs.SS = 0x0030
        self.cpu.regs.SP = 0x0100
        self.memory.mem_write_word(0x00400, 0xF00F)
        self.load_code_string("9D F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SS, 0x0030) # Should be unmodified.
        self.assertEqual(self.cpu.regs.SP, 0x00102)
        self.assert_flags("oszPC") # ODITSZAPC
        self.assertEqual(self.memory.mem_read_word(0x00400), 0xF00F) # Should be unmodified.
        
    def test_lahf_simple(self):
        """
        lahf
        hlt
        """
        self.cpu.flags.sign = True
        self.cpu.flags.carry = True
        self.cpu.regs.AH = 0x12
        self.cpu.regs.AL = 0x34
        self.load_code_string("9F F4")
        self.assert_flags("oSzpC") # ODITSZAPC # Should be unmodified.
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0x81)
        self.assertEqual(self.cpu.regs.AL, 0x34) # Should be unmodified.
        
    def test_sahf_simple(self):
        """
        sahf
        hlt
        """
        self.cpu.regs.AH = 0x7E
        self.cpu.regs.AL = 0x34
        self.load_code_string("9E F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AH, 0x7E) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AL, 0x34) # Should be unmodified.
        self.assert_flags("osZPc") # ODITSZAPC
        
    def test_sahf_doesnt_modify_overflow(self):
        """
        sahf
        hlt
        """
        self.cpu.flags.overflow = True
        self.cpu.regs.AH = 0x7E
        self.load_code_string("9E F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assert_flags("OsZPc") # ODITSZAPC
        
class NegOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_neg_8_bit_positive(self):
        """
        neg bl
        hlt
        """
        self.cpu.regs.BH = 0x77
        self.cpu.regs.BL = 55
        self.load_code_string("F6 DB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BL, 0xC9) # -55 in two's complement.
        self.assertEqual(self.cpu.regs.BH, 0x77) # Should be unmodified.
        self.assert_flags("oSzPC") # ODITSZAPC
        
    def test_neg_8_bit_negative(self):
        """
        neg bl
        hlt
        """
        self.cpu.regs.BH = 0x77
        self.cpu.regs.BL = 0xC9 # -55 in two's complement.
        self.load_code_string("F6 DB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BL, 55)
        self.assertEqual(self.cpu.regs.BH, 0x77) # Should be unmodified.
        self.assert_flags("oszpC") # ODITSZAPC
        
    def test_neg_8_bit_zero(self):
        """
        neg bl
        hlt
        """
        self.cpu.regs.BH = 0x77
        self.cpu.regs.BL = 0
        self.load_code_string("F6 DB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BL, 0)
        self.assertEqual(self.cpu.regs.BH, 0x77) # Should be unmodified.
        self.assert_flags("osZPc") # ODITSZAPC
        
    def test_neg_16_bit_positive(self):
        """
        neg bx
        hlt
        """
        self.cpu.regs.BX = 1000
        self.load_code_string("F7 DB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 0xFC18) # -1000 in two's complement.
        self.assert_flags("oSzPC") # ODITSZAPC
        
    def test_neg_16_bit_negative(self):
        """
        neg bx
        hlt
        """
        self.cpu.regs.BX = 0xFC18 # -1000 in two's complement.
        self.load_code_string("F7 DB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 1000)
        self.assert_flags("oszPC") # ODITSZAPC
        
    def test_neg_16_bit_zero(self):
        """
        neg bx
        hlt
        """
        self.cpu.regs.BX = 0
        self.load_code_string("F7 DB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 0)
        self.assert_flags("osZPc") # ODITSZAPC
        
class JcxzOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_taken_cx_is_zero(self):
        """
        jcxz location
        hlt
        location: inc al
        hlt
        """
        self.cpu.regs.CX = 0
        self.load_code_string("E3 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken_cx_not_zero(self):
        """
        jcxz location
        hlt
        location: inc al
        hlt
        """
        self.cpu.regs.CX = 5643
        self.load_code_string("E3 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_can_be_backward(self):
        """
        location: inc ax
        hlt
        jcxz location
        hlt
        """
        self.cpu.regs.CX = 0
        self.load_code_string("40 F4 E3 FC F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0002), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class ShrOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_shr_rm8_1_positive(self):
        """
        shr al, 1
        hlt
        """
        self.cpu.regs.AL = 0x40
        self.load_code_string("D0 E8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x20)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertFalse(self.cpu.flags.carry)
        
    def test_shr_rm8_1_negative(self):
        """
        shr al, 1
        hlt
        """
        self.cpu.regs.AL = 0x80
        self.load_code_string("D0 E8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x40) # Doesn't maintain sign like SAR.
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertFalse(self.cpu.flags.carry)
        
    def test_shr_rm8_1_shift_out(self):
        """
        shr al, 1
        hlt
        """
        self.cpu.regs.AL = 0x01
        self.load_code_string("D0 E8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x00)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertTrue(self.cpu.flags.carry) # Carry out.
        
    def test_shr_rm16_1_positive(self):
        """
        shr ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x4000
        self.load_code_string("D1 E8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x2000)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_shr_rm16_1_negative(self):
        """
        shr ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x8000
        self.load_code_string("D1 E8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x4000) # Doesn't maintain sign like SAR.
        self.assertFalse(self.cpu.flags.carry)
        
    def test_shr_rm16_1_shift_out(self):
        """
        shr ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x0001
        self.load_code_string("D1 E8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0000)
        self.assertTrue(self.cpu.flags.carry) # Carry out.
        
    def test_shr_rm16_1_cross_byte(self):
        """
        shr ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x0100
        self.load_code_string("D1 E8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0080)
        self.assertFalse(self.cpu.flags.carry)
        
class ShlOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_shl_rm8_1_simple(self):
        """
        shl al, 1
        hlt
        """
        self.cpu.regs.AL = 0x01
        self.load_code_string("D0 E0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x02)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertFalse(self.cpu.flags.carry)
        
    def test_shl_rm8_1_shift_out(self):
        """
        shl al, 1
        hlt
        """
        self.cpu.regs.AL = 0x80
        self.load_code_string("D0 E0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x00)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertTrue(self.cpu.flags.carry) # Carry out.
        
    def test_shl_rm16_1_simple(self):
        """
        shl ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x0002
        self.load_code_string("D1 E0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0004)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_shl_rm16_1_shift_out(self):
        """
        shl ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x8000
        self.load_code_string("D1 E0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0000)
        self.assertTrue(self.cpu.flags.carry) # Carry out.
        
    def test_shl_rm16_1_cross_byte(self):
        """
        shl ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x0080
        self.load_code_string("D1 E0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0100)
        self.assertFalse(self.cpu.flags.carry)
        
class DivOpcodeTests(BaseOpcodeAcceptanceTests):
    def setUp(self):
        super(DivOpcodeTests, self).setUp()
        self.local_interrupt_log = []
        self.cpu.internal_service_interrupt = self.service_interrupt_hook
        
    def service_interrupt_hook(self, interrupt):
        self.local_interrupt_log.append(interrupt)
        
    def test_div_by_byte(self):
        """
        div bl
        hlt
        """
        self.cpu.regs.AX = 1000
        self.cpu.regs.BL = 7
        self.load_code_string("F6 F3 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 142)
        self.assertEqual(self.cpu.regs.AH, 6)
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_div_by_byte_no_remainder(self):
        """
        div bl
        hlt
        """
        self.cpu.regs.AX = 1000
        self.cpu.regs.BL = 10
        self.load_code_string("F6 F3 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 100)
        self.assertEqual(self.cpu.regs.AH, 0)
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_div_by_byte_zero(self):
        """
        div bl
        hlt
        """
        self.cpu.regs.AX = 1000
        self.cpu.regs.BL = 0
        self.load_code_string("F6 F3 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.local_interrupt_log, [0])
        
    def test_div_by_byte_result_too_big(self):
        """
        div bl
        hlt
        """
        self.cpu.regs.AX = 1000
        self.cpu.regs.BL = 2
        self.load_code_string("F6 F3 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.local_interrupt_log, [0])
        
    def test_div_by_word(self):
        """
        div bx
        hlt
        """
        self.cpu.regs.DX = 0xABCD
        self.cpu.regs.AX = 0xEF12
        self.cpu.regs.BX = 0xF000
        self.load_code_string("F7 F3 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xB742)
        self.assertEqual(self.cpu.regs.DX, 0xF12)
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_div_by_word_no_remainder(self):
        """
        div bx
        hlt
        """
        self.cpu.regs.DX = 0xABCD
        self.cpu.regs.AX = 0xE000
        self.cpu.regs.BX = 0xF000
        self.load_code_string("F7 F3 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xB742)
        self.assertEqual(self.cpu.regs.DX, 0)
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_div_by_word_zero(self):
        """
        div bx
        hlt
        """
        self.cpu.regs.DX = 0xABCD
        self.cpu.regs.AX = 0xE000
        self.cpu.regs.BX = 0
        self.load_code_string("F7 F3 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.local_interrupt_log, [0])
        
    def test_div_by_word_result_too_big(self):
        """
        div bx
        hlt
        """
        self.cpu.regs.DX = 0xABCD
        self.cpu.regs.AX = 0xE000
        self.cpu.regs.BX = 2
        self.load_code_string("F7 F3 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.local_interrupt_log, [0])
        
    
class ScasOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_scasb_incrementing(self):
        """
        scasb
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AH = 0xFF
        self.cpu.regs.AL = 0x30
        self.load_code_string("AE F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x30) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AH, 0xFF) # Should be unmodified.
        self.assertEqual(self.cpu.regs.ES, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DI, 0x0005)
        self.assertEqual(self.memory.mem_read_byte(19), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x00) # Should be unmodified
        self.assertEqual(self.memory.mem_read_byte(21), 0x00) # Should be unmodified.
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_scasb_decrementing(self):
        """
        scasb
        hlt
        """
        self.cpu.flags.direction = True
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AH = 0xFF
        self.cpu.regs.AL = 0x30
        self.load_code_string("AE F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x30) # Should be unmodified.
        self.assertEqual(self.cpu.regs.AH, 0xFF) # Should be unmodified.
        self.assertEqual(self.cpu.regs.ES, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DI, 0x0003)
        self.assertEqual(self.memory.mem_read_byte(19), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x00) # Should be unmodified
        self.assertEqual(self.memory.mem_read_byte(21), 0x00) # Should be unmodified.
        self.assert_flags("oszPc") # ODITSZAPC
        
    def test_scasb_zero(self):
        """
        scasb
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AL = 0x30
        self.memory.mem_write_byte(19, 0x31)
        self.memory.mem_write_byte(20, 0x30)
        self.memory.mem_write_byte(21, 0x32)
        self.load_code_string("AE F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DI, 0x0005)
        self.assert_flags("osZPc") # ODITSZAPC
        
    def test_scasb_negative(self):
        """
        scasb
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AL = 0x20
        self.memory.mem_write_byte(20, 0x30)
        self.load_code_string("AE F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DI, 0x0005)
        self.assert_flags("oSzPC") # ODITSZAPC
        
    def test_scasw_incrementing(self):
        """
        scasw
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AX = 0xABCD
        self.load_code_string("AF F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xABCD) # Should be unmodified.
        self.assertEqual(self.cpu.regs.ES, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DI, 0x0006)
        self.assertEqual(self.memory.mem_read_byte(19), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x00) # Should be unmodified
        self.assertEqual(self.memory.mem_read_byte(21), 0x00) # Should be unmodified.
        self.assert_flags("oSzpc") # ODITSZAPC
        
    def test_scasw_decrementing(self):
        """
        scasw
        hlt
        """
        self.cpu.flags.direction = True
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AX = 0xABCD
        self.load_code_string("AF F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xABCD) # Should be unmodified.
        self.assertEqual(self.cpu.regs.ES, 0x0001) # Should be unmodified.
        self.assertEqual(self.cpu.regs.DI, 0x0002)
        self.assertEqual(self.memory.mem_read_byte(19), 0x00) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(20), 0x00) # Should be unmodified
        self.assertEqual(self.memory.mem_read_byte(21), 0x00) # Should be unmodified.
        self.assert_flags("oSzpc") # ODITSZAPC
        
    def test_scasw_zero(self):
        """
        scasw
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AX = 0x5020
        self.memory.mem_write_byte(20, 0x20)
        self.memory.mem_write_byte(21, 0x50)
        self.load_code_string("AF F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DI, 0x0006)
        self.assert_flags("osZPc") # ODITSZAPC
        
    def test_scasw_negative(self):
        """
        scasw
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AX = 0x2000
        self.memory.mem_write_byte(20, 0x00)
        self.memory.mem_write_byte(21, 0x30)
        self.load_code_string("AF F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DI, 0x0006)
        self.assert_flags("oSzPC") # ODITSZAPC
        
class RepzRepnzPrefixTests(BaseOpcodeAcceptanceTests):
    def test_repnz_scasb_exit_on_zero(self):
        """
        repnz scasb
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AL = 0x02
        self.cpu.regs.CX = 20
        self.cpu.flags.zero = True # Should not cause it to immediately terminate.
        self.memory.mem_write_byte(20, 0x01)
        self.memory.mem_write_byte(21, 0x01)
        self.memory.mem_write_byte(22, 0x01)
        self.memory.mem_write_byte(23, 0x01)
        self.memory.mem_write_byte(24, 0x02)
        self.load_code_string("F2 AE F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.CX, 15)
        self.assertEqual(self.cpu.regs.DI, 0x0009)
        self.assert_flags("osZPc") # ODITSZAPC
        
    def test_repz_scasb_exit_on_nonzero(self):
        """
        repz scasb
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AL = 0x01
        self.cpu.regs.CX = 20
        self.cpu.flags.zero = False # Should not cause it to immediately terminate.
        self.memory.mem_write_byte(20, 0x01)
        self.memory.mem_write_byte(21, 0x01)
        self.memory.mem_write_byte(22, 0x01)
        self.memory.mem_write_byte(23, 0x01)
        self.memory.mem_write_byte(24, 0x02)
        self.load_code_string("F3 AE F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.CX, 15)
        self.assertEqual(self.cpu.regs.DI, 0x0009)
        self.assert_flags("oSzPC") # ODITSZAPC
        
    def test_repnz_cancels_after_one(self):
        """
        repnz scasb
        scasb
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AL = 0x02
        self.cpu.regs.CX = 3
        self.cpu.flags.zero = True # Should not cause it to immediately terminate.
        self.memory.mem_write_byte(20, 0x01)
        self.memory.mem_write_byte(21, 0x01)
        self.memory.mem_write_byte(22, 0x01) # This also tests exit on CX == 0.
        self.memory.mem_write_byte(23, 0x01)
        self.memory.mem_write_byte(24, 0x02)
        self.load_code_string("F2 AE AE F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.CX, 0)
        self.assertEqual(self.cpu.regs.DI, 0x0008)
        self.assert_flags("oszpc") # ODITSZAPC - We should not hit the matching case.
        
    def test_repz_cancels_after_one(self):
        """
        repz scasb
        scasb
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AL = 0x01
        self.cpu.regs.CX = 3
        self.cpu.flags.zero = False # Should not cause it to immediately terminate.
        self.memory.mem_write_byte(20, 0x01)
        self.memory.mem_write_byte(21, 0x01)
        self.memory.mem_write_byte(22, 0x01) # This also tests exit on CX == 0.
        self.memory.mem_write_byte(23, 0x01)
        self.memory.mem_write_byte(24, 0x02)
        self.load_code_string("F3 AE AE F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.CX, 0)
        self.assertEqual(self.cpu.regs.DI, 0x0008)
        self.assert_flags("osZPc") # ODITSZAPC - We should not hit the matching case.
        
    def test_repnz_skip_if_cx_zero(self):
        """
        repnz scasb
        hlt
        """
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AL = 0x02
        self.cpu.regs.CX = 0
        self.load_code_string("F2 AE F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.CX, 0)
        self.assertEqual(self.cpu.regs.DI, 0x0004)
        
    def test_repz_skip_if_cx_zero(self):
        """
        repz scasb
        hlt
        """
        self.cpu.regs.ES = 0x0001
        self.cpu.regs.DI = 0x0004
        self.cpu.regs.AL = 0x01
        self.cpu.regs.CX = 0
        self.load_code_string("F3 AE F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.CX, 0)
        self.assertEqual(self.cpu.regs.DI, 0x0004)
        
class RetfOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_retf_simple(self):
        """
        retf
        hlt
        TIMES (0x14 - ($ - $$)) db 0x00
        inc al
        hlt
        """
        self.cpu.regs.SS = 0x0000
        self.cpu.regs.SP = 0x00FC
        self.memory.mem_write_word(0x00FC, 0x0004)
        self.memory.mem_write_word(0x00FE, 0x0001)
        self.load_code_string("CB F4 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        self.assertEqual(self.cpu.regs.SP, 0x0100)
        self.assertEqual(self.cpu.regs.CS, 0x0001)
        self.assertEqual(self.cpu.regs.IP, 0x0007) # Next instruction after the hlt.
        
    def test_retf_imm16(self):
        """
        retf 0x6
        hlt
        TIMES (0x14 - ($ - $$)) db 0x00
        inc al
        hlt
        """
        self.cpu.regs.SS = 0x0000
        self.cpu.regs.SP = 0x00FC
        self.memory.mem_write_word(0x00FC, 0x0004)
        self.memory.mem_write_word(0x00FE, 0x0001)
        self.load_code_string("CA 06 00 F4 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        self.assertEqual(self.cpu.regs.SP, 0x0106)
        self.assertEqual(self.cpu.regs.CS, 0x0001)
        self.assertEqual(self.cpu.regs.IP, 0x0007) # Next instruction after the hlt.
        
class RorOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_ror_rm8_1_simple(self):
        """
        ror al, 1
        hlt
        """
        self.cpu.regs.AL = 0xF0
        self.load_code_string("D0 C8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x78)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertFalse(self.cpu.flags.carry)
        
    def test_ror_rm8_1_wrap_around(self):
        """
        ror al, 1
        hlt
        """
        self.cpu.regs.AL = 0x01
        self.load_code_string("D0 C8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x80)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertTrue(self.cpu.flags.carry)
        
    def test_ror_rm8_cl(self):
        """
        ror al, cl
        hlt
        """
        self.cpu.regs.AL = 0x01
        self.cpu.regs.CL = 2
        self.load_code_string("D2 C8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x40)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertFalse(self.cpu.flags.carry)
        
    def test_ror_rm16_1_simple(self):
        """
        ror ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x0F00
        self.load_code_string("D1 C8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0780)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_ror_rm16_1_wrap_around(self):
        """
        ror ax, 1
        hlt
        """
        self.cpu.regs.AX = 0x0001
        self.load_code_string("D1 C8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x8000)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_ror_rm16_cl(self):
        """
        ror ax, cl
        hlt
        """
        self.cpu.regs.AX = 0x1000
        self.cpu.regs.CL = 9
        self.load_code_string("D3 C8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0008)
        self.assertFalse(self.cpu.flags.carry)
        
class XlatOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_xlat_simple(self):
        """
        xlat
        hlt
        """
        self.memory.mem_write_byte(0x0137, 0xAA)
        self.cpu.regs.BX = 0x0100
        self.cpu.regs.AL = 0x37
        self.load_code_string("D7 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0xAA)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        
    def test_xlat_zero(self):
        """
        xlat
        hlt
        """
        self.memory.mem_write_byte(0x0100, 0x55)
        self.cpu.regs.BX = 0x0100
        self.cpu.regs.AL = 0x00
        self.load_code_string("D7 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x55)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        
    def test_xlat_max(self):
        """
        xlat
        hlt
        """
        self.memory.mem_write_byte(0x01FF, 0xA5)
        self.cpu.regs.BX = 0x0100
        self.cpu.regs.AL = 0xFF
        self.load_code_string("D7 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0xA5)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        
class ImmediateOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_sign_extend_byte_to_word(self):
        """
        add bx, -1
        hlt
        """
        self.cpu.regs.BX = 0x1234
        self.load_code_string("83 C3 FF F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.BX, 0x1233)
        
class CallOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_call_rm16(self):
        """
        mov bx, ham
        call bx
        inc cl
        hlt

        ham:
        inc al
        hlt
        """
        self.cpu.regs.SP = 0x0100
        self.load_code_string("BB 08 00 FF D3 FE C1 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 4)
        self.assertEqual(self.cpu.regs.AL, 1)
        self.assertEqual(self.cpu.regs.CL, 0) # We don't actually return in this test.
        self.assertEqual(self.cpu.regs.SP, 0x00FE)
        self.assertEqual(self.memory.mem_read_word(0x00FE), 0x0005) # Return should point back at INC cl.
        self.assertEqual(self.cpu.regs.CS, 0x0000)
        self.assertEqual(self.cpu.regs.IP, 0x000B) # Next instruction after the second hlt.
        
    def test_call_relative_forward(self):
        """
        call ham
        inc cl
        hlt
        
        ham:
        inc al
        hlt
        """
        self.cpu.regs.SP = 0x0100
        self.load_code_string("E8 03 00 FE C1 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        self.assertEqual(self.cpu.regs.CL, 0) # We don't actually return in this test.
        self.assertEqual(self.cpu.regs.SP, 0x00FE)
        self.assertEqual(self.memory.mem_read_word(0x00FE), 0x0003) # Return should point back at INC cl.
        self.assertEqual(self.cpu.regs.CS, 0x0000)
        self.assertEqual(self.cpu.regs.IP, 0x0009) # Next instruction after the second hlt.
        
    def test_call_relative_backward(self):
        """
        ham:
        inc al
        hlt
        
        call ham
        inc cl
        hlt
        """
        self.cpu.regs.SP = 0x0100
        self.load_code_string("FE C0 F4 E8 FA FF FE C1 F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0003), 3) # Start at CALL ham.
        self.assertEqual(self.cpu.regs.AL, 1)
        self.assertEqual(self.cpu.regs.CL, 0) # We don't actually return in this test.
        self.assertEqual(self.cpu.regs.SP, 0x00FE)
        self.assertEqual(self.memory.mem_read_word(0x00FE), 0x0006) # Return should point back at INC cl.
        self.assertEqual(self.cpu.regs.CS, 0x0000)
        self.assertEqual(self.cpu.regs.IP, 0x0003) # Next instruction after the first hlt.
        
    def test_callf_immediate(self):
        """
        call 0x0001:0x0002
        TIMES (0x10 - ($ - $$)) nop
        inc ax ; Should be skipped
        inc bx ; Should be skipped
        inc cx
        hlt
        """
        self.cpu.regs.SP = 0x0100
        self.load_code_string("9A 02 00 01 00 90 90 90 90 90 90 90 90 90 90 90 40 43 41 F4")
        self.assertEqual(self.run_to_halt(), 3) # Skip the NOPs.
        self.assertEqual(self.cpu.regs.AX, 0)
        self.assertEqual(self.cpu.regs.BX, 0)
        self.assertEqual(self.cpu.regs.CX, 1)
        self.assertEqual(self.cpu.regs.SP, 0x00FC) # 2 words.
        self.assertEqual(self.memory.mem_read_word(0x00FE), 0x0000) # Original CS.
        self.assertEqual(self.memory.mem_read_word(0x00FC), 0x0005) # Original IP (first NOP).
        self.assertEqual(self.cpu.regs.CS, 0x0001)
        self.assertEqual(self.cpu.regs.IP, 0x0004) # Next instruction after the hlt.
        
    def test_callf_dword_pointer(self):
        """
        call [0x24]
        TIMES (0x10 - ($ - $$)) nop
        inc ax ; Should be skipped
        inc bx ; Should be skipped
        inc cx
        hlt
        TIMES (0x24 - ($ - $$)) nop
        dw 0x0002 ; IP
        dw 0x0001 ; CS
        """
        self.cpu.regs.SP = 0x0100
        self.load_code_string("FF 1E 24 00 90 90 90 90 90 90 90 90 90 90 90 90 40 43 41 F4 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 02 00 01 00")
        self.assertEqual(self.run_to_halt(), 3) # Skip the NOPs.
        self.assertEqual(self.cpu.regs.AX, 0)
        self.assertEqual(self.cpu.regs.BX, 0)
        self.assertEqual(self.cpu.regs.CX, 1)
        self.assertEqual(self.cpu.regs.SP, 0x00FC) # 2 words.
        self.assertEqual(self.memory.mem_read_word(0x00FE), 0x0000) # Original CS.
        self.assertEqual(self.memory.mem_read_word(0x00FC), 0x0004) # Original IP (first NOP).
        self.assertEqual(self.cpu.regs.CS, 0x0001)
        self.assertEqual(self.cpu.regs.IP, 0x0004) # Next instruction after the hlt.
        
class RclOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_rcl_rm8_1_carry_in(self):
        """
        rcl al, 1
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AL = 0x08
        self.load_code_string("D0 D0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x11)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertFalse(self.cpu.flags.carry)
        
    def test_rcl_rm8_1_carry_out(self):
        """
        rcl al, 1
        hlt
        """
        self.cpu.flags.carry = False
        self.cpu.regs.AL = 0xF0
        self.load_code_string("D0 D0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0xE0)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertTrue(self.cpu.flags.carry)
        
    def test_rcl_rm8_cl(self):
        """
        rcl al, cl
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AL = 0x81
        self.cpu.regs.CL = 2
        self.load_code_string("D2 D0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x07)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertFalse(self.cpu.flags.carry)
        
    def test_rcl_rm16_1_carry_in(self):
        """
        rcl ax, 1
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AX = 0x0080
        self.load_code_string("D1 D0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0101)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_rcl_rm16_1_carry_out(self):
        """
        rcl ax, 1
        hlt
        """
        self.cpu.flags.carry = False
        self.cpu.regs.AX = 0x9000
        self.load_code_string("D1 D0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x2000)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_rcl_rm16_cl(self):
        """
        rcl ax, cl
        hlt
        """
        self.cpu.flags.carry = False
        self.cpu.regs.AX = 0x9000
        self.cpu.regs.CL = 2
        self.load_code_string("D3 D0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x4001)
        self.assertFalse(self.cpu.flags.carry)
        
class InvalidOpcodeTests(BaseOpcodeAcceptanceTests):
    def assert_throws_invalid_opcode(self, code_string):
        self.load_code_string(code_string)
        with self.assertRaises(InvalidOpcodeException) as context:
            self.run_to_halt()
            
    def test_0f_not_valid_for_808x(self):
        self.assert_throws_invalid_opcode("0F")
        
    def test_6x_not_valid_for_808x(self):
        self.assert_throws_invalid_opcode("60")
        self.assert_throws_invalid_opcode("61")
        self.assert_throws_invalid_opcode("62")
        self.assert_throws_invalid_opcode("63")
        self.assert_throws_invalid_opcode("64")
        self.assert_throws_invalid_opcode("65")
        self.assert_throws_invalid_opcode("66")
        self.assert_throws_invalid_opcode("67")
        self.assert_throws_invalid_opcode("68")
        self.assert_throws_invalid_opcode("69")
        self.assert_throws_invalid_opcode("6A")
        self.assert_throws_invalid_opcode("6B")
        self.assert_throws_invalid_opcode("6C")
        self.assert_throws_invalid_opcode("6D")
        self.assert_throws_invalid_opcode("6E")
        self.assert_throws_invalid_opcode("6F")
        
    def test_cx_not_valid_for_808x(self):
        self.assert_throws_invalid_opcode("C0")
        self.assert_throws_invalid_opcode("C1")
        self.assert_throws_invalid_opcode("C8")
        self.assert_throws_invalid_opcode("C9")
        
    def test_d6_not_valid_for_808x(self):
        self.assert_throws_invalid_opcode("D6")
        
    def test_f1_not_valid_for_808x(self):
        self.assert_throws_invalid_opcode("F1")
        
class JoOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_taken(self):
        """
        jo location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.overflow = True
        self.load_code_string("70 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken(self):
        """
        jo location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.overflow = False
        self.load_code_string("70 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_can_be_backward(self):
        """
        location: inc al
        hlt
        jo location
        hlt
        """
        self.cpu.flags.overflow = True
        self.load_code_string("FE C0 F4 70 FB F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0003), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JnoOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_taken(self):
        """
        jno location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.overflow = False
        self.load_code_string("71 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken(self):
        """
        jno location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.overflow = True
        self.load_code_string("71 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_can_be_backward(self):
        """
        location: inc al
        hlt
        jno location
        hlt
        """
        self.cpu.flags.overflow = False
        self.load_code_string("FE C0 F4 71 FB F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0003), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JcOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_taken(self):
        """
        jc location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.carry = True
        self.load_code_string("72 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken(self):
        """
        jc location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.carry = False
        self.load_code_string("72 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_can_be_backward(self):
        """
        location: inc al
        hlt
        jc location
        hlt
        """
        self.cpu.flags.carry = True
        self.load_code_string("FE C0 F4 72 FB F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0003), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JncOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_taken(self):
        """
        jnc location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.carry = False
        self.load_code_string("73 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken(self):
        """
        jnc location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.carry = True
        self.load_code_string("73 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_can_be_backward(self):
        """
        location: inc al
        hlt
        jnc location
        hlt
        """
        self.cpu.flags.carry = False
        self.load_code_string("FE C0 F4 73 FB F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0003), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JzOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_taken(self):
        """
        jz location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.zero = True
        self.load_code_string("74 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken(self):
        """
        jz location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.zero = False
        self.load_code_string("74 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_can_be_backward(self):
        """
        location: inc al
        hlt
        jz location
        hlt
        """
        self.cpu.flags.zero = True
        self.load_code_string("FE C0 F4 74 FB F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0003), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JnzOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_taken(self):
        """
        jnz location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.zero = False
        self.load_code_string("75 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken(self):
        """
        jnz location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.zero = True
        self.load_code_string("75 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_can_be_backward(self):
        """
        location: inc al
        hlt
        jnz location
        hlt
        """
        self.cpu.flags.zero = False
        self.load_code_string("FE C0 F4 75 FB F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0003), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JnaOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_taken_only_carry_set(self):
        """
        jna location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.carry = True
        self.load_code_string("76 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_taken_only_zero_set(self):
        """
        jna location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.zero = True
        self.load_code_string("76 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken_both_clear(self):
        """
        jna location
        hlt
        location: inc al
        hlt
        """
        self.load_code_string("76 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_taken_both_set(self):
        """
        jna location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.flags.zero = True
        self.load_code_string("76 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_can_be_backward(self):
        """
        location: inc ax
        hlt
        jna location
        hlt
        """
        self.cpu.flags.carry = True
        self.load_code_string("40 F4 76 FC F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0002), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JaOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_not_taken_only_carry_set(self):
        """
        ja location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.carry = True
        self.load_code_string("77 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_not_taken_only_zero_set(self):
        """
        ja location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.zero = True
        self.load_code_string("77 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_taken_both_clear(self):
        """
        ja location
        hlt
        location: inc al
        hlt
        """
        self.load_code_string("77 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken_both_set(self):
        """
        ja location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.flags.zero = True
        self.load_code_string("77 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_can_be_backward(self):
        """
        location: inc ax
        hlt
        ja location
        hlt
        """
        self.load_code_string("40 F4 77 FC F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0002), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JsOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_taken(self):
        """
        js location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.sign = True
        self.load_code_string("78 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken(self):
        """
        js location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.sign = False
        self.load_code_string("78 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_can_be_backward(self):
        """
        location: inc al
        hlt
        js location
        hlt
        """
        self.cpu.flags.sign = True
        self.load_code_string("FE C0 F4 78 FB F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0003), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JnsOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_taken(self):
        """
        jns location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.sign = False
        self.load_code_string("79 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken(self):
        """
        jns location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.sign = True
        self.load_code_string("79 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_can_be_backward(self):
        """
        location: inc al
        hlt
        jns location
        hlt
        """
        self.cpu.flags.sign = False
        self.load_code_string("FE C0 F4 79 FB F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0003), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JpOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_taken(self):
        """
        jp location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.parity = True
        self.load_code_string("7A 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken(self):
        """
        jp location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.parity = False
        self.load_code_string("7A 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_can_be_backward(self):
        """
        location: inc al
        hlt
        jp location
        hlt
        """
        self.cpu.flags.parity = True
        self.load_code_string("FE C0 F4 7A FB F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0003), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JnpOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_taken(self):
        """
        jnp location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.parity = False
        self.load_code_string("7B 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
    def test_jump_not_taken(self):
        """
        jnp location
        hlt
        location: inc al
        hlt
        """
        self.cpu.flags.parity = True
        self.load_code_string("7B 01 F4 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0)
        
    def test_jump_can_be_backward(self):
        """
        location: inc al
        hlt
        jnp location
        hlt
        """
        self.cpu.flags.parity = False
        self.load_code_string("FE C0 F4 7B FB F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0003), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JleOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_conditions(self):
        """
        jle location
        hlt
        location: inc al
        hlt
        """
        test_data = (
            # Sign, Overflow,   Zero,   Jump should be taken
            (False, False,      False,  False),
            (False, False,      True,   True),
            (False, True,       False,  True),
            (False, True,       True,   True),
            (True,  False,      False,  True),
            (True,  False,      True,   True),
            (True,  True,       False,  False),
            (True,  True,       True,   True),
        )
        
        self.load_code_string("7E 01 F4 FE C0 F4")
        
        for self.cpu.flags.sign, self.cpu.flags.overflow, self.cpu.flags.zero, jump_should_be_taken in test_data:
            self.cpu.regs.AL = 0
            
            if jump_should_be_taken:
                self.assertEqual(self.run_to_halt(), 3)
                self.assertEqual(self.cpu.regs.AL, 1)
            else:
                self.assertEqual(self.run_to_halt(), 2)
                self.assertEqual(self.cpu.regs.AL, 0)
                
    def test_jump_can_be_backward(self):
        """
        location: inc al
        hlt
        jle location
        hlt
        """
        self.cpu.flags.zero = True
        self.load_code_string("FE C0 F4 7E FB F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0003), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class JnleOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_jump_conditions(self):
        """
        jnle location
        hlt
        location: inc al
        hlt
        """
        test_data = (
            # Sign, Overflow,   Zero,   Jump should be taken
            (False, False,      False,  True),
            (False, False,      True,   False),
            (False, True,       False,  False),
            (False, True,       True,   False),
            (True,  False,      False,  False),
            (True,  False,      True,   False),
            (True,  True,       False,  True),
            (True,  True,       True,   False),
        )
        
        self.load_code_string("7F 01 F4 FE C0 F4")
        
        for self.cpu.flags.sign, self.cpu.flags.overflow, self.cpu.flags.zero, jump_should_be_taken in test_data:
            self.cpu.regs.AL = 0
            
            if jump_should_be_taken:
                self.assertEqual(self.run_to_halt(), 3)
                self.assertEqual(self.cpu.regs.AL, 1)
            else:
                self.assertEqual(self.run_to_halt(), 2)
                self.assertEqual(self.cpu.regs.AL, 0)
                
    def test_jump_can_be_backward(self):
        """
        location: inc al
        hlt
        jnle location
        hlt
        """
        self.load_code_string("FE C0 F4 7F FB F4")
        self.assertEqual(self.run_to_halt(starting_ip = 0x0003), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        
class LeaTests(BaseOpcodeAcceptanceTests):
    def test_lea_direct(self):
        """
        lea ax, [foo]
        hlt
        foo:
            db 72
        """
        self.load_code_string("8D 06 05 00 F4 48")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 5)
        
    def test_lea_indirect(self):
        """
        lea ax, [bx + 6]
        hlt
        """
        self.cpu.regs.BX = 0x1000
        self.load_code_string("8D 47 06 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x1006)
        
class CmpsOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_cmpsb_incrementing(self):
        """
        cmpsb
        hlt
        foo: db "foo", 0
        bar: db "bar", 0
        """
        self.cpu.flags.direction = False
        self.cpu.regs.SI = 0x0002
        self.cpu.regs.DI = 0x0006
        self.load_code_string("A6 F4 66 6F 6F 00 62 61 72 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SI, 0x0003)
        self.assertEqual(self.cpu.regs.DI, 0x0007)
        self.assertEqual(self.memory.mem_read_byte(0x0002), 0x66) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(0x0006), 0x62) # Should be unmodified
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_cmpsb_decrementing(self):
        """
        cmpsb
        hlt
        foo: db "foo", 0
        bar: db "bar", 0
        """
        self.cpu.flags.direction = True
        self.cpu.regs.SI = 0x0002
        self.cpu.regs.DI = 0x0006
        self.load_code_string("A6 F4 66 6F 6F 00 62 61 72 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SI, 0x0001)
        self.assertEqual(self.cpu.regs.DI, 0x0005)
        self.assertEqual(self.memory.mem_read_byte(0x0002), 0x66) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(0x0006), 0x62) # Should be unmodified
        self.assert_flags("oszpc") # ODITSZAPC
        
    def test_cmpsb_zero(self):
        """
        cmpsb
        hlt
        """
        self.cpu.flags.direction = False
        self.cpu.regs.SI = 0x0010
        self.cpu.regs.DI = 0x0020
        self.load_code_string("A6 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SI, 0x0011)
        self.assertEqual(self.cpu.regs.DI, 0x0021)
        self.assert_flags("osZPc") # ODITSZAPC
        
    def test_cmpsb_negative(self):
        """
        cmpsb
        hlt
        foo: db "foo", 0
        bar: db "bar", 0
        """
        self.cpu.flags.direction = False
        self.cpu.regs.SI = 0x0006 # Switched SI and DI from previous tests.
        self.cpu.regs.DI = 0x0002
        self.load_code_string("A6 F4 66 6F 6F 00 62 61 72 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.SI, 0x0007)
        self.assertEqual(self.cpu.regs.DI, 0x0003)
        self.assertEqual(self.memory.mem_read_byte(0x0002), 0x66) # Should be unmodified.
        self.assertEqual(self.memory.mem_read_byte(0x0006), 0x62) # Should be unmodified
        self.assert_flags("oSzPC") # ODITSZAPC
        
class CwdOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_cwd_zero(self):
        """
        cwd
        hlt
        """
        self.cpu.regs.DX = 0xAA55
        self.cpu.regs.AX = 0x0000
        self.load_code_string("99 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DX, 0x0000)
        self.assertEqual(self.cpu.regs.AX, 0x0000) # Should be unmodified.
        
    def test_cwd_positive(self):
        """
        cwd
        hlt
        """
        self.cpu.regs.DX = 0xAA55
        self.cpu.regs.AX = 0x7FFF
        self.load_code_string("99 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DX, 0x0000)
        self.assertEqual(self.cpu.regs.AX, 0x7FFF) # Should be unmodified.
        
    def test_cwd_negative(self):
        """
        cwd
        hlt
        """
        self.cpu.regs.DX = 0xAA55
        self.cpu.regs.AX = 0x8000
        self.load_code_string("99 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.DX, 0xFFFF)
        self.assertEqual(self.cpu.regs.AX, 0x8000) # Should be unmodified.
        
class RcrOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_rcr_rm8_1_carry_in(self):
        """
        rcr al, 1
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AL = 0x10
        self.load_code_string("D0 D8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x88)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertFalse(self.cpu.flags.carry)
        
    def test_rcr_rm8_1_carry_out(self):
        """
        rcr al, 1
        hlt
        """
        self.cpu.flags.carry = False
        self.cpu.regs.AL = 0x0F
        self.load_code_string("D0 D8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0x07)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertTrue(self.cpu.flags.carry)
        
    def test_rcr_rm8_cl(self):
        """
        rcr al, cl
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AL = 0x81
        self.cpu.regs.CL = 2
        self.load_code_string("D2 D8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 0xE0)
        self.assertEqual(self.cpu.regs.AH, 0x00) # Should be unmodified.
        self.assertFalse(self.cpu.flags.carry)
        
    def test_rcr_rm16_1_carry_in(self):
        """
        rcr ax, 1
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.regs.AX = 0x0100
        self.load_code_string("D1 D8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x8080)
        self.assertFalse(self.cpu.flags.carry)
        
    def test_rcr_rm16_1_carry_out(self):
        """
        rcr ax, 1
        hlt
        """
        self.cpu.flags.carry = False
        self.cpu.regs.AX = 0x0009
        self.load_code_string("D1 D8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0004)
        self.assertTrue(self.cpu.flags.carry)
        
    def test_rcr_rm16_cl(self):
        """
        rcr ax, cl
        hlt
        """
        self.cpu.flags.carry = False
        self.cpu.regs.AX = 0x0009
        self.cpu.regs.CL = 2
        self.load_code_string("D3 D8 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x8002)
        self.assertFalse(self.cpu.flags.carry)
        
class IdivOpcodeTests(BaseOpcodeAcceptanceTests):
    def setUp(self):
        super(IdivOpcodeTests, self).setUp()
        self.local_interrupt_log = []
        self.cpu.internal_service_interrupt = self.service_interrupt_hook
        
    def service_interrupt_hook(self, interrupt):
        self.local_interrupt_log.append(interrupt)
        
    def test_idiv_by_byte(self):
        """
        idiv bl
        hlt
        """
        self.cpu.regs.AX = 1000
        self.cpu.regs.BL = 14
        self.load_code_string("F6 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 71)
        self.assertEqual(self.cpu.regs.AH, 6)
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_idiv_by_byte_no_remainder(self):
        """
        idiv bl
        hlt
        """
        self.cpu.regs.AX = 1000
        self.cpu.regs.BL = 10
        self.load_code_string("F6 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 100)
        self.assertEqual(self.cpu.regs.AH, 0)
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_idiv_by_byte_zero(self):
        """
        idiv bl
        hlt
        """
        self.cpu.regs.AX = 1000
        self.cpu.regs.BL = 0
        self.load_code_string("F6 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.local_interrupt_log, [0])
        
    def test_idiv_by_byte_result_too_big(self):
        """
        idiv bl
        hlt
        """
        self.cpu.regs.AX = 1280
        self.cpu.regs.BL = 10
        self.load_code_string("F6 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.local_interrupt_log, [0]) # 128 is bigger than 127
        
    def test_idiv_by_byte_negative_dividend(self):
        """
        idiv bl
        hlt
        """
        self.cpu.regs.AX = -1000
        self.cpu.regs.BL = 14
        self.load_code_string("F6 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 185) # -71, Determined by operands.
        self.assertEqual(self.cpu.regs.AH, 250) # -6, Same sign as dividend.
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_idiv_by_byte_negative_divisor(self):
        """
        idiv bl
        hlt
        """
        self.cpu.regs.AX = 1000
        self.cpu.regs.BL = -14
        self.load_code_string("F6 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 185) # -71, Determined by operands.
        self.assertEqual(self.cpu.regs.AH, 6) # Same sign as dividend.
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_idiv_by_byte_both_negative(self):
        """
        idiv bl
        hlt
        """
        self.cpu.regs.AX = -1000
        self.cpu.regs.BL = -14
        self.load_code_string("F6 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AL, 71) # Determined by operands.
        self.assertEqual(self.cpu.regs.AH, 250) # -6, Same sign as dividend.
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_idiv_by_byte_result_too_big_negative(self):
        """
        idiv bl
        hlt
        """
        self.cpu.regs.AX = -1280
        self.cpu.regs.BL = 10
        self.load_code_string("F6 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.local_interrupt_log, [0]) # -128 is smaller than -127
        
    def test_idiv_by_word(self):
        """
        idiv bx
        hlt
        """
        self.cpu.regs.DX = 0x000F # 1,000,000
        self.cpu.regs.AX = 0x4240
        self.cpu.regs.BX = 77
        self.load_code_string("F7 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 12987)
        self.assertEqual(self.cpu.regs.DX, 1)
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_idiv_by_word_no_remainder(self):
        """
        idiv bx
        hlt
        """
        self.cpu.regs.DX = 0x000F # 1,000,000
        self.cpu.regs.AX = 0x4240
        self.cpu.regs.BX = 1000
        self.load_code_string("F7 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 1000)
        self.assertEqual(self.cpu.regs.DX, 0)
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_idiv_by_word_zero(self):
        """
        idiv bx
        hlt
        """
        self.cpu.regs.DX = 0x000F # 1,000,000
        self.cpu.regs.AX = 0x4240
        self.cpu.regs.BX = 0
        self.load_code_string("F7 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.local_interrupt_log, [0])
        
    def test_idiv_by_word_result_too_big(self):
        """
        idiv bx
        hlt
        """
        self.cpu.regs.DX = 0x0005 # 327,680
        self.cpu.regs.AX = 0x0000
        self.cpu.regs.BX = 10
        self.load_code_string("F7 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.local_interrupt_log, [0])
        
    def test_idiv_by_word_negative_dividend(self):
        """
        idiv bx
        hlt
        """
        self.cpu.regs.DX = 0xFFF0 # -1,000,000
        self.cpu.regs.AX = 0xBDC0
        self.cpu.regs.BX = 77
        self.load_code_string("F7 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xCD45) # -12987, Determined by operands.
        self.assertEqual(self.cpu.regs.DX, 0xFFFF) # -1, Same sign as dividend.
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_idiv_by_word_negative_divisor(self):
        """
        idiv bx
        hlt
        """
        self.cpu.regs.DX = 0x000F # 1,000,000
        self.cpu.regs.AX = 0x4240
        self.cpu.regs.BX = -77
        self.load_code_string("F7 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xCD45) # -12987, Determined by operands.
        self.assertEqual(self.cpu.regs.DX, 1) # -1, Same sign as dividend.
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_idiv_by_word_both_negative(self):
        """
        idiv bx
        hlt
        """
        self.cpu.regs.DX = 0xFFF0 # -1,000,000
        self.cpu.regs.AX = 0xBDC0
        self.cpu.regs.BX = -77
        self.load_code_string("F7 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 12987) # 12987, Determined by operands.
        self.assertEqual(self.cpu.regs.DX, 0xFFFF) # -1, Same sign as dividend.
        self.assertEqual(self.local_interrupt_log, [])
        
    def test_idiv_by_word_result_too_big_negative(self):
        """
        idiv bx
        hlt
        """
        self.cpu.regs.DX = 0xFFFB # -327,680
        self.cpu.regs.AX = 0x0000
        self.cpu.regs.BX = 10
        self.load_code_string("F7 FB F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.local_interrupt_log, [0])
        
class ImulOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_imul_al_rm8_small(self):
        """
        imul byte [value]
        hlt
        value:
            db 25
        """
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.cpu.regs.AH = 0xA5 # Should be ignored.
        self.cpu.regs.AL = 5
        self.load_code_string("F6 2E 05 00 F4 19")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x007D) # 125
        self.assertFalse(self.cpu.flags.carry)
        self.assertFalse(self.cpu.flags.overflow)
        
    def test_imul_al_rm8_large(self):
        """
        imul byte [value]
        hlt
        value:
            db 25
        """
        self.cpu.regs.AH = 0xA5 # Should be ignored.
        self.cpu.regs.AL = 0x7F
        self.load_code_string("F6 2E 05 00 F4 19")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0C67) # 3175
        self.assertTrue(self.cpu.flags.carry)
        self.assertTrue(self.cpu.flags.overflow)
        
    def test_imul_al_rm8_negative_small(self):
        """
        imul byte [value]
        hlt
        value:
            db 25
        """
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.cpu.regs.AH = 0xA5 # Should be ignored.
        self.cpu.regs.AL = -5
        self.load_code_string("F6 2E 05 00 F4 19")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xFF83) # -125
        self.assertFalse(self.cpu.flags.carry)
        self.assertFalse(self.cpu.flags.overflow)
        
    def test_imul_al_rm8_negative_large(self):
        """
        imul byte [value]
        hlt
        value:
            db 25
        """
        self.cpu.regs.AH = 0xA5 # Should be ignored.
        self.cpu.regs.AL = -7
        self.load_code_string("F6 2E 05 00 F4 19")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xFF51) # -175
        self.assertTrue(self.cpu.flags.carry)
        self.assertTrue(self.cpu.flags.overflow)
        
    def test_imul_al_rm8_negative_rm8(self):
        """
        imul byte [value]
        hlt
        value:
            db -25
        """
        self.cpu.regs.AH = 0xA5 # Should be ignored.
        self.cpu.regs.AL = 7
        self.load_code_string("F6 2E 05 00 F4 E7")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xFF51) # -175
        self.assertTrue(self.cpu.flags.carry)
        self.assertTrue(self.cpu.flags.overflow)
        
    def test_imul_ax_rm16_small(self):
        """
        imul word [value]
        hlt
        value:
            dw 25
        """
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.cpu.regs.AX = 400
        self.load_code_string("F7 2E 05 00 F4 19 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x2710) # 10000
        self.assertEqual(self.cpu.regs.DX, 0x0000)
        self.assertFalse(self.cpu.flags.carry)
        self.assertFalse(self.cpu.flags.overflow)
        
    def test_imul_ax_rm16_large(self):
        """
        imul word [value]
        hlt
        value:
            dw 25
        """
        self.cpu.regs.AX = 0x7FFF
        self.load_code_string("F7 2E 05 00 F4 19 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x7FE7) # 819175
        self.assertEqual(self.cpu.regs.DX, 0x000C)
        self.assertTrue(self.cpu.flags.carry)
        self.assertTrue(self.cpu.flags.overflow)
        
    def test_imul_ax_rm16_negative_small(self):
        """
        imul word [value]
        hlt
        value:
            dw 25
        """
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.cpu.regs.AX = -400
        self.load_code_string("F7 2E 05 00 F4 19 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0xD8F0) # -10000
        self.assertEqual(self.cpu.regs.DX, 0xFFFF)
        self.assertFalse(self.cpu.flags.carry)
        self.assertFalse(self.cpu.flags.overflow)
        
    def test_imul_ax_rm16_negative_large(self):
        """
        imul word [value]
        hlt
        value:
            dw 25
        """
        self.cpu.regs.AX = 0x8001
        self.load_code_string("F7 2E 05 00 F4 19 00")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x8019) # -819175
        self.assertEqual(self.cpu.regs.DX, 0xFFF3)
        self.assertTrue(self.cpu.flags.carry)
        self.assertTrue(self.cpu.flags.overflow)
        
    def test_imul_ax_rm16_negative_rm16(self):
        """
        imul word [value]
        hlt
        value:
            dw -25
        """
        self.cpu.regs.AX = 0x7FFF
        self.load_code_string("F7 2E 05 00 F4 E7 FF")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x8019) # -819175
        self.assertEqual(self.cpu.regs.DX, 0xFFF3)
        self.assertTrue(self.cpu.flags.carry)
        self.assertTrue(self.cpu.flags.overflow)
        
class GeneralShiftOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_shift_by_zero_does_nothing(self):
        """
        shl ax, cl
        hlt
        """
        self.cpu.flags.carry = True
        self.cpu.flags.overflow = True
        self.cpu.regs.AX = 0x0001
        self.cpu.regs.CL = 0
        self.load_code_string("D3 E0 F4")
        self.assertEqual(self.run_to_halt(), 2)
        self.assertEqual(self.cpu.regs.AX, 0x0001) # Should be unmodified.
        
        # Ordinarily these would be the last shifted out value, but since we shifted by
        # zero they are unmodified.
        self.assertTrue(self.cpu.flags.carry) # Should be unmodified.
        self.assertTrue(self.cpu.flags.overflow) # Should be unmodified.
        

class RetOpcodeTests(BaseOpcodeAcceptanceTests):
    def test_ret_simple(self):
        """
        ret
        hlt
        TIMES (0x10 - ($ - $$)) db 0x00
        inc al
        hlt
        """
        self.cpu.regs.SS = 0x0000
        self.cpu.regs.SP = 0x00FE
        self.memory.mem_write_word(0x00FE, 0x0010) # Will be IP after the RET.
        self.load_code_string("C3 F4 00 00 00 00 00 00 00 00 00 00 00 00 00 00 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        self.assertEqual(self.cpu.regs.SP, 0x0100)
        self.assertEqual(self.cpu.regs.IP, 0x0013) # Next instruction after the hlt.
        
    def test_ret_imm16(self):
        """
        ret 0x6
        hlt
        TIMES (0x10 - ($ - $$)) db 0x00
        inc al
        hlt
        """
        self.cpu.regs.SS = 0x0000
        self.cpu.regs.SP = 0x00FE
        self.memory.mem_write_word(0x00FE, 0x0010) # Will be IP after the RET.
        self.load_code_string("C2 06 00 F4 00 00 00 00 00 00 00 00 00 00 00 00 FE C0 F4")
        self.assertEqual(self.run_to_halt(), 3)
        self.assertEqual(self.cpu.regs.AL, 1)
        self.assertEqual(self.cpu.regs.SP, 0x0106)
        self.assertEqual(self.cpu.regs.IP, 0x0013) # Next instruction after the hlt.
        
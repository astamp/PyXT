"""
pyxt.cpu - 8088-ish CPU module for PyXT.
"""

# Standard library imports
import struct
import operator
from ctypes import Structure, Union, c_ushort, c_ubyte

# PyXT imports
from pyxt.exceptions import InvalidOpcodeException
from pyxt.helpers import *

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants
WORD, LOW, HIGH = range(3)

MOD_MASK = 0xC0
MOD_SHIFT = 6
MOD_SPECIAL = 0x00
MOD_8_BIT = 0x01
MOD_16_BIT = 0x02
MOD_RM_IS_REG = 0x03

REG_MASK = 0x38
REG_SHIFT = 3
RM_MASK = 0x07

UNKNOWN = 0
ADDRESS = 1
REGISTER = 2

# Repeat prefixes.
# REP is valid for: INS, OUTS, MOVS, LODS, STOS
# REPZ, REPNZ are valid for: CMPS, SCAS
REPEAT_NONE = 0
REPEAT_REP_REPZ = 0xF3
REPEAT_REPNZ = 0xF2

INT_DIVIDE_ERROR = 0

BYTE_REG = {
    0x00 : "AL",
    0x01 : "CL",
    0x02 : "DL",
    0x03 : "BL",
    0x04 : "AH",
    0x05 : "CH",
    0x06 : "DH",
    0x07 : "BH",
}

WORD_REG = {
    0x00 : "AX",
    0x01 : "CX",
    0x02 : "DX",
    0x03 : "BX",
    0x04 : "SP",
    0x05 : "BP",
    0x06 : "SI",
    0x07 : "DI",
}

SEGMENT_REG = {
    0x00 : "ES",
    0x01 : "CS",
    0x02 : "SS",
    0x03 : "DS",
}


# Functions
SIGNED_DWORD = struct.Struct("<l")
UNSIGNED_DWORD = struct.Struct("<L")
SIGNED_WORD = struct.Struct("<h")
UNSIGNED_WORD = struct.Struct("<H")
SIGNED_BYTE = struct.Struct("<b")
UNSIGNED_BYTE = struct.Struct("<B")

def signed_dword(value):
    """ Interpret an unsigned double word as a signed double word. """
    return SIGNED_DWORD.unpack(UNSIGNED_DWORD.pack(value))[0]
    
def signed_word(value):
    """ Interpret an unsigned word as a signed word. """
    return SIGNED_WORD.unpack(UNSIGNED_WORD.pack(value))[0]
    
def signed_byte(value):
    """ Interpret an unsigned byte as a signed byte. """
    return SIGNED_BYTE.unpack(UNSIGNED_BYTE.pack(value))[0]
    
def decode_seg_reg(value):
    """ Decode a segment register selector into the string register name. """
    return SEGMENT_REG[value & 0x03]
    
# Decorators
def supports_rep_prefix(func):
    """ Decorator to implement the REP prefix which repeats while CX != 0. """
    
    def _repeated(self, *args):
        """ Wrapper that implements REP. """
        if self.repeat_prefix == REPEAT_REP_REPZ:
            while self.regs.CX != 0:
                # TODO: When interrupts are supported we will need to process them here.
                self.regs.CX -= 1
                func(self, *args)
                
            # Clear the prefix so we can catch invalid combinations.
            self.repeat_prefix = REPEAT_NONE
            
        else:
            func(self, *args)
            
    return _repeated
    
def supports_repz_repnz_prefix(func):
    """ Decorator to implement the REPZ/REPNZ prefixes which repeats while CX != 0 and the zero flag is in a given state. """
    
    def _repeated(self, *args):
        """ Wrapper that implements REPZ and REPNZ. """
        if self.repeat_prefix == REPEAT_REP_REPZ:
            while self.regs.CX != 0:
                # TODO: When interrupts are supported we will need to process them here.
                self.regs.CX -= 1
                func(self, *args)
                if not self.flags.zero: # Need to test this after func() to avoid testing precondition.
                    break
                    
            # Clear the prefix so we can catch invalid combinations.
            self.repeat_prefix = REPEAT_NONE
            
        elif self.repeat_prefix == REPEAT_REPNZ:
            while self.regs.CX != 0:
                # TODO: When interrupts are supported we will need to process them here.
                self.regs.CX -= 1
                func(self, *args)
                if self.flags.zero: # Need to test this after func() to avoid testing precondition.
                    break
                    
            # Clear the prefix so we can catch invalid combinations.
            self.repeat_prefix = REPEAT_NONE
            
        else:
            func(self, *args)
            
    return _repeated

# Classes
class WordRegs(Structure):
    _fields_ = [
        ("AX", c_ushort),
        ("BX", c_ushort),
        ("CX", c_ushort),
        ("DX", c_ushort),
        ("SI", c_ushort),
        ("DI", c_ushort),
        
        # The segment registers are not part of union REGS but are here for now.
        ("ES", c_ushort),
        ("CS", c_ushort),
        ("SS", c_ushort),
        ("DS", c_ushort),
        
        # These are also not part of union REGS but they need to be in our registers.
        ("IP", c_ushort),
        ("BP", c_ushort),
        ("SP", c_ushort),
    ]
    
class ByteRegs(Structure):
    _fields_ = [
        ("AL", c_ubyte),
        ("AH", c_ubyte),
        ("BL", c_ubyte),
        ("BH", c_ubyte),
        ("CL", c_ubyte),
        ("CH", c_ubyte),
        ("DL", c_ubyte),
        ("DH", c_ubyte),
    ]
    
class UnionRegs(Union):
    _anonymous_ = ("x", "h")
    _fields_ = [
        ("x", WordRegs),
        ("h", ByteRegs),
    ]
    
    def __init__(self):
        Union.__init__(self)
        
        # These are all initialized to zero by ctypes but this is done so PyLint isn't confused.
        # pylint: disable=invalid-name
        self.AX = 0x0000
        self.AH = 0x00
        self.AL = 0x00
        
        self.BX = 0x0000
        self.BH = 0x00
        self.BL = 0x00
        
        self.CX = 0x0000
        self.CH = 0x00
        self.CL = 0x00
        
        self.DX = 0x0000
        self.DH = 0x00
        self.DL = 0x00
        
        self.SI = 0x0000
        self.DI = 0x0000
        
        self.ES = 0x0000
        self.CS = 0xFFFF # This is so we hit the reset vector at power up.
        self.SS = 0x0000
        self.DS = 0x0000
        
        self.IP = 0x0000
        self.BP = 0x0000
        self.SP = 0x0000
        # pylint: enable=invalid-name
    
    def __getitem__(self, key):
        return getattr(self, key)
        
    def __setitem__(self, key, value):
        setattr(self, key, value)
        
class FLAGS(object):
    """ 8086/8088 FLAGS register. """
    BLANK =       0x0000
    
    CARRY =       0x0001
    RESERVED_1 =  0x0002
    PARITY =      0x0004
    RESERVED_2 =  0x0008
    
    ADJUST =      0x0010
    RESERVED_3 =  0x0020
    ZERO =        0x0040
    SIGN =        0x0080
    
    TRAP =        0x0100
    INT_ENABLE =  0x0200
    DIRECTION =   0x0400
    OVERFLOW =    0x0800
    
    IOPL_0 =      0x1000
    IOPL_1 =      0x2000
    NESTED =      0x4000
    RESERVED_4 =  0x8000
    
    # These bits are always set in an 8086/8088.
    ALWAYS_ON_808x = RESERVED_4 | NESTED | IOPL_1 | IOPL_0
    
    def __init__(self):
        self.carry = False
        self.parity = False
        self.adjust = False
        self.zero = False
        self.sign = False
        self.trap = False
        self.interrupt_enable = False
        self.direction = False
        self.overflow = False
        
    def set_from_alu_word(self, value):
        """ Set ZF, SF, CF, and PF based the result of an ALU operation. """
        self.zero = not (value & 0xFFFF)
        self.sign = value & 0x8000 == 0x8000
        self.carry = value & 0x10000 == 0x10000
        self.parity = (count_bits_fast(value & 0x00FF) % 2) == 0
        
    def set_from_alu_no_carry_word(self, value):
        """ Set ZF, SF, and PF based the result of an ALU operation. """
        self.zero = not (value & 0xFFFF)
        self.sign = value & 0x8000 == 0x8000
        self.parity = (count_bits_fast(value & 0x00FF) % 2) == 0
        
    def set_from_alu_byte(self, value):
        """ Set ZF, SF, CF, and PF based the result of an ALU operation. """
        self.zero = not (value & 0xFF)
        self.sign = value & 0x80 == 0x80
        self.carry = value & 0x100 == 0x100
        self.parity = (count_bits_fast(value & 0x00FF) % 2) == 0
        
    def set_from_alu_no_carry_byte(self, value):
        """ Set ZF, SF, and PF based the result of an ALU operation. """
        self.zero = not (value & 0xFF)
        self.sign = value & 0x80 == 0x80
        self.parity = (count_bits_fast(value & 0x00FF) % 2) == 0
        
    def set_from_alu(self, value, bits = 16, carry = True):
        """ Generic wrapper for set_from_alu_*. """
        if bits == 8:
            if carry:
                self.set_from_alu_byte(value)
            else:
                self.set_from_alu_no_carry_byte(value)
        else:
            if carry:
                self.set_from_alu_word(value)
            else:
                self.set_from_alu_no_carry_word(value)
                
    def clear_logical(self):
        """ The carry and overflow flags are cleared after a logical ALU operation. """
        self.carry = self.overflow = False
        
    @property
    def value(self):
        """ Return the FLAGS register as a word value. """
        value = self.ALWAYS_ON_808x
        
        if self.carry:
            value |= self.CARRY
        if self.parity:
            value |= self.PARITY
        if self.adjust:
            value |= self.ADJUST
        if self.zero:
            value |= self.ZERO
        if self.sign:
            value |= self.SIGN
        if self.trap:
            value |= self.TRAP
        if self.interrupt_enable:
            value |= self.INT_ENABLE
        if self.direction:
            value |= self.DIRECTION
        if self.overflow:
            value |= self.OVERFLOW
        
        return value
        
    @value.setter
    def value(self, value):
        """ Set the FLAGS register from a word value. """
        self.carry = bool(value & self.CARRY)
        self.parity = bool(value & self.PARITY)
        self.adjust = bool(value & self.ADJUST)
        self.zero = bool(value & self.ZERO)
        self.sign = bool(value & self.SIGN)
        self.trap = bool(value & self.TRAP)
        self.interrupt_enable = bool(value & self.INT_ENABLE)
        self.direction = bool(value & self.DIRECTION)
        self.overflow = bool(value & self.OVERFLOW)
        
class CPU(object):
    def __init__(self):
        # System bus for memory and I/O access.
        self.bus = None
        
        # CPU halt flag.
        self.hlt = False
        
        # Flags register.
        self.flags = FLAGS()
        
        # Normal registers.
        self.regs = UnionRegs()
        
        # ALU vector table.
        self.alu_vector_table = {
            0x00 : self._alu_rm8_r8,
            0x01 : self._alu_rm16_r16,
            0x02 : self._alu_r8_rm8,
            0x03 : self._alu_r16_rm16,
            0x04 : self._alu_al_imm8,
            0x05 : self._alu_ax_imm16,
        }
        
        # Prefix flags.
        self.repeat_prefix = REPEAT_NONE
        self.segment_override = None
        
        # Fast instruction decoding.
        self.opcode_vector = [
            # 0x00 - 0x0F
            self.opcode_group_add,
            self.opcode_group_add,
            self.opcode_group_add,
            self.opcode_group_add,
            self.opcode_group_add,
            self.opcode_group_add,
            lambda _opcode: self.internal_push(self.regs.ES),
            lambda _opcode: operator.setitem(self.regs, "ES", self.internal_pop()),
            self.opcode_group_or,
            self.opcode_group_or,
            self.opcode_group_or,
            self.opcode_group_or,
            self.opcode_group_or,
            self.opcode_group_or,
            lambda _opcode: self.internal_push(self.regs.CS),
            self.signal_invalid_opcode, # There is no POP CS (0x0F is used for two-byte opcodes in 286+).
            
            # 0x10 - 0x1F
            self.opcode_group_adc,
            self.opcode_group_adc,
            self.opcode_group_adc,
            self.opcode_group_adc,
            self.opcode_group_adc,
            self.opcode_group_adc,
            lambda _opcode: self.internal_push(self.regs.SS),
            lambda _opcode: operator.setitem(self.regs, "SS", self.internal_pop()),
            self.opcode_group_sbb,
            self.opcode_group_sbb,
            self.opcode_group_sbb,
            self.opcode_group_sbb,
            self.opcode_group_sbb,
            self.opcode_group_sbb,
            lambda _opcode: self.internal_push(self.regs.DS),
            lambda _opcode: operator.setitem(self.regs, "DS", self.internal_pop()), 
            
            # 0x20 - 0x2F
            self.opcode_group_and,
            self.opcode_group_and,
            self.opcode_group_and,
            self.opcode_group_and,
            self.opcode_group_and,
            self.opcode_group_and,
            None, # ES segment override prefix.
            None, # TODO: Implement DAA.
            self.opcode_group_sub,
            self.opcode_group_sub,
            self.opcode_group_sub,
            self.opcode_group_sub,
            self.opcode_group_sub,
            self.opcode_group_sub,
            None, # CS segment override prefix.
            None, # TODO: Implement DAS.
            
            # 0x30 - 0x3F
            self.opcode_group_xor,
            self.opcode_group_xor,
            self.opcode_group_xor,
            self.opcode_group_xor,
            self.opcode_group_xor,
            self.opcode_group_xor,
            None, # SS segment override prefix.
            None, # TODO: Implement AAA.
            self.opcode_cmp_rm8_r8,
            self.opcode_cmp_rm16_r16,
            self.opcode_cmp_r8_rm8,
            self.opcode_cmp_r16_rm16,
            self.opcode_cmp_al_imm8,
            self.opcode_cmp_ax_imm16,
            None, # DS segment override prefix.
            None, # TODO: Implement AAS.
            
            # 0x40 - 0x4F
            self.opcode_group_inc,
            self.opcode_group_inc,
            self.opcode_group_inc,
            self.opcode_group_inc,
            self.opcode_group_inc,
            self.opcode_group_inc,
            self.opcode_group_inc,
            self.opcode_group_inc,
            self.opcode_group_dec,
            self.opcode_group_dec,
            self.opcode_group_dec,
            self.opcode_group_dec,
            self.opcode_group_dec,
            self.opcode_group_dec,
            self.opcode_group_dec,
            self.opcode_group_dec,
            
            # 0x50 - 0x5F
            self.opcode_group_push,
            self.opcode_group_push,
            self.opcode_group_push,
            self.opcode_group_push,
            self.opcode_push_sp,
            self.opcode_group_push,
            self.opcode_group_push,
            self.opcode_group_push,
            self.opcode_group_pop,
            self.opcode_group_pop,
            self.opcode_group_pop,
            self.opcode_group_pop,
            self.opcode_pop_sp,
            self.opcode_group_pop,
            self.opcode_group_pop,
            self.opcode_group_pop,
            
            # 0x60 - 0x6F (All invalid on 808x).
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            self.signal_invalid_opcode,
            
            # 0x70 - 0x7F
            self.opcode_jo,
            self.opcode_jno,
            self.opcode_jc,
            self.opcode_jnc,
            self.opcode_jz,
            self.opcode_jnz,
            self.opcode_jna,
            self.opcode_ja,
            self.opcode_js,
            self.opcode_jns,
            self.opcode_jp,
            self.opcode_jnp,
            self.opcode_jl,
            self.opcode_jnl,
            self.opcode_jle,
            self.opcode_jnle,
        ]
        
        while len(self.opcode_vector) < 256:
            self.opcode_vector.append(None)
            
        # Set the default LOOP opcode handler.
        # TODO: This can be removed when LOOP is moved to the fancy new vector table.
        self.opcode_loop = self.opcode_loop_no_shortcuts
        
    def install_bus(self, bus):
        """ Register the bus with the CPU. """
        self.bus = bus
        self.mem_read_byte = self.bus.mem_read_byte
        
    def read_instruction_byte(self):
        """ Read a byte from CS:IP and increment IP to point at the next instruction. """
        address = segment_offset_to_address(self.regs.CS, self.regs.IP)
        self.regs.IP += 1
        return self.mem_read_byte(address)
        
    def fetch(self):
        """ Fetch and execute one instruction. """
        # Process any pending interrupts, including trap/single-step.
        self.process_interrupts()
        
        # Clear all prefixes.
        self.repeat_prefix = REPEAT_NONE
        self.segment_override = None
        
        # We could have multiple prefixes.
        # TODO: There is probably a better way to do this than `while True'.
        while True:
            # Fetch an opcode or prefix.
            opcode = self.read_instruction_byte()
            
            # Configure flags based on the prefix.
            if opcode == 0xF3:
                self.repeat_prefix = REPEAT_REP_REPZ
            elif opcode == 0xF2:
                self.repeat_prefix = REPEAT_REPNZ
            elif opcode == 0x26:
                self.segment_override = "ES"
            elif opcode == 0x2E:
                self.segment_override = "CS"
            elif opcode == 0x36:
                self.segment_override = "SS"
            elif opcode == 0x3E:
                self.segment_override = "DS"
            else:
                break
                
        # First check if the opcode is in the instruction decoding table.
        opcode_handler = self.opcode_vector[opcode]
        if opcode_handler is not None:
            opcode_handler(opcode)
            
            # HACK: Remove this and the return when all instructions are converted.
            if self.repeat_prefix != REPEAT_NONE:
                self.signal_invalid_opcode(opcode, "Opcode doesn't support repeat prefix.")
            
            return
            
        if opcode == 0xF4:
            self._hlt()
        elif opcode & 0xFC == 0x80:
            self.opcode_group_8x(opcode)
        elif opcode & 0xF8 == 0x90:
            self._xchg_r16_ax(opcode)
        elif opcode & 0xFE == 0xF6:
            self.opcode_group_f6f7(opcode)
        elif opcode == 0xE0:
            self.opcode_loopnz()
        elif opcode == 0xE1:
            self.opcode_loopz()
        elif opcode == 0xE2:
            self.opcode_loop()
        elif opcode == 0xE8:
            self.opcode_call_rel16()
        elif opcode == 0xC2:
            self.opcode_ret_imm16()
        elif opcode == 0xC3:
            self.opcode_ret()
        elif opcode == 0xCA:
            self.opcode_retf_imm16()
        elif opcode == 0xCB:
            self.opcode_retf()
            
        # Interrupt instructions.
        elif opcode == 0xCD:
            self.opcode_int()
        elif opcode == 0xCF:
            self.opcode_iret()
            
        # MOV instructions.
        elif opcode & 0xF0 == 0xB0:
            self._mov_imm_to_reg(opcode)
        elif opcode == 0x8B:
            self._mov_r16_rm16()
        elif opcode == 0x88:
            self._mov_rm8_r8()
        elif opcode == 0x89:
            self._mov_reg16_to_rm16() # BAD NAME
        elif opcode == 0x8A:
            self.opcode_mov_r8_rm8()
        elif opcode == 0xC6:
            self._mov_rm8_imm8()
        elif opcode == 0xC7:
            self._mov_rm16_imm16()
        elif opcode == 0x8E:
            self._mov_sreg_rm16()
        elif opcode == 0x8C:
            self._mov_rm16_sreg()
        elif opcode == 0xA0:
            self.opcode_mov_al_moffs8()
        elif opcode == 0xA1:
            self.opcode_mov_ax_moffs16()
        elif opcode == 0xA2:
            self.opcode_mov_moffs8_al()
        elif opcode == 0xA3:
            self.opcode_mov_moffs16_ax()
            
        elif opcode == 0xE3:
            self.opcode_jcxz()
            
        # FLAGS set/clear instructions.
        elif opcode == 0xF8:
            self.opcode_clc()
        elif opcode == 0xF9:
            self.opcode_stc()
        elif opcode == 0xF5:
            self.opcode_cmc()
        elif opcode == 0xFC:
            self.opcode_cld()
        elif opcode == 0xFD:
            self.opcode_std()
        elif opcode == 0xFA:
            self.opcode_cli()
        elif opcode == 0xFB:
            self.opcode_sti()
            
        elif opcode == 0x90:
            self._nop()
        elif opcode == 0xE9:
            self._jmp_rel16()
        elif opcode == 0xEB:
            self._jmp_rel8()
        elif opcode == 0x86:
            self.opcode_xchg_r8_rm8()
        elif opcode == 0x87:
            self.opcode_xchg_r16_rm16()
        elif opcode == 0xFE:
            self.opcode_group_fe()
        elif opcode == 0xFF:
            self.opcode_group_ff()
        elif opcode == 0xEA:
            self._jmpf()
        elif opcode == 0x9A:
            self.opcode_callf()
            
        # Flags opcodes.
        elif opcode == 0x9E:
            self.opcode_sahf()
        elif opcode == 0x9F:
            self.opcode_lahf()
        elif opcode == 0x9C:
            self.opcode_pushf()
        elif opcode == 0x9D:
            self.opcode_popf()
            
        elif opcode & 0xFC == 0xD0:
            self.opcode_group_rotate_and_shift(opcode)
        elif opcode == 0xE4:
            self.opcode_in_al_imm8()
        elif opcode == 0xEC:
            self.opcode_in_al_dx()
        elif opcode == 0xE6:
            self._out_imm8_al()
        elif opcode == 0xEE:
            self._out_dx_al()
        elif opcode == 0xA8:
            self.opcode_test_al_imm8()
        elif opcode == 0xA9:
            self.opcode_test_ax_imm16()
        elif opcode == 0x84:
            self.opcode_test_rm8_r8()
        elif opcode == 0x85:
            self.opcode_test_rm16_r16()
        elif opcode == 0xC4:
            self.opcode_les()
        elif opcode == 0xC5:
            self.opcode_lds()
        elif opcode == 0x8D:
            self.opcode_lea()
        elif opcode == 0x98:
            self.opcode_cbw()
        elif opcode == 0x99:
            self.opcode_cwd()
        elif opcode == 0xD7:
            self.opcode_xlat()
            
        # String operations.
        elif opcode == 0xA4:
            self.opcode_movsb()
        elif opcode == 0xA5:
            self.opcode_movsw()
        elif opcode == 0xAA:
            self.opcode_stosb()
        elif opcode == 0xAB:
            self.opcode_stosw()
        elif opcode == 0xAC:
            self.opcode_lodsb()
        elif opcode == 0xAD:
            self.opcode_lodsw()
        elif opcode == 0xAE:
            self.opcode_scasb()
        elif opcode == 0xAF:
            self.opcode_scasw()
        elif opcode == 0xA6:
            self.opcode_cmpsb()
            
        elif opcode == 0x8F:
            self.opcode_pop_rm16()
            
        # ESCape opcodes (used to allow 8087 to access the bus).
        # These decode a ModRM field but we toss it for now because we don't have an 8087.
        elif opcode & 0xF8 == 0xD8:
            _sub_opcode, _rm_type, _rm_value = self.get_modrm_operands(16, decode_register = False)
            
        else:
            self.signal_invalid_opcode(opcode, "Opcode not implemented.")
            
        # The REP* prefixes will clear this after execution.  If it is still set at this point
        # it means that someone tried to REP an instruction that doesn't support it.
        if self.repeat_prefix != REPEAT_NONE:
            self.signal_invalid_opcode(opcode, "Opcode doesn't support repeat prefix.")
            
    def signal_invalid_opcode(self, opcode, message = None):
        """ Invalid opcode handler. """
        log.error("Invalid opcode: 0x%02x at CS:IP %04x:%04x", opcode, self.regs.CS, self.regs.IP)
        if self.repeat_prefix != REPEAT_NONE:
            log.error("Repeat prefix was: 0x%02x", self.repeat_prefix)
        if message is not None:
            log.error(message)
            
        # Throw an unhandled exception so we print the register contents.
        raise InvalidOpcodeException(opcode, self.regs.CS, self.regs.IP)
        
    # ********** Opcode parameter helpers. **********
    def get_modrm_operands(self, size, decode_register = True):
        """
        Returns register, rm_type, rm_value from a MODRM byte.
        
        See: https://en.wikibooks.org/wiki/X86_Assembly/Machine_Language_Conversion
        """
        register = None
        rm_type = UNKNOWN
        rm_value = None
        
        # Get the mod r/m byte and decode it.
        modrm = self.read_instruction_byte()
        
        mod = (modrm & MOD_MASK) >> MOD_SHIFT
        reg = (modrm & REG_MASK) >> REG_SHIFT
        rm = modrm & RM_MASK
        
        if decode_register:
            if size == 8:
                register = BYTE_REG[reg]
            elif size == 16:
                register = WORD_REG[reg]
        else:
            register = reg
            
        # Mod 00, 01, 10 - r/m is address (calculated base + displacement).
        if mod in (0x00, 0x01, 0x02):
            rm_type = ADDRESS
            
            # Determine the calculated base.
            if rm == 0x00:
                rm_value = self.regs.BX + self.regs.SI
            elif rm == 0x01:
                rm_value = self.regs.BX + self.regs.DI
            elif rm == 0x02:
                rm_value = self.regs.BP + self.regs.SI
                if self.segment_override is None:
                    self.segment_override = "SS"
            elif rm == 0x03:
                rm_value = self.regs.BP + self.regs.DI
                if self.segment_override is None:
                    self.segment_override = "SS"
            elif rm == 0x04:
                rm_value = self.regs.SI
            elif rm == 0x05:
                rm_value = self.regs.DI
            elif rm == 0x06:
                # Mod 00 / r/m 110 is absolute address.
                if mod == 0x00:
                    rm_value = self.get_word_immediate()
                else:
                    rm_value = self.regs.BP
                    if self.segment_override is None:
                        self.segment_override = "SS"
            elif rm == 0x07:
                rm_value = self.regs.BX
                
            # Determine the displacement.
            displacement = 0
            if mod == 0x01:
                displacement = sign_extend_byte_to_word(self.get_byte_immediate())
            elif mod == 0x02:
                displacement = self.get_word_immediate()
            
            # Negative displacements do two's complement math, we need to mask this to 16 bits for it to work.
            rm_value = (rm_value + displacement) & 0xFFFF
            
        # Mod 11 - r/m is a second register field.
        elif mod == 0x03:
            rm_type = REGISTER
            if size == 8:
                rm_value = BYTE_REG[rm]
            elif size == 16:
                rm_value = WORD_REG[rm]
                
        # Sanity checks.
        assert register is not None
        assert rm_type != UNKNOWN
        assert rm_value is not None
        
        # log_line = "reg = %s, " % register
        # if rm_type == REGISTER:
            # log_line += "r/m = %s" % rm_value
        # elif rm_type == ADDRESS:
            # log_line += "r/m = 0x%04x" % rm_value
        # log.debug(log_line)
            
        return register, rm_type, rm_value
        
    def get_immediate(self, word):
        """ Get either a byte or word immediate value from CS:IP. """
        if word:
            return self.get_word_immediate()
        else:
            return self.get_byte_immediate()
        
    def get_word_immediate(self):
        """ Get a word immediate value from CS:IP. """
        value = self.read_instruction_byte()
        value |= (self.read_instruction_byte() << 8)
        return value
        
    # Get a byte immediate value from CS:IP.
    get_byte_immediate = read_instruction_byte
    
    # ********** Data movement opcodes. **********
    def _mov_imm_to_reg(self, opcode):
        word = opcode & 0x08
        if word:
            dest = WORD_REG[opcode & 0x07]
        else:
            dest = BYTE_REG[opcode & 0x07]
            
        value = self.get_immediate(word)
        self.regs[dest] = value
        
    def _mov_r16_rm16(self):
        register, rm_type, rm_value = self.get_modrm_operands(16)
        self.regs[register] = self._get_rm16(rm_type, rm_value)
        
    def _mov_rm8_r8(self):
        register, rm_type, rm_value = self.get_modrm_operands(8)
        self._set_rm8(rm_type, rm_value, self.regs[register])
        
    def opcode_mov_r8_rm8(self):
        register, rm_type, rm_value = self.get_modrm_operands(8)
        self.regs[register] = self._get_rm8(rm_type, rm_value)
        
    def _mov_reg16_to_rm16(self):
        register, rm_type, rm_value = self.get_modrm_operands(16)
        self._set_rm16(rm_type, rm_value, self.regs[register])
        
    def _mov_rm8_imm8(self):
        sub_opcode, rm_type, rm_value = self.get_modrm_operands(8, decode_register = False)
        assert sub_opcode == 0
        self._set_rm8(rm_type, rm_value, self.get_byte_immediate())
        
    def _mov_rm16_imm16(self):
        sub_opcode, rm_type, rm_value = self.get_modrm_operands(16, decode_register = False)
        assert sub_opcode == 0
        self._set_rm16(rm_type, rm_value, self.get_word_immediate())
        
    def _mov_sreg_rm16(self):
        segment_register, rm_type, rm_value = self.get_modrm_operands(16, decode_register = False)
        self.regs[decode_seg_reg(segment_register)] = self._get_rm16(rm_type, rm_value)
        
    def _mov_rm16_sreg(self):
        segment_register, rm_type, rm_value = self.get_modrm_operands(16, decode_register = False)
        self._set_rm16(rm_type, rm_value, self.regs[decode_seg_reg(segment_register)])
        
    def opcode_mov_al_moffs8(self):
        """ Load a byte from DS:offset into AL. """
        self.regs.AL = self.read_data_byte(self.get_word_immediate())
        
    def opcode_mov_ax_moffs16(self):
        """ Load a word from DS:offset into AX. """
        self.regs.AX = self.read_data_word(self.get_word_immediate())
        
    def opcode_mov_moffs8_al(self):
        """ Load a byte from AL into DS:offset. """
        self.write_data_byte(self.get_word_immediate(), self.regs.AL)
        
    def opcode_mov_moffs16_ax(self):
        """ Load a word from AX into DS:offset. """
        self.write_data_word(self.get_word_immediate(), self.regs.AX)
        
    def opcode_xchg_r8_rm8(self):
        """ Swap the contents of a byte register and memory location. """
        register, rm_type, rm_value = self.get_modrm_operands(8)
        temp = self._get_rm8(rm_type, rm_value)
        self._set_rm8(rm_type, rm_value, self.regs[register])
        self.regs[register] = temp
        
    def opcode_xchg_r16_rm16(self):
        """ Swap the contents of a word register and memory location. """
        register, rm_type, rm_value = self.get_modrm_operands(16)
        temp = self._get_rm16(rm_type, rm_value)
        self._set_rm16(rm_type, rm_value, self.regs[register])
        self.regs[register] = temp
        
    def _xchg_r16_ax(self, opcode):
        dest = WORD_REG[opcode & 0x07]
        temp = self.regs[dest]
        self.regs[dest] = self.regs.AX
        self.regs.AX = temp
        
    def opcode_les(self):
        """ Load ES:r16 with the far pointer from r/m16. """
        register, rm_type, rm_value = self.get_modrm_operands(16)
        assert rm_type == ADDRESS
        
        offset = self._get_rm16(rm_type, rm_value)
        segment = self._get_rm16(rm_type, rm_value + 2)
        
        self.regs[register] = offset
        self.regs.ES = segment
        
    def opcode_lds(self):
        """ Load DS:r16 with the far pointer from r/m16. """
        register, rm_type, rm_value = self.get_modrm_operands(16)
        assert rm_type == ADDRESS
        
        offset = self._get_rm16(rm_type, rm_value)
        segment = self._get_rm16(rm_type, rm_value + 2)
        
        self.regs[register] = offset
        self.regs.DS = segment
        
    def opcode_lea(self):
        """ Load the destination register with the offset from r/m16. """
        register, rm_type, rm_value = self.get_modrm_operands(16)
        assert rm_type == ADDRESS
        
        self.regs[register] = rm_value
        
    # ********** Stack opcodes. **********
    def opcode_group_push(self, opcode):
        """ Handler for all PUSH [register] instructions. """
        src = WORD_REG[opcode & 0x07]
        value = self.regs[src]
        self.internal_push(value)
        
    def opcode_group_pop(self, opcode):
        """ Handler for all POP [register] instructions. """
        dest = WORD_REG[opcode & 0x07]
        self.regs[dest] = self.internal_pop()
        
    def opcode_pop_rm16(self):
        """ Pop a word off of the stack and store it in an r/m16 destination. """
        register, rm_type, rm_value = self.get_modrm_operands(16)
        self._set_rm16(rm_type, rm_value, self.internal_pop())
        
    def opcode_push_sp(self, opcode):
        """
        Special handler for PUSH SP on 8086/8088.
        
        On 808x this pushes the new SP value, on 286+ this pushes the old SP value.
        """
        self.regs.SP -= 2
        self.bus.mem_write_word(segment_offset_to_address(self.regs.SS, self.regs.SP), self.regs.SP)
        
    def opcode_pop_sp(self, opcode):
        """
        Special handler for POP SP.
        
        This needs to assign the top of the stack to SP, then increment it by 2.
        """
        self.regs.SP = self.bus.mem_read_word(segment_offset_to_address(self.regs.SS, self.regs.SP))
        self.regs.SP += 2
        
    def internal_push(self, value):
        """ Decrement the stack pointer and push a word on to the stack. """
        self.regs.SP -= 2
        self.bus.mem_write_word(segment_offset_to_address(self.regs.SS, self.regs.SP), value)
        
    def internal_pop(self):
        """ Pop a word off of the stack and incrementt the stack pointer. """
        value = self.bus.mem_read_word(segment_offset_to_address(self.regs.SS, self.regs.SP))
        self.regs.SP += 2
        return value
        
    # ********** Conditional jump opcodes. **********
    def opcode_jc(self, _opcode):
        """ JC/JNAE/JB - Jump short if the carry flag is set. """
        distance = self.get_byte_immediate()
        if self.flags.carry:
            self.regs.IP += signed_byte(distance)
            
    def opcode_jz(self, _opcode):
        """ JZ/JE - Jump short if the zero flag is set. """
        distance = self.get_byte_immediate()
        if self.flags.zero:
            self.regs.IP += signed_byte(distance)
            
    def opcode_jnz(self, _opcode):
        """ JNZ/JNE - Jump short if the zero flag is clear. """
        distance = self.get_byte_immediate()
        if not self.flags.zero:
            self.regs.IP += signed_byte(distance)
            
    def opcode_jna(self, _opcode):
        """ JNA/JBE - Jump short if zero or carry are set. """
        distance = self.get_byte_immediate()
        if self.flags.zero or self.flags.carry:
            self.regs.IP += signed_byte(distance)
            
    def opcode_ja(self, _opcode):
        """ JA/JNBE - Jump short if both zero and carry are clear. """
        distance = self.get_byte_immediate()
        if not self.flags.zero and not self.flags.carry:
            self.regs.IP += signed_byte(distance)
            
    def opcode_jnc(self, _opcode):
        """ JNC/JAE/JNB - Jump short if the carry flag is clear. """
        distance = self.get_byte_immediate()
        if not self.flags.carry:
            self.regs.IP += signed_byte(distance)
            
    def opcode_jnp(self, _opcode):
        """ JNP/JPO - Jump short if the parity flag is clear (odd parity). """
        distance = self.get_byte_immediate()
        if not self.flags.parity:
            self.regs.IP += signed_byte(distance)
            
    def opcode_jp(self, _opcode):
        """ JP/JPE - Jump short if the parity flag is set (even parity). """
        distance = self.get_byte_immediate()
        if self.flags.parity:
            self.regs.IP += signed_byte(distance)
            
    def opcode_jns(self, _opcode):
        """ JNS - Jump short if the sign flag is clear. """
        distance = self.get_byte_immediate()
        if not self.flags.sign:
            self.regs.IP += signed_byte(distance)
            
    def opcode_js(self, _opcode):
        """ JS - Jump short if the sign flag is set. """
        distance = self.get_byte_immediate()
        if self.flags.sign:
            self.regs.IP += signed_byte(distance)
            
    def opcode_jno(self, _opcode):
        """ Jump short if the overflow flag is clear. """
        distance = self.get_byte_immediate()
        if not self.flags.overflow:
            self.regs.IP += signed_byte(distance)
            
    def opcode_jo(self, _opcode):
        """ Jump short if the overflow flag is set. """
        distance = self.get_byte_immediate()
        if self.flags.overflow:
            self.regs.IP += signed_byte(distance)
            
    def opcode_jl(self, _opcode):
        """ JL/JNGE - Jump short if the sign flag is not equal to the overflow flag. """
        distance = self.get_byte_immediate()
        if self.flags.sign != self.flags.overflow:
            self.regs.IP += signed_byte(distance)
            
    def opcode_jnl(self, _opcode):
        """ JNL/JGE - Jump short if the sign flag is equal to the overflow flag. """
        distance = self.get_byte_immediate()
        if self.flags.sign == self.flags.overflow:
            self.regs.IP += signed_byte(distance)
            
    def opcode_jle(self, _opcode):
        """ JLE/JNG - Jump short if the sign flag is not equal to the overflow flag or the zero flag is set. """
        distance = self.get_byte_immediate()
        if self.flags.zero or (self.flags.sign != self.flags.overflow):
            self.regs.IP += signed_byte(distance)
            
    def opcode_jnle(self, _opcode):
        """ JNLE/JG - Jump short if the sign flag equals the overflow flag and the zero flag is clear. """
        distance = self.get_byte_immediate()
        if not self.flags.zero and (self.flags.sign == self.flags.overflow):
            self.regs.IP += signed_byte(distance)
            
    def opcode_jcxz(self):
        """ Jump short if the CX register == 0. """
        distance = self.get_byte_immediate()
        if self.regs.CX == 0:
            self.regs.IP += signed_byte(distance)
            
    # ********** Interrupt opcodes. **********
    def opcode_int(self):
        """ Jump to the specified interrupt vector (imm8). """
        self.internal_service_interrupt(self.get_byte_immediate())
        
    def opcode_iret(self):
        """ Return from interrupt, restoring IP, CS, and FLAGS. """
        self.regs.IP = self.internal_pop()
        self.regs.CS = self.internal_pop()
        self.flags.value = self.internal_pop()
        
    def process_interrupts(self):
        """ Process non-software interrupts. """
        if self.flags.interrupt_enable and self.bus.pic and self.bus.pic.interrupt_pending():
            interrupt = self.bus.pic.pop_interrupt_vector()
            log.debug("External interrupt requested INT %02xh.", interrupt)
            self.internal_service_interrupt(interrupt)
            
    def internal_service_interrupt(self, interrupt):
        """ Jump to the specified interrupt vector, saving FLAGS, CS, and IP. """
        self.internal_push(self.flags.value)
        self.flags.trap = False
        self.flags.interrupt_enable = False
        self.internal_push(self.regs.CS)
        self.regs.CS = self.bus.mem_read_word((interrupt * 4) + 2)
        self.internal_push(self.regs.IP)
        self.regs.IP = self.bus.mem_read_word(interrupt * 4)
        log.debug("INT %02xh to CS:IP %04x:%04x", interrupt, self.regs.CS, self.regs.IP)
        
    # ********** Fancy jump opcodes. **********
    def _jmpf(self):
        # This may look silly, but you can't modify IP or CS while reading the JUMP FAR parameters.
        new_ip = self.get_word_immediate()
        new_cs = self.get_word_immediate()
        self.regs.IP = new_ip
        self.regs.CS = new_cs
        log.debug("JMP FAR to CS: 0x%04x  IP:0x%04x", self.regs.CS, self.regs.IP)
        
    def opcode_callf(self):
        """ Calls a far function from the parameters given in the instruction. """
        new_ip = self.get_word_immediate()
        new_cs = self.get_word_immediate()
        self.internal_push(self.regs.CS)
        self.internal_push(self.regs.IP)
        self.regs.IP = new_ip
        self.regs.CS = new_cs
        log.debug("CALL FAR to CS:IP %04x:%04x", self.regs.CS, self.regs.IP)
        
    def opcode_call_rel16(self):
        """ Calls a near function at a location relative to the current IP. """
        offset = signed_word(self.get_word_immediate())
        self.internal_push(self.regs.IP)
        self.regs.IP += offset
        # log.debug("CALL incremented IP by 0x%04x to 0x%04x", offset, self.regs.IP)
        
    def opcode_ret(self):
        """ RET - Near return, pops IP. """
        self.regs.IP = self.internal_pop()
        
    def opcode_ret_imm16(self):
        """ RET - Near return, pops IP and adds imm16 to SP. """
        adjustment = self.get_word_immediate()
        self.regs.IP = self.internal_pop()
        self.regs.SP += adjustment
        
    def opcode_retf(self):
        """ RETF - Far return, pops IP and CS. """
        new_ip = self.internal_pop()
        new_cs = self.internal_pop()
        self.regs.IP = new_ip
        self.regs.CS = new_cs
        
    def opcode_retf_imm16(self):
        """ RETF - Far return, pops IP and CS and adds imm16 to SP. """
        adjustment = self.get_word_immediate()
        new_ip = self.internal_pop()
        new_cs = self.internal_pop()
        self.regs.IP = new_ip
        self.regs.CS = new_cs
        self.regs.SP += adjustment
        
    def opcode_loop_no_shortcuts(self):
        """
        LOOP - Decrement CX and jump short if it is non-zero.
        
        This version does not optimize away delay loops.
        """
        distance = self.get_byte_immediate()
        
        value = self.regs.CX - 1
        self.regs.CX = value
        
        if value != 0:
            self.regs.IP += signed_byte(distance)
            
    def opcode_loop_collapse_delay_loops(self):
        """
        LOOP - Decrement CX and jump short if it is non-zero.
        
        In this version if the distance is 0xFE (-2) meaning that it will just jump back to this instruction
        it will set CX to zero and jump out immediately.  This may cause issues for applications that are waiting
        for a DMA or timer operation to occur during a delay loop.
        """
        distance = self.get_byte_immediate()
        
        value = self.regs.CX - 1
        self.regs.CX = value
        
        if value != 0 and distance != 0xFE: # Skip delay loops that only jump back to this instruction.
            self.regs.IP += signed_byte(distance)
        elif distance == 0xFE:
            self.regs.CX = 0
            
    def collapse_delay_loops(self, value):
        """ API to enable/disable LOOP instruction optimizations. """
        if value:
            self.opcode_loop = self.opcode_loop_collapse_delay_loops
        else:
            self.opcode_loop = self.opcode_loop_no_shortcuts
        
    def opcode_loopz(self):
        """ LOOPZ/LOOPE - Decrement CX and jump short if it is non-zero and the zero flag is set. """
        distance = self.get_byte_immediate()
        
        value = self.regs.CX - 1
        self.regs.CX = value
        
        if value != 0 and self.flags.zero:
            self.regs.IP += signed_byte(distance)
            
    def opcode_loopnz(self):
        """ LOOPNZ/LOOPNE - Decrement CX and jump short if it is non-zero and the zero flag is clear. """
        distance = self.get_byte_immediate()
        
        value = self.regs.CX - 1
        self.regs.CX = value
        
        if value != 0 and self.flags.zero is False:
            self.regs.IP += signed_byte(distance)
            
    # ********** Arithmetic opcodes. **********
    def opcode_group_8x(self, opcode):
        """ Handler for immediate ALU instructions. """
        if opcode == 0x82:
            opcode = 0x80
            
        word_reg = opcode & 0x01
        word_imm = opcode == 0x81
        sign_extend = opcode & 0x02
        
        sub_opcode, rm_type, rm_value = self.get_modrm_operands(16 if word_reg else 8, decode_register = False)
        if word_reg:
            value = self._get_rm16(rm_type, rm_value)
        else:
            value = self._get_rm8(rm_type, rm_value)
            
        # Process the immediate.
        immediate = self.get_immediate(word_imm)
        if sign_extend and not word_imm:
            immediate = sign_extend_byte_to_word(immediate)
            
        set_value = True
        logical = False
        if sub_opcode == 0x00:
            result = value + immediate
        elif sub_opcode == 0x01:
            result = value | immediate
            logical = True
        elif sub_opcode == 0x02:
            result = value + immediate + (1 if self.flags.carry else 0)
        elif sub_opcode == 0x03:
            if word_reg:
                result = self.operator_sbb_16(value, immediate)
            else:
                result = self.operator_sbb_8(value, immediate)
        elif sub_opcode == 0x04:
            result = value & immediate
            logical = True
        elif sub_opcode == 0x05:
            result = value - immediate
        elif sub_opcode == 0x06:
            result = value ^ immediate
            logical = True
        elif sub_opcode == 0x07:
            if word_reg:
                result = self.operator_sub_16(value, immediate)
            else:
                result = self.operator_sub_8(value, immediate)
            set_value = False
        else:
            raise NotImplementedError("sub_opcode = %r" % sub_opcode)
            
        if word_reg:
            self.flags.set_from_alu_word(result)
            if set_value:
                self._set_rm16(rm_type, rm_value, result)
        else:
            self.flags.set_from_alu_byte(result)
            if set_value:
                self._set_rm8(rm_type, rm_value, result)
            
        if logical:
            self.flags.clear_logical()
            
    # Bitwise opcodes.
    def opcode_group_or(self, opcode):
        """ Entry point for all OR opcodes. """
        self.alu_vector_table[opcode & 0x07](operator.or_)
        self.flags.clear_logical()
        
    def opcode_group_and(self, opcode):
        """ Entry point for all AND opcodes. """
        self.alu_vector_table[opcode & 0x07](operator.and_)
        self.flags.clear_logical()
        
    def opcode_group_xor(self, opcode):
        """ Entry point for all XOR opcodes. """
        self.alu_vector_table[opcode & 0x07](operator.xor)
        self.flags.clear_logical()
        
    def opcode_test_al_imm8(self):
        """ AND al with imm8, update the flags, but don't store the value. """
        value = self.regs.AL & self.get_byte_immediate()
        self.flags.set_from_alu_byte(value)
        
    def opcode_test_ax_imm16(self):
        """ AND ax with imm16, update the flags, but don't store the value. """
        value = self.regs.AX & self.get_word_immediate()
        self.flags.set_from_alu_word(value)
        self.flags.clear_logical()
        
    def opcode_test_rm8_r8(self):
        """ AND an r/m8 value and a register value, update the flags, but don't store the value. """
        register, rm_type, rm_value = self.get_modrm_operands(8)
        value = self._get_rm8(rm_type, rm_value) & self.regs[register]
        self.flags.set_from_alu_no_carry_byte(value)
        self.flags.clear_logical()
        
    def opcode_test_rm16_r16(self):
        """ AND an r/m16 value and a register value, update the flags, but don't store the value. """
        register, rm_type, rm_value = self.get_modrm_operands(16)
        value = self._get_rm16(rm_type, rm_value) & self.regs[register]
        self.flags.set_from_alu_no_carry_word(value)
        self.flags.clear_logical()
        
    # Generic ALU helper functions.
    def _alu_rm8_r8(self, operation):
        """ Generic r/m8 r8 ALU processor. """
        register, rm_type, rm_value = self.get_modrm_operands(8)
        op1 = self._get_rm8(rm_type, rm_value)
        op2 = self.regs[register]
        op1 = operation(op1, op2)
        self.flags.set_from_alu_byte(op1)
        self._set_rm8(rm_type, rm_value, op1 & 0xFF)
        
    def _alu_rm16_r16(self, operation):
        """ Generic r/m16 r16 ALU processor. """
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self._get_rm16(rm_type, rm_value)
        op2 = self.regs[register]
        op1 = operation(op1, op2)
        self.flags.set_from_alu_word(op1)
        self._set_rm16(rm_type, rm_value, op1 & 0xFFFF)
        
    def _alu_r8_rm8(self, operation):
        """ Generic r8 r/m8 ALU processor. """
        register, rm_type, rm_value = self.get_modrm_operands(8)
        op1 = self.regs[register]
        op2 = self._get_rm8(rm_type, rm_value)
        op1 = operation(op1, op2)
        self.flags.set_from_alu_byte(op1)
        self.regs[register] = op1 & 0xFF
        
    def _alu_r16_rm16(self, operation):
        """ Generic r16 r/m16 ALU processor. """
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self.regs[register]
        op2 = self._get_rm16(rm_type, rm_value)
        op1 = operation(op1, op2)
        self.flags.set_from_alu_word(op1)
        self.regs[register] = op1 & 0xFFFF
        
    def _alu_al_imm8(self, operation):
        """ Generic al imm8 ALU processor. """
        value = operation(self.regs.AL, self.get_byte_immediate())
        self.flags.set_from_alu_byte(value)
        self.regs.AL = value & 0xFF
        
    def _alu_ax_imm16(self, operation):
        """ Generic ax imm16 ALU processor. """
        value = operation(self.regs.AX, self.get_word_immediate())
        self.flags.set_from_alu_word(value)
        self.regs.AX = value & 0xFFFF
        
    # ADD
    def opcode_group_add(self, opcode):
        """ Entry point for all ADD opcodes. """
        self.alu_vector_table[opcode & 0x07](self.operator_add_16 if opcode & 0x01 else self.operator_add_8)
        
    def operator_add_8(self, operand_a, operand_b):
        """ Implements the 8-bit add operation with overflow support. """
        result = operand_a + operand_b
        self.flags.overflow = operand_a & 0x80 == operand_b & 0x80 and operand_a & 0x80 != result & 0x80
        return result
        
    def operator_add_16(self, operand_a, operand_b):
        """ Implements the 16-bit add operation with overflow support. """
        result = operand_a + operand_b
        self.flags.overflow = operand_a & 0x8000 == operand_b & 0x8000 and operand_a & 0x8000 != result & 0x8000
        return result
        
    # SUB
    def opcode_group_sub(self, opcode):
        """ Entry point for all SUB opcodes. """
        self.alu_vector_table[opcode & 0x07](self.operator_sub_16 if opcode & 0x01 else self.operator_sub_8)
        
    def operator_sub_8(self, operand_a, operand_b):
        """ Implements the 8-bit sub operation with overflow support. """
        result = operand_a - operand_b
        self.flags.overflow = operand_a & 0x80 != operand_b & 0x80 and operand_b & 0x80 == result & 0x80
        return result
        
    def operator_sub_16(self, operand_a, operand_b):
        """ Implements the 16-bit sub operation with overflow support. """
        result = operand_a - operand_b
        self.flags.overflow = operand_a & 0x8000 != operand_b & 0x8000 and operand_b & 0x8000 == result & 0x8000
        return result
        
    # SBB
    def operator_sbb_8(self, operand_a, operand_b):
        """ Implements the 8-bit SBB operator which subtracts an extra 1 if CF is set. """
        result = operand_a - operand_b
        if self.flags.carry:
            result -= 1
        self.flags.overflow = operand_a & 0x80 != operand_b & 0x80 and operand_b & 0x80 == result & 0x80
        return result
        
    def operator_sbb_16(self, operand_a, operand_b):
        """ Implements the 16-bit SBB operator which subtracts an extra 1 if CF is set. """
        result = operand_a - operand_b
        if self.flags.carry:
            result -= 1
        self.flags.overflow = operand_a & 0x8000 != operand_b & 0x8000 and operand_b & 0x8000 == result & 0x8000
        return result
        
    def opcode_group_sbb(self, opcode):
        """ Entry point for all SBB opcodes. """
        self.alu_vector_table[opcode & 0x07](self.operator_sbb_16 if opcode & 0x01 else self.operator_sbb_8)
        
    # ADC
    def operator_adc_8(self, operand_a, operand_b):
        """ Implements the 8-bit ADC operator which adds an extra 1 if CF is set. """
        result = operand_a + operand_b
        if self.flags.carry:
            result += 1
        self.flags.overflow = operand_a & 0x80 == operand_b & 0x80 and operand_a & 0x80 != result & 0x80
        return result
        
    def operator_adc_16(self, operand_a, operand_b):
        """ Implements the 16-bit ADC operator which adds an extra 1 if CF is set. """
        result = operand_a + operand_b
        if self.flags.carry:
            result += 1
        self.flags.overflow = operand_a & 0x8000 == operand_b & 0x8000 and operand_a & 0x8000 != result & 0x8000
        return result
        
    def opcode_group_adc(self, opcode):
        """ Entry point for all ADC opcodes. """
        self.alu_vector_table[opcode & 0x07](self.operator_adc_16 if opcode & 0x01 else self.operator_adc_8)
        
    # CMP
    def opcode_cmp_rm8_r8(self, _opcode):
        """ Subtract op2 from op1, update the flags, but don't store the value. """
        register, rm_type, rm_value = self.get_modrm_operands(8)
        op1 = self._get_rm8(rm_type, rm_value)
        op2 = self.regs[register]
        result = self.operator_sub_8(op1, op2)
        self.flags.set_from_alu_byte(result)
        
    def opcode_cmp_rm16_r16(self, _opcode):
        """ Subtract op2 from op1, update the flags, but don't store the value. """
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self._get_rm16(rm_type, rm_value)
        op2 = self.regs[register]
        result = self.operator_sub_16(op1, op2)
        self.flags.set_from_alu_word(result)
        
    def opcode_cmp_r8_rm8(self, _opcode):
        """ Subtract op2 from op1, update the flags, but don't store the value. """
        register, rm_type, rm_value = self.get_modrm_operands(8)
        op1 = self.regs[register]
        op2 = self._get_rm8(rm_type, rm_value)
        result = self.operator_sub_8(op1, op2)
        self.flags.set_from_alu_byte(result)
        
    def opcode_cmp_r16_rm16(self, _opcode):
        """ Subtract op2 from op1, update the flags, but don't store the value. """
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self.regs[register]
        op2 = self._get_rm16(rm_type, rm_value)
        result = self.operator_sub_16(op1, op2)
        self.flags.set_from_alu_word(result)
        
    def opcode_cmp_al_imm8(self, _opcode):
        """ Subtract immediate byte from AL, update the flags, but don't store the value. """
        result = self.operator_sub_8(self.regs.AL, self.get_byte_immediate())
        self.flags.set_from_alu_byte(result)
        
    def opcode_cmp_ax_imm16(self, _opcode):
        """ Subtract immediate word from AX, update the flags, but don't store the value. """
        result = self.operator_sub_16(self.regs.AX, self.get_word_immediate())
        self.flags.set_from_alu_word(result)
        
    def opcode_cbw(self):
        """ Sign extends the byte in AL to a word in AX. """
        self.regs.AX = sign_extend_byte_to_word(self.regs.AL)
        
    def opcode_cwd(self):
        """ Sign extends the word in AX to a double word in DX:AX. """
        self.regs.DX = 0xFFFF if self.regs.AX & 0x8000 == 0x8000 else 0x0000
        
    def opcode_xlat(self):
        """ Fetches the value at DS:[BX+AL] into AL. """
        self.regs.AL = self.read_data_byte(self.regs.BX + self.regs.AL)
        
    def opcode_group_f6f7(self, opcode):
        """ "Group 1" byte and word instructions. """
        bits = 16 if opcode == 0xF7 else 8
        sub_opcode, rm_type, rm_value = self.get_modrm_operands(bits, decode_register = False)
        value = self._get_rm_bits(bits, rm_type, rm_value)
        
        if sub_opcode == 0: # TEST
            self.flags.set_from_alu(value & self.get_immediate(bits == 16), bits = 16, carry = True)
            
        elif sub_opcode == 2: # NOT
            value = ~value
            self._set_rm_bits(bits, rm_type, rm_value, value)
            
        elif sub_opcode == 3: # NEG
            value = 0 - value
            self._set_rm_bits(bits, rm_type, rm_value, value)
            self.flags.set_from_alu(value, bits = bits, carry = False)
            self.flags.carry = value != 0
            
        elif sub_opcode == 4: # MUL (unsigned)
            if bits == 16:
                value = self.regs.AX * value
                self.regs.DX = (value & 0xFFFF0000) >> 16
                self.regs.AX = value & 0x0000FFFF
                self.flags.carry = self.flags.overflow = self.regs.DX != 0
            else:
                self.regs.AX = self.regs.AL * value
                self.flags.carry = self.flags.overflow = self.regs.AH != 0
                
        elif sub_opcode == 5: # IMUL (signed)
            if bits == 16:
                value = signed_word(self.regs.AX) * signed_word(value)
                self.regs.DX = (value & 0xFFFF0000) >> 16
                self.regs.AX = value & 0x0000FFFF
                # Is the high word (DX) just a sign extension of the low word (AX)?
                self.flags.carry = self.flags.overflow = (
                    (self.regs.AX & 0x8000 == 0x8000 and self.regs.DX != 0xFFFF) or
                    (self.regs.AX & 0x8000 == 0x0000 and self.regs.DX != 0x0000)
                )
            else:
                self.regs.AX = signed_byte(self.regs.AL) * signed_byte(value)
                # Is the high byte (AH) just a sign extension of the low byte (AL)?
                self.flags.carry = self.flags.overflow = (
                    (self.regs.AL & 0x80 == 0x80 and self.regs.AH != 0xFF) or
                    (self.regs.AL & 0x80 == 0x00 and self.regs.AH != 0x00)
                )
        elif sub_opcode == 6: # DIV (unsigned)
            # Throw a divide error for divide by zero.
            if value == 0:
                self.internal_service_interrupt(INT_DIVIDE_ERROR)
                
            else:
                if bits == 16:
                    source = (self.regs.DX << 16) | self.regs.AX
                    quotient = source // value
                    # Throw a divide error for a result too large to fix in AX.
                    if quotient > 0xFFFF:
                        self.internal_service_interrupt(INT_DIVIDE_ERROR)
                    else:
                        self.regs.AX = quotient
                        self.regs.DX = source % value
                    
                else:
                    source = self.regs.AX
                    quotient = source // value
                    # Throw a divide error for a result too large to fix in AL.
                    if quotient > 0xFF:
                        self.internal_service_interrupt(INT_DIVIDE_ERROR)
                    else:
                        self.regs.AL = quotient
                        self.regs.AH = source % value
                        
        elif sub_opcode == 7: # IDIV (signed)
            # Throw a divide error for divide by zero.
            if value == 0:
                self.internal_service_interrupt(INT_DIVIDE_ERROR)
                
            else:
                if bits == 16:
                    # Python's integer division always truncates towards negative infinity.
                    # We need to truncate towards zero, so do all of the work unsigned and convert back.
                    dividend = signed_dword((self.regs.DX << 16) | self.regs.AX)
                    divisor = signed_word(value)
                    
                    dividend_sign = -1 if dividend < 0 else 1
                    divisor_sign = -1 if divisor < 0 else 1
                    
                    quotient = (abs(dividend) // abs(divisor)) * dividend_sign * divisor_sign
                
                
                    # quotient = source // value
                    # Throw a divide error for a result too large to fix in AX.
                    if quotient > 32767 or quotient < -32767:
                        self.internal_service_interrupt(INT_DIVIDE_ERROR)
                    else:
                        self.regs.AX = quotient
                        self.regs.DX = (abs(dividend) % abs(divisor)) * dividend_sign
                    
                else:
                    # Python's integer division always truncates towards negative infinity.
                    # We need to truncate towards zero, so do all of the work unsigned and convert back.
                    dividend = signed_word(self.regs.AX)
                    divisor = signed_byte(value)
                    
                    dividend_sign = -1 if dividend < 0 else 1
                    divisor_sign = -1 if divisor < 0 else 1
                    
                    quotient = (abs(dividend) // abs(divisor)) * dividend_sign * divisor_sign
                    
                    # Throw a divide error for a value that will overflow a signed 8-bit value.
                    if quotient > 127 or quotient < -127:
                        self.internal_service_interrupt(INT_DIVIDE_ERROR)
                    else:
                        self.regs.AL = quotient
                        self.regs.AH = (abs(dividend) % abs(divisor)) * dividend_sign
                        
        else:
            raise NotImplementedError("sub_opcode = %r" % sub_opcode)
            
    # Inc/dec opcodes.
    def opcode_group_inc(self, opcode):
        """ Handler for all INC [register] instructions. """
        dest = WORD_REG[opcode & 0x07]
        self.regs[dest] += 1
        self.flags.set_from_alu_no_carry_word(self.regs[dest])
        
    def opcode_group_dec(self, opcode):
        """ Handler for all DEC [register] instructions. """
        dest = WORD_REG[opcode & 0x07]
        self.regs[dest] -= 1
        self.flags.set_from_alu_no_carry_word(self.regs[dest])
        
    def opcode_group_fe(self):
        """ Opcode group "2" for r/m8 which only has sub-opcodes 0 (INC) and 1 (DEC) defined. """
        sub_opcode, rm_type, rm_value = self.get_modrm_operands(8, decode_register = False)
        value = self._get_rm8(rm_type, rm_value)
        
        if sub_opcode == 0: # INC
            value += 1
            
        elif sub_opcode == 1: # DEC
            value -= 1
            
        else:
            raise NotImplementedError("sub_opcode = %r" % sub_opcode)
            
        self._set_rm8(rm_type, rm_value, value)
        self.flags.set_from_alu_no_carry_byte(value)
        
    def opcode_group_ff(self):
        """ Opcode group "2" for r/m16. """
        sub_opcode, rm_type, rm_value = self.get_modrm_operands(16, decode_register = False)
        value = self._get_rm16(rm_type, rm_value)
        
        if sub_opcode == 0: # INC
            value += 1
            self._set_rm16(rm_type, rm_value, value)
            self.flags.set_from_alu_no_carry_word(value)
            
        elif sub_opcode == 1: # DEC
            value -= 1
            self._set_rm16(rm_type, rm_value, value)
            self.flags.set_from_alu_no_carry_word(value)
            
        elif sub_opcode == 2: # CALL r/m16
            self.internal_push(self.regs.IP)
            self.regs.IP = value
            
        elif sub_opcode == 3: # CALLF - Call far to an IP:CS pointer at the address specified.
            self.internal_push(self.regs.CS)
            self.internal_push(self.regs.IP)
            self.regs.IP = value
            self.regs.CS = self._get_rm16(rm_type, rm_value + 2)
            
        elif sub_opcode == 4: # JMP
            self.regs.IP = value
            
        elif sub_opcode == 5: # JMPF - Jump far to an IP:CS pointer located at the address specified.
            self.regs.IP = value
            self.regs.CS = self._get_rm16(rm_type, rm_value + 2)
            
        elif sub_opcode == 6: # PUSH
            self.internal_push(value)
            
        else:
            raise NotImplementedError("sub_opcode = %r" % sub_opcode)
            
    # Shift opcodes.
    def opcode_group_rotate_and_shift(self, opcode):
        """ Opcode group for ROL, ROR, RCL, RCR, SHL, SHR, SAL/SHL, and SAR. """
        # 0xD0 and 0xD1 use a count of 1, 0xD2 and 0xD3 use the value in CL.
        count = 1
        if opcode & 0x02 == 0x02:
            count = self.regs.CL
            
        # 0xD0 and 0xD2 work on bytes, 0xD1 and 0xD3 work on words.
        bits = 8
        if opcode & 0x01 == 0x01:
            bits = 16
            
        high_bit_mask = 1 << (bits - 1)
        
        sub_opcode, rm_type, rm_value = self.get_modrm_operands(bits, decode_register = False)
        
        old_value = value = self._get_rm_bits(bits, rm_type, rm_value)
        
        # No need to shift by zero.
        if count == 0:
            return
            
        if sub_opcode == 0x00: # ROL - Rotate left shifting bits back in on the right.
            if bits == 8:
                value, self.flags.carry = rotate_left_8_bits(value, count)
            else:
                value, self.flags.carry = rotate_left_16_bits(value, count)
                
            self.flags.set_from_alu(value, bits = bits, carry = False)
            self._set_rm_bits(bits, rm_type, rm_value, value)
            
        elif sub_opcode == 0x01: # ROR - Rotate right shifting bits back in on the left.
            if bits == 8:
                value, self.flags.carry = rotate_right_8_bits(value, count)
            else:
                value, self.flags.carry = rotate_right_16_bits(value, count)
                
            self.flags.set_from_alu(value, bits = bits, carry = False)
            self._set_rm_bits(bits, rm_type, rm_value, value)
            
        elif sub_opcode == 0x02: # RCL - Rotate left through the carry flag.
            if bits == 8:
                value, self.flags.carry = rotate_thru_carry_left_8_bits(value, self.flags.carry, count)
            else:
                value, self.flags.carry = rotate_thru_carry_left_16_bits(value, self.flags.carry, count)
                
            self.flags.set_from_alu(value, bits = bits, carry = False)
            self._set_rm_bits(bits, rm_type, rm_value, value)
            
        elif sub_opcode == 0x03: # RCR - Rotate right through the carry flag.
            if bits == 8:
                value, self.flags.carry = rotate_thru_carry_right_8_bits(value, self.flags.carry, count)
            else:
                value, self.flags.carry = rotate_thru_carry_right_16_bits(value, self.flags.carry, count)
                
            self.flags.set_from_alu(value, bits = bits, carry = False)
            self._set_rm_bits(bits, rm_type, rm_value, value)
            
        elif sub_opcode == 0x05: # SHR - Shift right, no sign extension.
            self.flags.carry = (value >> (count - 1)) & 0x01 == 0x01
            value = value >> count
            
            self.flags.set_from_alu(value, bits = bits, carry = False)
            self._set_rm_bits(bits, rm_type, rm_value, value)
            
        elif sub_opcode == 0x04: # SHL/SAL - Shift in zeros to the left, to the left.
            if bits == 8:
                self.flags.carry = (value << count) & 0x100 == 0x100
            else:
                self.flags.carry = (value << count) & 0x10000 == 0x10000
                
            value = value << count
            self.flags.set_from_alu(value, bits = bits, carry = False)
            if count == 1:
                self.flags.overflow = ((old_value & high_bit_mask) ^ (value & high_bit_mask)) == high_bit_mask
                
            self._set_rm_bits(bits, rm_type, rm_value, value)
            
        elif sub_opcode == 0x07:
            if bits == 8:
                value, self.flags.carry = shift_arithmetic_right_8_bits(value, count)
            else:
                value, self.flags.carry = shift_arithmetic_right_16_bits(value, count)
                
            self.flags.set_from_alu(value, bits = bits, carry = False)
            self._set_rm_bits(bits, rm_type, rm_value, value)
            
        else:
            raise NotImplementedError("sub_opcode = %r" % sub_opcode)
            
    # ********** FLAGS opcodes. **********
    def opcode_stc(self):
        """ Sets the carry flag. """
        self.flags.carry = True
        
    def opcode_clc(self):
        """ Clears the carry flag. """
        self.flags.carry = False
        
    def opcode_cmc(self):
        """ Toggles the carry flag. """
        self.flags.carry = not self.flags.carry
        
    def opcode_std(self):
        """ Sets the direction flag (count down). """
        self.flags.direction = True
        
    def opcode_cld(self):
        """ Clears the direction flag (count up). """
        self.flags.direction = False
        
    def opcode_cli(self):
        """ Disable interrupts. """
        self.flags.interrupt_enable = False
        
    def opcode_sti(self):
        """ Enable interrupts. """
        self.flags.interrupt_enable = True
        
    def opcode_sahf(self):
        """ Copy AH into the lower byte of FLAGS (SF, ZF, AF, PF, CF). """
        self.flags.value = (self.flags.value & 0xFF00) | self.regs.AH
        
    def opcode_lahf(self):
        """ Copy the lower byte of FLAGS into AH (SF, ZF, AF, PF, CF). """
        self.regs.AH = self.flags.value & 0x00FF
        
    def opcode_pushf(self):
        """ Pushes the FLAGS register onto the stack. """
        self.internal_push(self.flags.value)
        
    def opcode_popf(self):
        """ Pops the FLAGS register off the stack. """
        self.flags.value = self.internal_pop()
        
    # ********** Miscellaneous opcodes. **********
    def _nop(self):
        pass
        
    def _hlt(self):
        log.critical("HLT encountered!")
        self.hlt = True
        log.error("Game over at CS:IP 0x%04x:0x%04x", self.regs.CS, self.regs.IP)
        
    def _jmp_rel16(self):
        offset = signed_word(self.get_word_immediate())
        self.regs.IP += offset
        
    def _jmp_rel8(self):
        offset = signed_byte(self.get_byte_immediate())
        self.regs.IP += offset
        
    # ********** I/O port opcodes. **********
    def opcode_in_al_imm8(self):
        """ Read a byte from a port specified by an immediate byte and put it in AL. """
        port = self.get_byte_immediate()
        self.regs.AL = self.bus.io_read_byte(port)
        
    def opcode_in_al_dx(self):
        """ Read a byte from a port specified by DX and put it in AL. """
        port = self.regs.DX
        self.regs.AL = self.bus.io_read_byte(port)
        
    def _out_imm8_al(self):
        port = self.get_byte_immediate()
        value = self.regs.AL
        self.bus.io_write_byte(port, value)
        
    def _out_dx_al(self):
        port = self.regs.DX
        value = self.regs.AL
        self.bus.io_write_byte(port, value)
        
    # ********** String opcodes. **********
    @supports_rep_prefix
    def opcode_stosb(self):
        """ Write the value in AL to ES:DI and increments or decrements DI. """
        self.bus.mem_write_byte(segment_offset_to_address(self.get_extra_segment(), self.regs.DI), self.regs.AL)
        self.regs.DI += -1 if self.flags.direction else 1
        
    @supports_rep_prefix
    def opcode_stosw(self):
        """ Write the word in AX to ES:DI and increments or decrements DI by 2. """
        self.bus.mem_write_word(segment_offset_to_address(self.get_extra_segment(), self.regs.DI), self.regs.AX)
        self.regs.DI += -2 if self.flags.direction else 2
        
    @supports_rep_prefix
    def opcode_lodsb(self):
        """ Reads a byte from DS:SI into AL and increments or decrements SI. """
        self.regs.AL = self.read_data_byte(self.regs.SI)
        self.regs.SI += -1 if self.flags.direction else 1
        
    @supports_rep_prefix
    def opcode_lodsw(self):
        """ Reads a word from DS:SI into AX and increments or decrements SI by 2. """
        self.regs.AX = self.read_data_word(self.regs.SI)
        self.regs.SI += -2 if self.flags.direction else 2
        
    @supports_rep_prefix
    def opcode_movsb(self):
        """ Reads a byte from DS:SI and writes it to ES:DI. """
        self.bus.mem_write_byte(
            segment_offset_to_address(self.get_extra_segment(), self.regs.DI),
            self.read_data_byte(self.regs.SI),
        )
        self.regs.SI += -1 if self.flags.direction else 1
        self.regs.DI += -1 if self.flags.direction else 1
        
    @supports_rep_prefix
    def opcode_movsw(self):
        """ Reads a word from DS:SI and writes it to ES:DI. """
        self.bus.mem_write_word(
            segment_offset_to_address(self.get_extra_segment(), self.regs.DI),
            self.read_data_word(self.regs.SI),
        )
        self.regs.SI += -2 if self.flags.direction else 2
        self.regs.DI += -2 if self.flags.direction else 2
        
    @supports_repz_repnz_prefix
    def opcode_scasb(self):
        """ Compare the byte at ES:DI with AL and update the flags. """
        result = self.operator_sub_8(
            self.regs.AL,
            self.bus.mem_read_byte(segment_offset_to_address(self.get_extra_segment(), self.regs.DI)),
        )
        self.flags.set_from_alu_byte(result)
        self.regs.DI += -1 if self.flags.direction else 1
        
    @supports_repz_repnz_prefix
    def opcode_scasw(self):
        """ Compare the word at ES:DI with AX and update the flags. """
        result = self.operator_sub_16(
            self.regs.AX,
            self.bus.mem_read_word(segment_offset_to_address(self.get_extra_segment(), self.regs.DI)),
        )
        self.flags.set_from_alu_word(result)
        self.regs.DI += -2 if self.flags.direction else 2
        
    @supports_repz_repnz_prefix
    def opcode_cmpsb(self):
        """ Compare the byte at ES:DI with the byte at DS:SI and update the flags. """
        result = self.operator_sub_8(
            self.bus.mem_read_word(segment_offset_to_address(self.get_data_segment(), self.regs.SI)),
            self.bus.mem_read_word(segment_offset_to_address(self.get_extra_segment(), self.regs.DI)),
        )
        self.flags.set_from_alu_byte(result)
        self.regs.SI += -1 if self.flags.direction else 1
        self.regs.DI += -1 if self.flags.direction else 1
        
    # ********** Memory access helpers. **********
    def get_data_segment(self):
        """ Helper function to return the effective data segment. """
        return self.regs[self.segment_override] if self.segment_override else self.regs.DS
        
    def get_extra_segment(self):
        """ Helper function to return the effective extra segment. """
        return self.regs[self.segment_override] if self.segment_override else self.regs.ES
        
    def write_data_word(self, offset, value):
        """ Write a word to data memory at the given offset.  Assume DS unless overridden by a prefix. """
        self.bus.mem_write_word(segment_offset_to_address(self.get_data_segment(), offset), value)
        
    def read_data_word(self, offset):
        """ Read a word from data memory at the given offset.  Assume DS unless overridden by a prefix. """
        return self.bus.mem_read_word(segment_offset_to_address(self.get_data_segment(), offset))
        
    def write_data_byte(self, offset, value):
        """ Write a byte to data memory at the given offset.  Assume DS unless overridden by a prefix. """
        self.bus.mem_write_byte(segment_offset_to_address(self.get_data_segment(), offset), value)
        
    def read_data_byte(self, offset):
        """ Read a byte from data memory at the given offset.  Assume DS unless overridden by a prefix. """
        return self.mem_read_byte(segment_offset_to_address(self.get_data_segment(), offset))
        
    def _get_rm16(self, rm_type, rm_value):
        """ Helper for reading from a 16 bit r/m field. """
        if rm_type == REGISTER:
            return self.regs[rm_value]
        elif rm_type == ADDRESS:
            return self.read_data_word(rm_value)
            
    def _set_rm16(self, rm_type, rm_value, value):
        """ Helper for writing to a 16 bit r/m field. """
        if rm_type == REGISTER:
            # The UnionRegs object will handle masking correctly.
            self.regs[rm_value] = value
        elif rm_type == ADDRESS:
            # Mask here as memory accesses are direct array.array accesses that do not like signed values.
            self.write_data_word(rm_value, value & 0xFFFF)
            
    def _get_rm8(self, rm_type, rm_value):
        """ Helper for reading from an 8 bit r/m field. """
        if rm_type == REGISTER:
            assert rm_value[1] in "HL"
            return self.regs[rm_value]
        elif rm_type == ADDRESS:
            return self.read_data_byte(rm_value)
            
    def _set_rm8(self, rm_type, rm_value, value):
        """ Helper for writing to an 8 bit r/m field. """
        if rm_type == REGISTER:
            assert rm_value[1] in "HL"
            # The UnionRegs object will handle masking correctly.
            self.regs[rm_value] = value
        elif rm_type == ADDRESS:
            # Mask here as memory accesses are direct array.array accesses that do not like signed values.
            self.write_data_byte(rm_value, value & 0xFF)
            
    def _get_rm_bits(self, bits, rm_type, rm_value):
        """ Helper for reading from either an 8 or 16 bit r/m field. """
        if bits == 8:
            return self._get_rm8(rm_type, rm_value)
        else:
            return self._get_rm16(rm_type, rm_value)
            
    def _set_rm_bits(self, bits, rm_type, rm_value, value):
        """ Helper for writing to either an 8 or 16 bit r/m field. """
        if bits == 8:
            return self._set_rm8(rm_type, rm_value, value)
        else:
            return self._set_rm16(rm_type, rm_value, value)
            
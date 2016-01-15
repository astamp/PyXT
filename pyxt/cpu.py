"""
pyxt.cpu - 8088-ish CPU module for PyXT.
"""

# Standard library imports
import re
import sys
import struct
import operator
from ctypes import Structure, Union, c_ushort, c_ubyte

# PyXT imports
from pyxt.helpers import *

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants
WORD, LOW, HIGH = range(3)

GDB_EXAMINE_REGEX = re.compile("^x\/(\\d+)([xduotacfs])([bwd])$")

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
def sign_extend_byte_to_word(value):
    value = value & 0x00FF
    if value & 0x80:
        value |= 0xFF00
    return value
    
def word_to_bytes_le(word):
    assert word >= 0 and word <= 0xFFFF
    return (word & 0x00FF), ((word & 0xFF00) >> 8)
    
def bytes_to_word_le(data):
    assert len(data) == 2
    return ((data[1] & 0xFF) << 8) | (data[0] & 0xFF)
    
SIGNED_WORD = struct.Struct("<h")
UNSIGNED_WORD = struct.Struct("<H")
SIGNED_BYTE = struct.Struct("<b")
UNSIGNED_BYTE = struct.Struct("<B")

def signed_word(value):
    """ Interpret an unsigned word as a signed word. """
    return SIGNED_WORD.unpack(UNSIGNED_WORD.pack(value))[0]
    
def signed_byte(value):
    """ Interpret an unsigned byte as a signed byte. """
    return SIGNED_BYTE.unpack(UNSIGNED_BYTE.pack(value))[0]
    
def decode_seg_reg(value):
    """ Decode a segment register selector into the string register name. """
    return SEGMENT_REG[value & 0x03]
    
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
    
    IOPL_1 =      0x1000
    IOPL_2 =      0x2000
    NESTED =      0x4000
    RESERVED_4 =  0x8000
    
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
        
    def set_from_alu(self, value):
        """ Set ZF, SF, CF, and PF based the result of an ALU operation. """
        self.zero = not value
        self.sign = value & 0x8000 == 0x8000
        self.carry = value & 0x10000 == 0x10000
        self.parity = (count_bits_fast(value & 0x00FF) % 2) == 0
        
    def set_from_alu_no_carry(self, value):
        """ Set ZF, SF, and PF based the result of an ALU operation. """
        self.zero = not value
        self.sign = value & 0x8000 == 0x8000
        self.parity = (count_bits_fast(value & 0x00FF) % 2) == 0
        
    @property
    def value(self):
        """ Return the FLAGS register as a word value. """
        value = self.BLANK
        
        if self.carry: value |= self.CARRY
        if self.parity: value |= self.PARITY
        if self.adjust: value |= self.ADJUST
        if self.zero: value |= self.ZERO
        if self.sign: value |= self.SIGN
        if self.trap: value |= self.TRAP
        if self.interrupt_enable: value |= self.INT_ENABLE
        if self.direction: value |= self.DIRECTION
        if self.overflow: value |= self.OVERFLOW
        
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
        
        # Internal debugging system. (TODO: Move this elsewhere)
        self.breakpoints = []
        self.single_step = False
        self.debugger_shortcut = []
        
        # CPU halt flag.
        self.hlt = False
        
        # Flags register.
        self.flags = FLAGS()
        
        # Normal registers.
        self.regs = UnionRegs()
        self.regs.CS = 0xFFFF
        
        # ALU vector table.
        self.alu_vector_table = {
            0x00 : self._alu_rm8_r8,
            0x01 : self._alu_rm16_r16,
            0x02 : self._alu_r8_rm8,
            0x03 : self._alu_r16_rm16,
            0x04 : self._alu_al_imm8,
            0x05 : self._alu_ax_imm16,
        }
        
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
        # Uncomment these lines for debugging, but they make the code slow if left on.
        
        # self.dump_regs()
        
        # if self.should_break():
            # self.enter_debugger()
            
        opcode = self.read_instruction_byte()
        # log.debug("Fetched opcode: 0x%02x", opcode)
        if opcode == 0xF4:
            self._hlt()
        elif opcode & 0xF8 == 0x00 and opcode & 0x6 != 0x6:
            self.opcode_group_add(opcode)
        elif opcode & 0xF8 == 0x08 and opcode & 0x6 != 0x6:
            self.opcode_group_or(opcode)
        elif opcode & 0xF8 == 0x10 and opcode & 0x6 != 0x6:
            self.opcode_group_adc(opcode)
        elif opcode & 0xF8 == 0x18 and opcode & 0x6 != 0x6:
            self.opcode_group_sbb(opcode)
        elif opcode & 0xF8 == 0x20 and opcode & 0x6 != 0x6:
            self.opcode_group_and(opcode)
        elif opcode & 0xF8 == 0x28 and opcode & 0x6 != 0x6:
            self.opcode_group_sub(opcode)
        elif opcode & 0xFC == 0x80:
            self.opcode_group_8x(opcode)
        elif opcode & 0xF8 == 0x40:
            self.opcode_group_inc(opcode)
        elif opcode & 0xF8 == 0x48:
            self.opcode_group_dec(opcode)
        elif opcode & 0xF8 == 0x50:
            self.opcode_group_push(opcode)
        elif opcode & 0xF8 == 0x58:
            self.opcode_group_pop(opcode)
        elif opcode & 0xF8 == 0x90:
            self._xchg_r16_ax(opcode)
        elif opcode == 0x74:
            self._jz()
        elif opcode == 0x75:
            self._jnz()
        elif opcode == 0xE2:
            self._loop()
        elif opcode == 0xE8:
            self._call()
        elif opcode == 0xC3:
            self._ret()
        elif opcode & 0xF0 == 0xB0:
            self._mov_imm_to_reg(opcode)
        elif opcode == 0x8B:
            self._mov_r16_rm16()
        elif opcode == 0x88:
            self._mov_rm8_r8()
        elif opcode == 0x89:
            self._mov_reg16_to_rm16()
        elif opcode == 0x8A:
            self._mov_rm8_to_reg8() # BAD NAME
        elif opcode == 0x31:
            self._xor_rm16_r16()
        elif opcode == 0x72:
            self._jc()
        elif opcode == 0x39:
            self._cmp_rm16_r16()
        elif opcode == 0x76:
            self._jna()
        elif opcode == 0x77:
            self._ja()
        elif opcode == 0x79:
            self._jns()
        elif opcode == 0x78:
            self._js()
        elif opcode == 0xF8:
            self._clc()
        elif opcode == 0xF9:
            self._stc()
        elif opcode == 0xFC:
            self._cld()
        elif opcode == 0xFD:
            self._std()
        elif opcode == 0x90:
            self._nop()
        elif opcode == 0xE9:
            self._jmp_rel16()
        elif opcode == 0xEB:
            self._jmp_rel8()
        elif opcode == 0x86:
            self._xchg_r8_rm8()
        elif opcode == 0xFE:
            self._inc_dec_rm8()
        elif opcode == 0xFF:
            self._inc_dec_rm16()
        elif opcode == 0x3C:
            self._cmp_al_imm8()
        elif opcode == 0xC6:
            self._mov_rm8_imm8()
        elif opcode == 0xC7:
            self._mov_rm16_imm16()
        elif opcode == 0xEA:
            self._jmpf()
        elif opcode == 0xFA:
            self._cli()
        elif opcode == 0x9E:
            self._sahf()
        elif opcode == 0x9F:
            self._lahf()
        elif opcode == 0x73:
            self._jae_jnb_jnc()
        elif opcode == 0x7B:
            self._jnp_jpo()
        elif opcode == 0x7A:
            self._jp_jpe()
        elif opcode & 0xFC == 0xD0:
            self._rotate_and_shift(opcode)
        elif opcode == 0x71:
            self._jno()
        elif opcode == 0x70:
            self._jo()
        elif opcode == 0x32:
            self._xor_r8_rm8()
        elif opcode == 0xE4:
            self.opcode_in_al_imm8()
        elif opcode == 0xE6:
            self._out_imm8_al()
        elif opcode == 0xEE:
            self._out_dx_al()
        elif opcode == 0x34:
            self._xor_al_imm8()
        elif opcode == 0x33:
            self._xor_r16_rm16()
        elif opcode == 0x8E:
            self._mov_sreg_rm16()
        elif opcode == 0x8C:
            self._mov_rm16_sreg()
        else:
            log.error("Invalid opcode: 0x%02x at CS:IP 0x%04x:0x%04x", opcode, self.regs.CS, self.regs.IP)
            self._hlt()
            
    # ********** Opcode parameter helpers. **********
    def get_modrm_operands(self, size, decode_register = True):
        """ Returns register, rm_type, rm_value from a MODRM byte. """
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
            
        if mod in (0x00, 0x01, 0x02):
            rm_type = ADDRESS
            if rm == 0x00:
                rm_value = self.regs.BX + self.regs.SI
            elif rm == 0x01:
                rm_value = self.regs.BX + self.regs.DI
            elif rm == 0x05:
                rm_value = self.regs.DI
            elif rm == 0x06:
                if mod == 0x00:
                    rm_value = self.get_word_immediate()
                else:
                    assert 0
            elif rm == 0x07:
                rm_value = self.regs.BX
                
            displacement = 0
            if not (mod == 0x00 and rm == 0x06):
                if mod == 0x01:
                    displacement = sign_extend_byte_to_word(self.get_byte_immediate())
                elif mod == 0x02:
                    displacement = self.get_word_immediate()
                
            rm_value += displacement
            
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
        
    def get_imm(self, word):
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
            
        value = self.get_imm(word)
        self.regs[dest] = value
        log.debug("MOV'd 0x%04x into %s", value, dest)
        
    def _mov_r16_rm16(self):
        log.info("MOV r16 r/m16")
        register, rm_type, rm_value = self.get_modrm_operands(16)
        self.regs[register] = self._get_rm16(rm_type, rm_value)
        
    def _mov_rm8_r8(self):
        log.info("MOV r/m8 r8")
        register, rm_type, rm_value = self.get_modrm_operands(8)
        self._set_rm8(rm_type, rm_value, self.regs[register])
        
    def _mov_rm8_to_reg8(self):
        log.info("MOV 8-bit r/m to reg (mov r8, r/m8)")
        register, rm_type, rm_value = self.get_modrm_operands(16)
        self.regs[register] = self._get_rm16(rm_type, rm_value)
        
    def _mov_reg16_to_rm16(self):
        log.info("MOV 16-bit reg to r/m (mov r/m16/32, r16/32)")
        register, rm_type, rm_value = self.get_modrm_operands(16)
        self._set_rm16(rm_type, rm_value, self.regs[register])
        
    def _mov_rm8_imm8(self):
        log.debug("MOV r/m8 imm8")
        sub_opcode, rm_type, rm_value = self.get_modrm_operands(8, decode_register = False)
        assert sub_opcode == 0
        self._set_rm8(rm_type, rm_value, self.get_byte_immediate())
        
    def _mov_rm16_imm16(self):
        log.debug("MOV r/m16 imm16")
        sub_opcode, rm_type, rm_value = self.get_modrm_operands(16, decode_register = False)
        assert sub_opcode == 0
        self._set_rm16(rm_type, rm_value, self.get_word_immediate())
        
    def _mov_sreg_rm16(self):
        log.debug("MOV Sreg r/m16")
        segment_register, rm_type, rm_value = self.get_modrm_operands(16, decode_register = False)
        self.regs[decode_seg_reg(segment_register)] = self._get_rm16(rm_type, rm_value)
        
    def _mov_rm16_sreg(self):
        log.debug("MOV r/m16 Sreg")
        segment_register, rm_type, rm_value = self.get_modrm_operands(16, decode_register = False)
        self._set_rm16(rm_type, rm_value, self.regs[decode_seg_reg(segment_register)])
        
    def _xchg_r8_rm8(self):
        log.debug("XCHG r8 r/m8")
        register, rm_type, rm_value = self.get_modrm_operands(8)
        temp = self._get_rm8(rm_type, rm_value)
        self._set_rm8(rm_type, rm_value, self.regs[register])
        self.regs[register] = temp
        
    def _xchg_r16_ax(self, opcode):
        log.debug("XCHG r16 AX")
        dest = WORD_REG[opcode & 0x07]
        temp = self.regs[dest]
        self.regs[dest] = self.regs.AX
        self.regs.AX = temp
        
    # ********** Stack opcodes. **********
    def opcode_group_push(self, opcode):
        """ Handler for all PUSH [register] instructions. """
        src = WORD_REG[opcode & 0x07]
        value = self.regs[src]
        self.internal_push(value)
        log.debug("PUSH'd 0x%04x from %s", value, src)
        
    def opcode_group_pop(self, opcode):
        """ Handler for all POP [register] instructions. """
        dest = WORD_REG[opcode & 0x07]
        self.regs[dest] = self.internal_pop()
        log.debug("POP'd 0x%04x into %s", self.regs[dest], dest)
        
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
    def _jc(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_byte_immediate()))[0]
        if self.flags.carry:
            self.regs.IP += distance
            log.debug("JC incremented IP by 0x%04x to 0x%04x", distance, self.regs.IP)
        else:
            log.debug("JC was skipped.")
            
    def _jz(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_byte_immediate()))[0]
        if self.flags.zero:
            self.regs.IP += distance
            log.debug("JZ incremented IP by 0x%04x to 0x%04x", distance, self.regs.IP)
        else:
            log.debug("JZ was skipped.")
            
    def _jnz(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_byte_immediate()))[0]
        if self.flags.zero:
            log.debug("JNZ/JNE was skipped.")
        else:
            self.regs.IP += distance
            log.debug("JNZ/JNE incremented IP by 0x%04x to 0x%04x", distance, self.regs.IP)
            
    def _jna(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_byte_immediate()))[0]
        if self.flags.zero or self.flags.carry:
            self.regs.IP += distance
            log.debug("JNA/JBE incremented IP by 0x%04x to 0x%04x", distance, self.regs.IP)
        else:
            log.debug("JNA/JBE was skipped.")
            
    def _ja(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_byte_immediate()))[0]
        if self.flags.zero == False and self.flags.carry == False:
            self.regs.IP += distance
            log.debug("JA incremented IP by 0x%04x to 0x%04x", distance, self.regs.IP)
        else:
            log.debug("JA was skipped.")
            
    def _jae_jnb_jnc(self):
        """ Jump short if the carry flag is clear. """
        distance = self.get_byte_immediate()
        if self.flags.carry == False:
            self.regs.IP += signed_byte(distance)
            log.debug("JAE/JNB/JNC incremented IP by 0x%04x to 0x%04x", distance, self.regs.IP)
        else:
            log.debug("JAE/JNB/JNC was skipped.")
            
    def _jnp_jpo(self):
        """ Jump short if the parity flag is clear. """
        distance = self.get_byte_immediate()
        if self.flags.parity == False:
            self.regs.IP += signed_byte(distance)
            log.debug("JNP/JPO incremented IP by 0x%04x to 0x%04x", distance, self.regs.IP)
        else:
            log.debug("JNP/JPO was skipped.")
            
    def _jp_jpe(self):
        """ Jump short if the parity flag is set. """
        distance = self.get_byte_immediate()
        if self.flags.parity == False:
            log.debug("JP/JPE was skipped.")
        else:
            self.regs.IP += signed_byte(distance)
            log.debug("JP/JPE incremented IP by 0x%04x to 0x%04x", distance, self.regs.IP)
            
    def _jns(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_byte_immediate()))[0]
        if self.flags.sign:
            log.debug("JNS was skipped.")
        else:
            self.regs.IP += distance
            log.debug("JNS incremented IP by 0x%04x to 0x%04x", distance, self.regs.IP)
            
    def _js(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_byte_immediate()))[0]
        if self.flags.sign:
            self.regs.IP += distance
            log.debug("JS incremented IP by 0x%04x to 0x%04x", distance, self.regs.IP)
        else:
            log.debug("JS was skipped.")
            
    def _jno(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_byte_immediate()))[0]
        if self.flags.overflow:
            log.debug("JNO was skipped.")
        else:
            self.regs.IP += distance
            log.debug("JNO incremented IP by 0x%04x to 0x%04x", distance, self.regs.IP)
            
    def _jo(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_byte_immediate()))[0]
        if self.flags.overflow:
            self.regs.IP += distance
            log.debug("JO incremented IP by 0x%04x to 0x%04x", distance, self.regs.IP)
        else:
            log.debug("JO was skipped.")
            
    # ********** Fancy jump opcodes. **********
    def _jmpf(self):
        # This may look silly, but you can't modify IP or CS while reading the JUMP FAR parameters.
        new_ip = self.get_word_immediate()
        new_cs = self.get_word_immediate()
        self.regs.IP = new_ip
        self.regs.CS = new_cs
        log.debug("JMP FAR to CS: 0x%04x  IP:0x%04x", self.regs.CS, self.regs.IP)
        
    def _call(self):
        offset = self.get_word_immediate()
        self.internal_push(self.regs.IP)
        self.regs.IP += offset
        log.debug("CALL incremented IP by 0x%04x to 0x%04x", offset, self.regs.IP)
        
    def _ret(self):
        self.regs.IP = self.internal_pop()
        log.debug("RET back to 0x%04x", self.regs.IP)
        
    def _loop(self):
        """ Decrement CX and jump short if it is non-zero. """
        distance = self.get_byte_immediate()
        regs = self.regs
        
        value = self.regs.CX - 1
        self.flags.set_from_alu(value)
        self.regs.CX = value
        
        if value != 0:
            self.regs.IP += signed_byte(distance)
            # log.debug("LOOP incremented IP by 0x%04x to 0x%04x", distance, self.regs.IP)
            
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
        immediate = self.get_imm(word_imm)
        if sign_extend and not word_imm:
            extended_imm = sign_extend_byte_to_word(immediate)
            log.debug("Sign extending 0x%02x to 0x%04x", immediate, extended_imm)
            immediate = extended_imm
            
        set_value = True
        if sub_opcode == 0x00:
            result = value + immediate
        elif sub_opcode == 0x01:
            result = value | immediate
        elif sub_opcode == 0x02:
            result = value + immediate + (1 if self.flags.carry else 0)
        elif sub_opcode == 0x04:
            result = value & immediate
        elif sub_opcode == 0x05:
            result = value - immediate
        elif sub_opcode == 0x07:
            result = value - immediate
            set_value = False
        else:
            assert 0
            
        self.flags.set_from_alu(result)
        if set_value:
            if word_reg:
                self._set_rm16(rm_type, rm_value, result)
            else:
                self._set_rm8(rm_type, rm_value, result)
                
    # Bitwise opcodes.
    def _xor_rm16_r16(self):
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self._get_rm16(rm_type, rm_value)
        op2 = self.regs[register]
        op1 = op1 ^ op2
        self.flags.set_from_alu(op1)
        self._set_rm16(rm_type, rm_value, op1 & 0xFFFF)
        
    def _xor_r16_rm16(self):
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self.regs[register]
        op2 = self._get_rm16(rm_type, rm_value)
        op1 = op1 ^ op2
        self.flags.set_from_alu(op1)
        self.regs[register] = op1 & 0xFFFF
        
    def _xor_r8_rm8(self):
        register, rm_type, rm_value = self.get_modrm_operands(8)
        op1 = self._get_rm8(rm_type, rm_value)
        op2 = self.regs[register]
        op1 = op1 ^ op2
        self.flags.set_from_alu(op1)
        self._set_rm8(rm_type, rm_value, op1 & 0xFFFF)
        
    def _xor_al_imm8(self):
        log.info("XOR al imm8")
        value = self.regs.AL ^ self.get_byte_immediate()
        self.flags.set_from_alu(value)
        self.regs.AL = value & 0xFF
        
    def opcode_group_or(self, opcode):
        """ Entry point for all OR opcodes. """
        self.alu_vector_table[opcode & 0x07](operator.or_)
        
    def opcode_group_and(self, opcode):
        """ Entry point for all AND opcodes. """
        self.alu_vector_table[opcode & 0x07](operator.and_)
        
    # Generic ALU helper functions.
    def _alu_rm8_r8(self, operation):
        """ Generic r/m8 r8 ALU processor. """
        register, rm_type, rm_value = self.get_modrm_operands(8)
        op1 = self._get_rm8(rm_type, rm_value)
        op2 = self.regs[register]
        op1 = operation(op1, op2)
        self.flags.set_from_alu(op1)
        self._set_rm8(rm_type, rm_value, op1 & 0xFF)
        
    def _alu_rm16_r16(self, operation):
        """ Generic r/m16 r16 ALU processor. """
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self._get_rm16(rm_type, rm_value)
        op2 = self.regs[register]
        op1 = operation(op1, op2)
        self.flags.set_from_alu(op1)
        self._set_rm16(rm_type, rm_value, op1 & 0xFFFF)
        
    def _alu_r8_rm8(self, operation):
        """ Generic r8 r/m8 ALU processor. """
        register, rm_type, rm_value = self.get_modrm_operands(8)
        op1 = self.regs[register]
        op2 = self._get_rm8(rm_type, rm_value)
        op1 = operation(op1, op2)
        self.flags.set_from_alu(op1)
        self.regs[register] = op1 & 0xFF
        
    def _alu_r16_rm16(self, operation):
        """ Generic r16 r/m16 ALU processor. """
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self.regs[register]
        op2 = self._get_rm16(rm_type, rm_value)
        op1 = operation(op1, op2)
        self.flags.set_from_alu(op1)
        self.regs[register] = op1 & 0xFFFF
        
    def _alu_al_imm8(self, operation):
        """ Generic al imm8 ALU processor. """
        value = operation(self.regs.AL, self.get_byte_immediate())
        self.flags.set_from_alu(value)
        self.regs.AL = value & 0xFF
        
    def _alu_ax_imm16(self, operation):
        """ Generic ax imm16 ALU processor. """
        value = operation(self.regs.AX, self.get_word_immediate())
        self.flags.set_from_alu(value)
        self.regs.AX = value & 0xFFFF
        
    # Math opcodes.
    def opcode_group_add(self, opcode):
        """ Entry point for all ADD opcodes. """
        self.alu_vector_table[opcode & 0x07](operator.add)
        
    def opcode_group_sub(self, opcode):
        """ Entry point for all SUB opcodes. """
        self.alu_vector_table[opcode & 0x07](operator.sub)
        
    def operator_sbb(self, operand_a, operand_b):
        """ Implements the SBB operator which subtracts an extra 1 if CF is set. """
        result = operand_a - operand_b
        if self.flags.carry:
            result -= 1
        return result
        
    def opcode_group_sbb(self, opcode):
        """ Entry point for all SBB opcodes. """
        self.alu_vector_table[opcode & 0x07](self.operator_sbb)
        
    def operator_adc(self, operand_a, operand_b):
        """ Implements the ADC operator which adds an extra 1 if CF is set. """
        result = operand_a + operand_b
        if self.flags.carry:
            result += 1
        return result
        
    def opcode_group_adc(self, opcode):
        """ Entry point for all ADC opcodes. """
        self.alu_vector_table[opcode & 0x07](self.operator_adc)
        
    def _cmp_rm16_r16(self):
        log.debug("CMP r/m16 r16")
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self._get_rm16(rm_type, rm_value)
        op2 = self.regs[register]
        value = op1 - op2
        self.flags.set_from_alu(value)
        
    def _cmp_al_imm8(self):
        log.debug("CMP al imm8")
        value = self.regs.AL - self.get_byte_immediate()
        self.flags.set_from_alu(value)
        
    # Inc/dec opcodes.
    def opcode_group_inc(self, opcode):
        """ Handler for all INC [register] instructions. """
        dest = WORD_REG[opcode & 0x07]
        self.regs[dest] += 1
        self.flags.set_from_alu_no_carry(self.regs[dest])
        # log.debug("INC'd %s to 0x%04x", dest, self.regs[dest])
        
    def opcode_group_dec(self, opcode):
        """ Handler for all DEC [register] instructions. """
        dest = WORD_REG[opcode & 0x07]
        self.regs[dest] -= 1
        self.flags.set_from_alu_no_carry(self.regs[dest])
        # log.debug("DEC'd %s to 0x%04x", dest, self.regs[dest])
        
    def _inc_dec_rm8(self):
        # log.debug("INC/DEC r/m8")
        sub_opcode, rm_type, rm_value = self.get_modrm_operands(8, decode_register = False)
        value = self._get_rm8(rm_type, rm_value)
        if sub_opcode == 0:
            value += 1
        elif sub_opcode == 1:
            value -= 1
        else:
            assert 0
        self._set_rm8(rm_type, rm_value, value)
        self.flags.set_from_alu_no_carry(value)
        
    def _inc_dec_rm16(self):
        log.debug("INC/DEC r/m16")
        sub_opcode, rm_type, rm_value = self.get_modrm_operands(16, decode_register = False)
        value = self._get_rm16(rm_type, rm_value)
        if sub_opcode == 0:
            value += 1
        elif sub_opcode == 1:
            value -= 1
        else:
            assert 0
        self._set_rm16(rm_type, rm_value, value)
        self.flags.set_from_alu_no_carry(value)
        
    # Shift opcodes.
    def _rotate_and_shift(self, opcode):
        log.debug("Rotate/shift")
        
        count = 1
        if opcode & 0x02 == 0x02:
            count = self.regs.CL
            
        bits = 8
        if opcode & 0x01 == 0x01:
            bits = 16
            
        high_bit_mask = 1 << (bits - 1)
        
        sub_opcode, rm_type, rm_value = self.get_modrm_operands(bits, decode_register = False)
        
        old_value = value = self._get_rm16(rm_type, rm_value)
        if sub_opcode == 0x05:
            value = value >> count
            self.flags.set_from_alu_no_carry(value)
            self.flags.carry = (old_value >> (count - 1)) & 0x01 == 0x01
        elif sub_opcode == 0x04:
            # 0x0010 << 12 => CF = True
            self.flags.carry = (value << count) & 0x10000 == 0x10000
            value = value << count
            self.flags.set_from_alu_no_carry(value)
            if count == 1:
                self.flags.overflow = ((old_value & high_bit_mask) ^ (value & high_bit_mask)) == high_bit_mask
        else:
            assert 0
            
    # ********** FLAGS opcodes. **********
    def _stc(self):
        """ Sets the carry flag. """
        log.debug("STC")
        self.flags.carry = True
        
    def _clc(self):
        """ Clears the carry flag. """
        log.debug("CLC")
        self.flags.carry = False
        
    def _std(self):
        """ Sets the direction flag. """
        log.debug("STD")
        self.flags.direction = True
        
    def _cld(self):
        """ Clears the direction flag. """
        log.debug("CLD")
        self.flags.direction = False
        
    def _cli(self):
        log.info("CLI Disabling interrupts.")
        self.flags.interrupt_enable = False
        
    def _sahf(self):
        """ Copy AH into the lower byte of FLAGS (SF, ZF, AF, PF, CF). """
        self.flags.value = (self.flags.value & 0xFF00) | self.regs.AH
        
    def _lahf(self):
        """ Copy the lower byte of FLAGS into AH (SF, ZF, AF, PF, CF). """
        self.regs.AH = self.flags.value & 0x00FF
        
    # ********** Miscellaneous opcodes. **********
    def _nop(self):
        log.critical("NOP")
        
    def _hlt(self):
        log.critical("HLT encountered!")
        self.hlt = True
        
    def _jmp_rel16(self):
        offset = signed_word(self.get_word_immediate())
        self.regs.IP += offset
        log.debug("JMP incremented IP by 0x%04x to 0x%04x", offset, self.regs.IP)
        
    def _jmp_rel8(self):
        offset = signed_byte(self.get_byte_immediate())
        self.regs.IP += offset
        log.debug("JMP incremented IP by 0x%04x to 0x%04x", offset, self.regs.IP)
        
    # ********** I/O port opcodes. **********
    def opcode_in_al_imm8(self):
        """ Read a byte from a port and put it in AL. """
        port = self.get_byte_immediate()
        self.regs.AL = self.bus.io_read_byte(port)
        log.info("Read 0x%02x from port 0x%04x.", self.regs.AL, port)
        
    def _out_imm8_al(self):
        port = self.get_byte_immediate()
        value = self.regs.AL
        log.info("Writing 0x%02x to port 0x%04x.", value, port)
        self.bus.io_write_byte(port, value)
        
    def _out_dx_al(self):
        port = self.regs.DX
        value = self.regs.AL
        log.info("Writing 0x%02x to port 0x%04x.", value, port)
        self.bus.io_write_byte(port, value)
        
    # ********** Memory access helpers. **********
    def get_data_segment(self):
        """ Helper function to return the effective data segment. """
        return self.regs.DS
        
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
            self.regs[rm_value] = value
        elif rm_type == ADDRESS:
            self.write_data_word(rm_value, value)
            
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
            self.regs[rm_value] = value
        elif rm_type == ADDRESS:
            self.write_data_byte(rm_value, value)
            
    # ********** Debugger functions. **********
    def dump_regs(self):
        regs = ("AX", "BX", "CX", "DX")
        log.debug("  ".join(["%s = 0x%04x" % (reg, self.regs[reg]) for reg in regs]))
        regs = ("IP", "SP", "SI", "DI")
        log.debug("  ".join(["%s = 0x%04x" % (reg, self.regs[reg]) for reg in regs]))
        regs = ("CS", "SS", "DS", "ES")
        log.debug("  ".join(["%s = 0x%04x" % (reg, self.regs[reg]) for reg in regs]))
        
    def should_break(self):
        return self.single_step or self.regs.IP in self.breakpoints
        
    def enter_debugger(self):
        while True:
            print ">",
            cmd = raw_input().lower().split()
            
            if len(cmd) == 0 and len(self.debugger_shortcut) != 0:
                cmd = self.debugger_shortcut
                print "Using: %s" % " ".join(cmd)
            else:
                self.debugger_shortcut = cmd
                
            if len(cmd) == 0:
                continue
                
            if len(cmd) == 1 and cmd[0] in ("continue", "c"):
                self.single_step = False
                break
                
            elif len(cmd) == 1 and cmd[0] in ("step", "s"):
                self.single_step = True
                break
                
            elif len(cmd) == 1 and cmd[0] in ("quit", "q"):
                sys.exit(0)
                
            elif len(cmd) >= 1 and cmd[0][0] == "x":
                if len(cmd[0]) > 1:
                    match = GDB_EXAMINE_REGEX.match(cmd[0])
                    if match is not None:
                        count = int(match.group(1))
                        format = match.group(2)
                        unit = match.group(3)
                else:
                    count = 1
                    format = "x"
                    unit = "w"
                    
                if len(cmd) >= 2:
                    address = int(cmd[1], 0)
                else:
                    print "you need an address"
                    continue
                    
                readable = ""
                unit_size_hex = 8
                if unit == "b":
                    unit_size_hex = 2
                    ending_address = address + count
                    data = [self.mem_read_byte(x) for x in xrange(address, ending_address)]
                    readable = "".join([chr(x) if x > 0x20 and x < 0x7F else "." for x in data])
                elif unit == "w":
                    unit_size_hex = 4
                    ending_address = address + (count * 2)
                    data = [self._read_word_from_ram(x) for x in xrange(address, ending_address, 2)]
                else:
                    print "invalid unit: %r" % unit
                    
                self.debugger_shortcut[1] = "0x%08x" % ending_address
                
                if format == "x":
                    format = "%0*x"
                else:
                    print "invalid format: %r" % format
                    continue
                    
                print "0x%08x:" % address, " ".join([(format % (unit_size_hex, item)) for item in data]), readable
                
            else:
                print "i don't know what %r is." % " ".join(cmd)
                

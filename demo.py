#!/usr/bin/env python

# Standard library imports
import sys
import array
import struct
import logging
log = logging.getLogger(__name__)

# Constants
IP_START = 0
SP_START = 0x100
SIXTY_FOUR_KB = 0x10000
WORD, LOW, HIGH = range(3)

FLAGS_BLANK = 0x0000
FLAGS_CARRY = 0x0001
FLAGS_ZERO =  0x0040
FLAGS_SIGN =  0x0080

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
    
# Classes
class Component(object):
    def __init__(self):
        self.bus = None
        
class Register(object):
    def __init__(self, initial = 0, byte_addressable = False):
        self._value = 0
        
        self.x = initial
        self.byte_addressable = byte_addressable
        
    @property
    def x(self):
        return self._value
        
    @x.setter
    def x(self, value):
        self._value = value & 0xFFFF
        
    @property
    def h(self):
        return (self._value & 0xFF00) >> 8
        
    @h.setter
    def h(self, value):
        self._value = (self._value & 0x00FF) | ((value & 0xFF) << 8)
        
    @property
    def l(self):
        return self._value & 0x00FF
        
    @l.setter
    def l(self, value):
        self._value = (self._value & 0xFF00) | (value & 0xFF)

class REGS(object):
    def __init__(self):
        self._regs = {}
        self._aliases = {}
        
    def add(self, name, reg):
        self._regs[name] = reg
        
        if reg.byte_addressable:
            self._aliases[name + "X"] = (reg, WORD)
            self._aliases[name + "L"] = (reg, LOW)
            self._aliases[name + "H"] = (reg, HIGH)
        else:
            self._aliases[name] = (reg, WORD)
            
    def __getitem__(self, key):
        reg, access = self._aliases[key]
        if access == LOW:
            return reg.l
        elif access == HIGH:
            return reg.h
        else:
            return reg.x
            
    def __setitem__(self, key, value):
        reg, access = self._aliases[key]
        if access == LOW:
            reg.l = value
        elif access == HIGH:
            reg.h = value
        else:
            reg.x = value
            
class FLAGS(object):
    def __init__(self):
        self.cf = False
        self.zf = False
        self.sf = False
        
    @property
    def value(self):
        value = FLAGS_BLANK
        if self.cf:
            value |= FLAGS_CARRY
        if self.zf:
            value |= FLAGS_ZERO
        if self.sf:
            value |= FLAGS_SIGN
        return value
        
    def set_from_value(self, value, include_cf = True):
        log.debug("Setting FLAGS from 0x%04x", value)
        if value < 0:
            value = struct.unpack("<H", struct.pack("<h", value))[0]
            log.debug("Setting FLAGS from 0x%04x", value)
            
        self.zf = value == 0
        self.sf = value & 0x8000
        if include_cf:
            self.cf = value > 0xFFFF
            
    def dump_flags(self):
        log.debug("CF=%d  ZF=%d  SF=%d", self.cf, self.zf, self.sf)
        
class CPU(Component):
    def __init__(self):
        super(CPU, self).__init__()
        self.hlt = False
        self.flags = FLAGS()
        self.regs = REGS()
        self.regs.add("IP", Register(IP_START))
        self.regs.add("SP", Register(SP_START))
        self.regs.add("A", Register(0, byte_addressable = True))
        self.regs.add("B", Register(0, byte_addressable = True))
        self.regs.add("C", Register(0, byte_addressable = True))
        self.regs.add("D", Register(0, byte_addressable = True))
        self.regs.add("DI", Register(0))
        
    def read_byte(self):
        location = self.regs["IP"]
        byte = self.mlb.ram.contents[self.regs["IP"]]
        self.regs["IP"] += 1
        log.debug("Read: 0x%02x from 0x%04x", byte, location)
        return byte
        
    def fetch(self):
        self.dump_regs()
        self.flags.dump_flags()
        
        opcode = self.read_byte()
        log.debug("Fetched opcode: 0x%02x", opcode)
        if opcode == 0xF4:
            self._hlt()
        elif opcode & 0xFC == 0x80:
            self._8x(opcode)
        elif opcode & 0xF8 == 0x40:
            self._inc(opcode)
        elif opcode & 0xF8 == 0x48:
            self._dec(opcode)
        elif opcode & 0xF8 == 0x50:
            self._push(opcode)
        elif opcode & 0xF8 == 0x58:
            self._pop(opcode)
        elif opcode == 0x74:
            self._jz()
        elif opcode == 0x75:
            self._jnz()
        elif opcode == 0xE8:
            self._call()
        elif opcode == 0xC3:
            self._ret()
        elif opcode & 0xF0 == 0xB0:
            self._mov_imm_to_reg(opcode)
        elif opcode == 0x8B:
            self._mov_ram_to_reg_16()
        elif opcode == 0x88:
            self._mov_reg_to_ram_8()
        elif opcode == 0x89:
            self._mov_reg16_to_rm16()
        elif opcode == 0x8A:
            self._mov_rm8_to_reg8()
        elif opcode == 0x31:
            self._xor_rm16_r16()
        elif opcode == 0x09:
            self._or_rm16_r16()
        elif opcode == 0x72:
            self._jc()
        elif opcode == 0x39:
            self._cmp_rm16_r16()
        elif opcode == 0x76:
            self._jna()
        elif opcode == 0x79:
            self._jns()
        elif opcode == 0x01:
            self._add_rm16_r16()
        elif opcode == 0x19:
            self._sbb_rm16_r16()
        elif opcode == 0xF9:
            self._stc()
        elif opcode == 0x90:
            self._nop()
        elif opcode == 0xE9:
            self._jmp_rel16()
        elif opcode == 0xEB:
            self._jmp_rel8()
        elif opcode == 0x29:
            self._sub_rm16_r16()
        else:
            log.error("Invalid opcode: 0x%02x", opcode)
            self._hlt()
            
    def get_modrm(self, word):
        mod, reg, rm = self.get_modrm_ex()
        
        op1 = ""
        op2 = ""
        if word == 0:
            op1 = BYTE_REG[reg]
        else:
            op1 = WORD_REG[reg]
            
        if mod == MOD_RM_IS_REG:
            if word == 0:
                op2 = BYTE_REG[rm]
            else:
                op2 = WORD_REG[rm]
            
        # print "op1 = %r" % op1
        # print "op2 = %r" % op2
        return op1, op2
        
    def get_modrm_ex(self):
        modrm = self.read_byte()
        mod = (modrm & MOD_MASK) >> MOD_SHIFT
        reg = (modrm & REG_MASK) >> REG_SHIFT
        rm = modrm & RM_MASK
        
        log.debug("mod = 0x%02X, reg = 0x%02X, rm = 0x%02X", mod, reg, rm)
        return mod, reg, rm
        
    def get_modrm_operands(self, size):
        """ Returns register, rm_type, rm_value from a MODRM byte. """
        register = None
        rm_type = UNKNOWN
        rm_value = None
        
        mod, reg, rm = self.get_modrm_ex()
        
        if size == 8:
            register = BYTE_REG[reg]
        elif size == 16:
            register = WORD_REG[reg]
            
        if mod == 0x00:
            rm_type = ADDRESS
            if rm == 0x06:
                rm_value = self.get_imm(True)
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
        
        log_line = "reg = %s" % register
        if rm_type == REGISTER:
            log_line += ", r/m = %s" % rm_value
        elif rm_type == ADDRESS:
            log_line += "r/m = 0x%04x" % rm_value
        log.debug(log_line)
            
        return register, rm_type, rm_value
        
    
        
    def get_imm(self, word):
        value = self.read_byte()
        if word:
            value |= (self.read_byte() << 8)
            # print "value = 0x%04X" % value
        # else:
            # print "value = 0x%02X" % value
            
        return value
        
    def _8x(self, opcode):
        if opcode == 0x82:
            opcode = 0x80
            
        word_reg = opcode & 0x01
        word_imm = opcode == 0x81
        sign_extend = opcode & 0x02
        
        _, op2 = self.get_modrm(word_reg)
        val1 = 0
        imm = self.get_imm(word_imm)
        val1 = self.regs[op2]
        if sign_extend and not word_imm:
            new_imm = sign_extend_byte_to_word(imm)
            log.debug("Sign extending 0x%02x to 0x%04x", imm, new_imm)
            imm = new_imm
            
        # print "val1 = 0x%04X" % val1
        # print "imm = 0x%04X" % imm
        result = val1 - imm
        
        self.flags.set_from_value(result)
        
    def _mov_imm_to_reg(self, opcode):
        word = opcode & 0x08
        if word:
            dest = WORD_REG[opcode & 0x07]
        else:
            dest = BYTE_REG[opcode & 0x07]
            
        value = self.get_imm(word)
        self.regs[dest] = value
        log.debug("MOV'd 0x%04x into %s", value, dest)
        
    def _mov_ram_to_reg_16(self):
        mod, reg, rm = self.get_modrm_ex()
        assert mod == 0x00 and rm == 0x06
        addr = self.get_imm(True)
        dest = WORD_REG[reg]
        self.regs[dest] = self._read_word_from_ram(addr)
        log.debug("MOV'd 0x%04x from 0x%04x into %s", self.regs[dest], addr, dest)
        
    def _mov_reg_to_ram_8(self):
        mod, reg, rm = self.get_modrm_ex()
        src = BYTE_REG[reg]
        assert mod == 0x00 and rm == 0x01
        addr = self.regs["BX"] + self.regs["DI"]
        self.mlb.ram.contents[addr] = self.regs[src]
        log.debug("MOV'd 0x%02x from %s into 0x%04x", self.regs[src], src, addr)
        
    def _mov_rm8_to_reg8(self):
        register, rm_type, rm_value = self.get_modrm_operands(16)
        self.regs[register] = self._get_rm16(rm_type, rm_value)
        
    def _mov_reg16_to_rm16(self):
        register, rm_type, rm_value = self.get_modrm_operands(16)
        self._set_rm16(rm_type, rm_value, self.regs[register])
        
    def _inc(self, opcode):
        dest = WORD_REG[opcode & 0x07]
        self.regs[dest] += 1
        self.flags.set_from_value(self.regs[dest], include_cf = False)
        log.debug("INC'd %s to 0x%04x", dest, self.regs[dest])
        
    def _dec(self, opcode):
        dest = WORD_REG[opcode & 0x07]
        self.regs[dest] -= 1
        self.flags.set_from_value(self.regs[dest], include_cf = False)
        log.debug("DEC'd %s to 0x%04x", dest, self.regs[dest])
        
    def _push(self, opcode):
        src = WORD_REG[opcode & 0x07]
        value = self.regs[src]
        self.__push(value)
        log.debug("PUSH'd 0x%04x from %s", value, src)
        
    def _pop(self, opcode):
        dest = WORD_REG[opcode & 0x07]
        self.regs[dest] = self.__pop()
        log.debug("POP'd 0x%04x into %s", self.regs[dest], dest)
        
    def __push(self, value):
        self.regs["SP"] -= 2
        self._write_word_to_ram(self.regs["SP"], value)
        
    def __pop(self):
        value = self._read_word_from_ram(self.regs["SP"])
        self.regs["SP"] += 2
        return value
        
    def _jc(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_imm(False)))[0]
        if self.flags.cf:
            self.regs["IP"] += distance
            log.debug("JC incremented IP by 0x%04x to 0x%04x", distance, self.regs["IP"])
        else:
            log.debug("JC was skipped.")
            
    def _jz(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_imm(False)))[0]
        if self.flags.zf:
            self.regs["IP"] += distance
            log.debug("JZ incremented IP by 0x%04x to 0x%04x", distance, self.regs["IP"])
        else:
            log.debug("JZ was skipped.")
            
    def _jnz(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_imm(False)))[0]
        if self.flags.zf:
            log.debug("JNZ/JNE was skipped.")
        else:
            self.regs["IP"] += distance
            log.debug("JNZ/JNE incremented IP by 0x%04x to 0x%04x", distance, self.regs["IP"])
            
    def _jna(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_imm(False)))[0]
        # HACK
        # if self.flags.zf or self.flags.cf:
            # log.debug("JNA was skipped.")
        # else:
            # self.regs["IP"] += distance
            # log.debug("JNA incremented IP by 0x%04x to 0x%04x", distance, self.regs["IP"])
            
    def _jns(self):
        distance = struct.unpack("<b", struct.pack("<B", self.get_imm(False)))[0]
        if self.flags.sf:
            log.debug("JNS was skipped.")
        else:
            self.regs["IP"] += distance
            log.debug("JNS incremented IP by 0x%04x to 0x%04x", distance, self.regs["IP"])
            
    def _call(self):
        offset = self.get_imm(True)
        self.__push(self.regs["IP"])
        self.regs["IP"] += offset
        log.debug("CALL incremented IP by 0x%04x to 0x%04x", offset, self.regs["IP"])
        
    def _ret(self):
        self.regs["IP"] = self.__pop()
        log.debug("RET back to 0x%04x", self.regs["IP"])
        
    def _xor_rm16_r16(self):
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self._get_rm16(rm_type, rm_value)
        op2 = self.regs[register]
        op1 = op1 ^ op2
        self.flags.set_from_value(op1, include_cf = True)
        self._set_rm16(rm_type, rm_value, op1 & 0xFFFF)
        
    def _or_rm16_r16(self):
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self._get_rm16(rm_type, rm_value)
        op2 = self.regs[register]
        op1 = op1 | op2
        self.flags.set_from_value(op1, include_cf = True)
        self._set_rm16(rm_type, rm_value, op1 & 0xFFFF)
        
    def _add_rm16_r16(self):
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self._get_rm16(rm_type, rm_value)
        op2 = self.regs[register]
        op1 = op1 + op2
        self.flags.set_from_value(op1, include_cf = True)
        self._set_rm16(rm_type, rm_value, op1 & 0xFFFF)
        
    def _sbb_rm16_r16(self):
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self._get_rm16(rm_type, rm_value)
        op2 = self.regs[register]
        op1 = op1 - op2
        # HACK
        # if self.flags.cf:
            # op1 -= 1
        self.flags.set_from_value(op1, include_cf = True)
        self._set_rm16(rm_type, rm_value, op1 & 0xFFFF)
        
    def _sub_rm16_r16(self):
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self._get_rm16(rm_type, rm_value)
        op2 = self.regs[register]
        op1 = op1 - op2
        self.flags.set_from_value(op1, include_cf = True)
        self._set_rm16(rm_type, rm_value, op1 & 0xFFFF)
        
    def _cmp_rm16_r16(self):
        register, rm_type, rm_value = self.get_modrm_operands(16)
        op1 = self._get_rm16(rm_type, rm_value)
        op2 = self.regs[register]
        print op1
        print op2
        value = op1 - op2
        print value
        self.flags.set_from_value(value, include_cf = True)
        
    def _stc(self):
        self.flags.cf = True
        
    def _nop(self):
        log.critical("NOP")
        
    def _hlt(self):
        log.critical("HLT encountered!")
        self.hlt = True
        
    def _jmp_rel16(self):
        offset = self.get_imm(True)
        self.regs["IP"] += offset
        log.debug("JMP incremented IP by 0x%04x to 0x%04x", offset, self.regs["IP"])
        
    def _jmp_rel8(self):
        offset = self.get_imm(False)
        self.regs["IP"] += offset
        log.debug("JMP incremented IP by 0x%04x to 0x%04x", offset, self.regs["IP"])
        
    def _write_word_to_ram(self, address, value):
        self.mlb.ram.contents[address], self.mlb.ram.contents[address + 1] = word_to_bytes_le(value)
        
    def _read_word_from_ram(self, address):
        return bytes_to_word_le((self.mlb.ram.contents[address], self.mlb.ram.contents[address + 1]))
        
    def _get_rm16(self, rm_type, rm_value):
        if rm_type == REGISTER:
            return self.regs[rm_value]
        elif rm_type == ADDRESS:
            return self._read_word_from_ram(rm_value)
            
    def _set_rm16(self, rm_type, rm_value, value):
        if rm_type == REGISTER:
            self.regs[rm_value] = value
        elif rm_type == ADDRESS:
            self._write_word_to_ram(rm_value, value)
            
    def dump_regs(self):
        regs = ("AX", "BX", "CX", "DX")
        log.debug("  ".join(["%s = 0x%04x" % (reg, self.regs[reg]) for reg in regs]))
        
class RAM(object):
    def __init__(self, size):
        super(RAM, self).__init__()
        self.contents = array.array("B", (0,) * size)
        
    def load_from_file(self, filename, address):
        with open(filename, "rb") as fileptr:
            data = fileptr.read()
            
        for index, char in enumerate(data, start = address):
            self.contents[index] = ord(char)
            
class Bus(object):
    def __init__(self):
        self.items = {}
        
        
class BusComponent(object):
    def __init__(self, address, length):
        self.address = address
        self.length = length
        self.bus = None
        
class MainLogicBoard(object):
    def __init__(self, cpu, ram):
        self.cpu = cpu
        self.cpu.mlb = self
        
        self.ram = ram
        
    def run(self):
        while not self.cpu.hlt:
            log.debug("")
            self.dump_screen()
            # import time
            # time.sleep(0.05)
            self.cpu.fetch()
            
    def dump_screen(self):
        screen = "\r\n+" + "-" * 80 + "+\r\n"
        for row in xrange(25):
            screen += "|"
            for col in xrange(80):
                screen += chr(self.ram.contents[0x8000 + (row * 80) + col])
            screen += "|\r\n"
        screen += "+" + "-" * 80 + "+\r\n"
        log.debug(screen)
        
# Main application
def main():
    logging.basicConfig(format = "%(asctime)s %(message)s", level = logging.DEBUG)
    log.info("PyXT oh hai")
    
    cpu = CPU()
    ram = RAM(SIXTY_FOUR_KB)
    ram.load_from_file(sys.argv[1], 0)
    mlb = MainLogicBoard(cpu, ram)
    mlb.run()
    
    log.info("PyXT kthxbai")
    
if __name__ == "__main__":
    main()
    
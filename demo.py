#!/usr/bin/env python

# Standard library imports
import sys
import array
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

OP_MASK = 0xFC
D_MASK =  0x02
W_MASK =  0x01

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
        self.zf = value == 0
        self.sf = value < 0
        if include_cf:
            self.cf = value > 0xFFFF
            
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
        
    def read_byte(self):
        byte = self.mlb.ram.contents[self.regs["IP"]]
        self.regs["IP"] += 1
        return byte
        
    def fetch(self):
        opcode = self.read_byte()
        log.debug("Fetched opcode: 0x%02X", opcode)
        if opcode == 0xF4:
            self._hlt()
        elif opcode & OP_MASK == 0x80:
            self._8x(opcode)
        elif opcode & 0xF8 == 0x40:
            self._inc(opcode)
        elif opcode & 0xF8 == 0x48:
            self._dec(opcode)
        elif opcode == 0x74:
            self._jz()
        elif opcode & 0xF0 == 0xB0:
            self._mov_imm_to_reg(opcode)
        else:
            log.error("Invalid opcode: 0x%02X", opcode)
            self._hlt()
            
    def get_modrm(self, d, word):
        modrm = self.read_byte()
        # print "modrm = 0x%02X" % modrm
        
        mod = (modrm & MOD_MASK) >> MOD_SHIFT
        # print "mod = 0x%02X" % mod
        
        reg = (modrm & REG_MASK) >> REG_SHIFT
        # print "reg = 0x%02X" % reg
        
        rm = modrm & RM_MASK
        # print "rm =  0x%02X" % rm
        
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
        
    def get_imm(self, word):
        value = self.read_byte()
        if word:
            value |= (self.read_byte() << 8)
            # print "value = 0x%04X" % value
        # else:
            # print "value = 0x%02X" % value
            
        return value
        
    def _8x(self, opcode):
        d = 1
        word = opcode & W_MASK
        _, op2 = self.get_modrm(d, word)
        val1 = 0
        imm = self.get_imm(word)
        val1 = self.regs[op2]
        
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
        
    def _jz(self):
        distance = self.get_imm(False)
        if self.flags.zf:
            self.regs["IP"] += distance
            log.debug("JZ incremented IP by 0x%04x to 0x%04x", distance, self.regs["IP"])
        else:
            log.debug("JZ was skipped.")
            
    def _hlt(self):
        log.critical("HLT encountered!")
        self.hlt = True
        
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
            self.cpu.fetch()
            
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
    
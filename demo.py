#!/usr/bin/env python

# Standard library imports
import sys
import array

# Constants
IP_START = 0
SP_START = 0x100
SIXTY_FOUR_KB = 0x10000

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
        self.mlb = None
        
class REG(object):
    def __init__(self, initial = 0):
        self._value = initial & 0xFFFF
        
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
    def __init__(self, regs):
        self._regs = regs
        
    def __setitem__(self, key, value):
        
        
class FLAGS(object):
    def __init__(self):
        self.cf = False
        self.zf = False
        self.sf = False
        
    @property
    def value(self):
        value = FLAGS_BLANK
        if self.cf: value |= FLAGS_CARRY
        if self.zf: value |= FLAGS_ZERO
        if self.sf: value |= FLAGS_SIGN
        return value
        
class CPU(object):
    def __init__(self):
        super(CPU, self).__init__()
        # self.ip = IP_START
        # self.sp = SP_START
        self.flags = FLAGS()
        self.hlt = False
        self.regs = {
            "IP" : REG(IP_START),
            "SP" : REG(SP_START),
            "A" : REG(0),
            "B" : REG(0),
            "C" : REG(0),
            "D" : REG(0),
        }
        
    def read_byte(self):
        byte = self.mlb.ram.contents[self.regs["IP"].x]
        self.regs["IP"].x += 1
        return byte
        
    def fetch(self):
        opcode = self.read_byte()
        print "opcode = 0x%02X" % opcode
        if opcode == 0xF4:
            self._hlt()
        elif opcode & OP_MASK == 0x80:
            self._8x(opcode)
        elif opcode == 0x74:
            self._jz()
        elif opcode & 0xF0 == 0xB0:
            self._mov_imm_to_reg(opcode)
        else:
            print "INVALID OPCODE"
            self._hlt()
            
    def get_modrm(self, d, word):
        modrm = self.read_byte()
        print "modrm = 0x%02X" % modrm
        
        mod = (modrm & MOD_MASK) >> MOD_SHIFT
        print "mod = 0x%02X" % mod
        
        reg = (modrm & REG_MASK) >> REG_SHIFT
        print "reg = 0x%02X" % reg
        
        rm = modrm & RM_MASK
        print "rm =  0x%02X" % rm
        
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
            
        print "op1 = %r" % op1
        print "op2 = %r" % op2
        return op1, op2
        
    def get_imm(self, word):
        value = self.read_byte()
        if word:
            value |= (self.read_byte() << 8)
            print "value = 0x%04X" % value
        else:
            print "value = 0x%02X" % value
            
        return value
        
    def _8x(self, opcode):
        d = 1
        word = opcode & W_MASK
        _, op2 = self.get_modrm(d, word)
        val1 = 0
        imm = self.get_imm(word)
        if word:
            val1 = self.regs[op2].x
        else:
            val1 = self.regs[op2].l
            
        result = val1 - imm
        self.flags.zf = result == 0
        self.flags.sf = result < 0
        self.flags.cf = result > 0xFFFF
        
    def _mov_imm_to_reg(self, opcode):
        print "MOV"
        word = opcode & 0x08
        if word:
            dest = WORD_REG[opcode & 0x07]
            value = self.get_imm(word)
            self.regs[dest].x = value
        else:
            dest = BYTE_REG[opcode & 0x07]
            value = self.get_imm(word)
            if dest[0] in self.regs:
                if dest[1] == "H":
                    self.regs[dest[0]].h = value
                else:
                    self.regs[dest[0]].l = value
            else:
                print "WTF"
                self._hlt()
                
    def _jz(self):
        distance = self.get_imm(False)
        self.regs["IP"].x += distance
        
    def _hlt(self):
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
            
class MainLogicBoard(object):
    def __init__(self, cpu, ram):
        self.cpu = cpu
        self.cpu.mlb = self
        
        self.ram = ram
        self.ram.mlb = self
        
    def run(self):
        while not self.cpu.hlt:
            self.cpu.fetch()
            
        print "hlt"
        
# Main application
def main():
    print "PyXT oh hai"
    
    cpu = CPU()
    ram = RAM(SIXTY_FOUR_KB)
    ram.load_from_file(sys.argv[1], 0)
    mlb = MainLogicBoard(cpu, ram)
    mlb.run()
    
if __name__ == "__main__":
    main()
    
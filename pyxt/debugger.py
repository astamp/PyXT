"""
pyxt.debugger - Debugger module for PyXT.
"""

# Standard library imports
import re
import sys

# PyXT imports
from pyxt.helpers import segment_offset_to_address

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants
GDB_EXAMINE_REGEX = re.compile("^x\\/(\\d+)([xduotacfs])([bwd])$")

# Classes
class Debugger(object):
    """ Interactive debugger for PyXT. """
    def __init__(self, cpu, bus):
        self.cpu = cpu
        self.bus = bus
        
        self.breakpoints = []
        self.single_step = False
        self.debugger_shortcut = []
        self.dump_enabled = False
        
    # ********** Debugger functions. **********
    def fetch(self):
        """ Wraps the CPU fetch() to print info and/or pause execution. """
        if self.dump_enabled:
            self.dump_all()
            
        if self.should_break():
            self.enter_debugger()
            
        self.cpu.fetch()
        
    def dump_all(self, level = logging.DEBUG):
        """ Dump all registers and flags. """
        self.dump_regs(level, "AX", "BX", "CX", "DX")
        self.dump_regs(level, "BP", "SP", "SI", "DI")
        self.dump_regs(level, "SS", "DS", "ES")
        self.dump_regs(level, "CS", "IP")
        self.dump_flags(level)
        
    def dump_regs(self, level, *regs):
        """ Dump a list of CPU registers to the log. """
        log.log(level, "  ".join(["%s = 0x%04x" % (reg, self.cpu.regs[reg]) for reg in regs]))
        
    def dump_flags(self, level):
        """ Dump the CPU FLAGS register to the log. """
        log.log(
            level,
            "FLAGS= 0x%04x cf=%d, zf=%d, sf=%d, df=%d",
            self.cpu.flags.value,
            self.cpu.flags.carry, self.cpu.flags.zero,
            self.cpu.flags.sign, self.cpu.flags.direction,
        )
        
    def should_break(self):
        """ Return True if we should break now. """
        return self.single_step or (self.cpu.regs.CS, self.cpu.regs.IP) in self.breakpoints
        
    def peek_instruction_byte(self):
        """ Return at CS:IP, but do not increment IP. """
        return self.bus.mem_read_byte(segment_offset_to_address(self.cpu.regs.CS, self.cpu.regs.IP))
        
    def enter_debugger(self):
        while True:
            print "\nNext instruction: 0x%02x" % self.peek_instruction_byte()
            if len(self.debugger_shortcut) != 0:
                print "[%s] >" % " ".join(self.debugger_shortcut),
            else:
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
                
            elif len(cmd) == 1 and cmd[0] in ("dump", "d"):
                self.dump_all()
                
            elif len(cmd) >= 1 and cmd[0] == "set":
                self.debugger_shortcut = []
                if len(cmd) == 2 and cmd[1] == "dump":
                    self.dump_enabled = True
                    self.dump_all()
                    
            elif len(cmd) >= 1 and cmd[0] == "clear":
                self.debugger_shortcut = []
                if len(cmd) == 2 and cmd[1] == "dump":
                    self.dump_enabled = False
                
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
                    data = [self.bus.mem_read_byte(x) for x in xrange(address, ending_address)]
                    readable = "".join([chr(x) if x > 0x20 and x < 0x7F else "." for x in data])
                elif unit == "w":
                    unit_size_hex = 4
                    ending_address = address + (count * 2)
                    data = [self.bus.mem_read_word(x) for x in xrange(address, ending_address, 2)]
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
                

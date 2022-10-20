"""
pyxt.debugger - Debugger module for PyXT.
"""

from __future__ import print_function

# Standard library imports
import re
import sys
from collections import Counter

# Six imports
from six.moves import range, input # pylint: disable=redefined-builtin

# PyXT imports
from pyxt.helpers import segment_offset_to_address

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants
GDB_EXAMINE_REGEX = re.compile("^x\\/(\\d+)([xduotacfs])([bwd])$")
RETURN_OPCODES = (
    0xCF, # IRET
    0xC3, # RET
    0xC2, # RET imm16
    0xCB, # RETF
    0xCA, # RETF imm16
)

# Classes
class Debugger(object):
    """ Interactive debugger for PyXT. """
    def __init__(self, cpu, bus):
        self.cpu = cpu
        self.bus = bus
        self.bus.debugger = self
        
        self.breakpoints = []
        self.single_step = False
        self.debugger_shortcut = []
        self.dump_enabled = False
        self.step_out = False
        
        self.location_counter = Counter()
        self.instruction_counter = Counter()
        self.trace_fileptr = None
        
    # ********** Debugger functions. **********
    def fetch(self):
        """ Wraps the CPU fetch() to print info and/or pause execution. """
        if self.dump_enabled:
            self.dump_all()
            
        next_instruction = self.peek_instruction_byte()
        if self.dump_enabled:
            log.debug("next_instruction = 0x%02x", next_instruction)
            
        if self.trace_fileptr:
            if self.cpu.regs.CS >= 0xF000:
                self.trace_fileptr.write("\t".join([
                    "%04x:%04x" % (self.cpu.regs.CS, self.cpu.regs.IP),
                    "0x%02x" % self.cpu.regs.AH,
                    "0x%02x" % self.cpu.regs.AL,
                    "%s" % (chr(self.cpu.regs.AL) if self.cpu.regs.AL >= 0x20 and self.cpu.regs.AL < 0x7F else "???"),
                    "0x%04x" % self.cpu.regs.BX,
                    "0x%04x" % self.cpu.regs.CX,
                    "0x%04x" % self.cpu.regs.DX,
                    "0x%04x" % self.cpu.regs.SI,
                    "0x%04x" % self.cpu.regs.DI,
                    "0x%04x" % self.cpu.regs.CS,
                    "0x%04x" % self.cpu.regs.DS,
                    "0x%04x" % self.cpu.regs.ES,
                ]) + "\r\n")
                
        # Check if we are trying to step out of a CALL-ed function.
        if self.step_out:
            if next_instruction in RETURN_OPCODES:
                log.debug("Return detected!")
                # At this point we want to drop to the debugger and not step out any longer.
                self.step_out = False
                self.single_step = True
                
        if self.should_break():
            self.enter_debugger()
            
        self.location_counter.update({(self.cpu.regs.CS, self.cpu.regs.IP) : 1})
        self.instruction_counter.update({next_instruction : 1})
        self.cpu.fetch()
        
    def dump_all(self, level = logging.DEBUG):
        """ Dump all registers and flags. """
        self.dump_regs(level, "AX", "BX", "CX", "DX")
        self.dump_reg_pair(level, "CS", "IP")
        self.dump_reg_pair(level, "DS", "SI")
        self.dump_reg_pair(level, "ES", "DI")
        self.dump_reg_pair(level, "SS", "SP")
        self.dump_reg_pair(level, "SS", "BP")
        self.dump_flags(level)
        
    def dump_regs(self, level, *regs):
        """ Dump a list of CPU registers to the log. """
        log.log(level, "  ".join(["%s = 0x%04x" % (reg, self.cpu.regs[reg]) for reg in regs]))
        
    def dump_reg_pair(self, level, segment, offset):
        """ Dump a segment:offset register pair to the log. """
        log.log(level, "%s:%s = %04x:%04x (0x%05x)",
                segment, offset, self.cpu.regs[segment], self.cpu.regs[offset],
                segment_offset_to_address(self.cpu.regs[segment], self.cpu.regs[offset]),
                )
        
    def dump_flags(self, level):
        """ Dump the CPU FLAGS register to the log. """
        log.log(
            level,
            "FLAGS = 0x%04x [%s%s%s%s%s%s%s%s%s]", self.cpu.flags.value,
            "O" if self.cpu.flags.overflow else "o",
            "D" if self.cpu.flags.direction else "d",
            "I" if self.cpu.flags.interrupt_enable else "i",
            "T" if self.cpu.flags.trap else "t",
            "S" if self.cpu.flags.sign else "s",
            "Z" if self.cpu.flags.zero else "z",
            "A" if self.cpu.flags.adjust else "a",
            "P" if self.cpu.flags.parity else "p",
            "C" if self.cpu.flags.carry else "c",
        )
        
    def dump_stack(self, depth):
        """ Dump the stack. """
        for temp_sp in range(self.cpu.regs.SP, self.cpu.regs.SP + (depth * 2), 2):
            value = self.bus.mem_read_word(segment_offset_to_address(self.cpu.regs.SS, temp_sp))
            log.debug("SP=%04x: %04x", temp_sp, value)
            
    def should_break(self):
        """ Return True if we should break now. """
        return self.single_step or (self.cpu.regs.CS, self.cpu.regs.IP) in self.breakpoints
        
    def peek_instruction_byte(self):
        """ Return at CS:IP, but do not increment IP. """
        return self.bus.mem_read_byte(segment_offset_to_address(self.cpu.regs.CS, self.cpu.regs.IP))
        
    def break_signal(self, _signum, _frame):
        """ Control-C handler to enter single-step mode. """
        print("Control-C")
        self.single_step = True
        
    def enter_debugger(self):
        """ Interactive debugger menu. """
        while True:
            print("\nNext instruction: 0x%02x" % self.peek_instruction_byte())
            if len(self.debugger_shortcut) != 0:
                print("[%s] >" % " ".join(self.debugger_shortcut), end=" ")
            else:
                print(">", end=" ")
                
            try:
                cmd = input().lower().split()
            except KeyboardInterrupt:
                print("^C")
                continue
                
            try:
                resume = self.process_command(cmd)
                if resume:
                    break
            except Exception as err:
                log.exception("Unhandled exception processing: %r" % cmd)
                
    def process_command(self, cmd):
        """ Actually process the command from the user. """
        if len(cmd) == 0 and len(self.debugger_shortcut) != 0:
            cmd = self.debugger_shortcut
            print("Using: %s" % " ".join(cmd))
        else:
            self.debugger_shortcut = cmd
            
        if len(cmd) == 0:
            return False
            
        if len(cmd) == 1 and cmd[0] in ("continue", "c"):
            self.single_step = False
            return True
            
        elif len(cmd) == 1 and cmd[0] in ("step", "s"):
            self.single_step = True
            return True
            
        elif len(cmd) == 1 and cmd[0] in ("quit", "q"):
            sys.exit(0)
            
        elif len(cmd) == 1 and cmd[0] in ("dump", "d"):
            self.dump_all()
            
        elif len(cmd) == 2 and cmd[0] in ("stack", "st"):
            self.dump_stack(int(cmd[1]))
            
        elif len(cmd) == 2 and cmd[0] in ("key", "scancode"):
            self.bus.io_decoder[0x060].key_pressed((int(cmd[1], 0), ))
            
        elif len(cmd) == 1 and cmd[0] == "ram-dump":
            with open("ram-dump.bin", "wb") as fileptr:
                for index in xrange(10):
                    fileptr.write(self.bus.devices[index].contents.tostring())
                    
        elif len(cmd) == 2 and cmd[0] == "trace":
            if cmd[1] == "on" and self.trace_fileptr is None:
                self.trace_fileptr = open("trace.log", "wb")
            elif cmd[1] == "off" and self.trace_fileptr is not None:
                self.trace_fileptr.close()
                self.trace_fileptr = None
            else:
                print("Trace is %s." % ("off" if self.trace_fileptr is None else "on"))
                
        elif len(cmd) == 1 and cmd[0] in ("step-out", "out"):
            # Set the step out flag and disable single stepping so we run to the next return.
            self.step_out = True
            self.single_step = False
            return True
            
        elif len(cmd) == 2 and cmd[0] in ("lc", "location-counter"):
            if cmd[1] == "clear":
                self.location_counter.clear()
            else:
                for location, count in self.location_counter.most_common(int(cmd[1])):
                    cs, ip = location
                    print("location = %04x:%04x, count = %d" % (cs, ip, count))
                
        elif len(cmd) == 2 and cmd[0] in ("ic", "instruction-counter"):
            if cmd[1] == "clear":
                self.instruction_counter.clear()
            else:
                for instruction, count in self.instruction_counter.most_common(int(cmd[1])):
                    print("instruction = 0x%02x, count = %d" % (instruction, count))
                
        elif len(cmd) == 1 and cmd[0] in ("vector", "vt"):
            for vector in range(0, 256):
                ip = self.bus.mem_read_word(vector * 4)
                cs = self.bus.mem_read_word((vector * 4) + 2)
                print("Vector 0x%02x - %04x:%04x" % (vector, cs, ip))
                
        elif len(cmd) >= 1 and cmd[0] == "info":
            self.debugger_shortcut = []
            if len(cmd) == 2 and cmd[1] in ("breakpoints", "break"):
                print("Breakpoints:")
                for index, breakpoint in enumerate(self.breakpoints):
                    print("  %04x:%04x" % breakpoint)
                    
        elif len(cmd) == 2 and cmd[0] == "break":
            self.debugger_shortcut = []
            (cs, ip) = cmd[1].split(":")
            self.breakpoints.append((int(cs, 16), int(ip, 16)))
            
        elif len(cmd) == 2 and cmd[0] == "clear":
            self.debugger_shortcut = []
            if cmd[1] == "all":
                self.breakpoints = []
            elif cmd[1] == "dump":
                self.dump_enabled = False
            else:
                (cs, ip) = cmd[1].split(":")
                self.breakpoints.remove((int(cs, 16), int(ip, 16)))
                    
        elif len(cmd) >= 1 and cmd[0] == "set":
            self.debugger_shortcut = []
            if len(cmd) == 2 and cmd[1] == "dump":
                self.dump_enabled = True
                self.dump_all()
                
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
                print("you need an address")
                return False
                
            readable = ""
            unit_size_hex = 8
            if unit == "b":
                unit_size_hex = 2
                ending_address = address + count
                data = [self.bus.mem_read_byte(x) for x in range(address, ending_address)]
                readable = "".join([chr(x) if x > 0x20 and x < 0x7F else "." for x in data])
            elif unit == "w":
                unit_size_hex = 4
                ending_address = address + (count * 2)
                data = [self.bus.mem_read_word(x) for x in range(address, ending_address, 2)]
            else:
                print("invalid unit: %r" % unit)
                
            self.debugger_shortcut[1] = "0x%08x" % ending_address
            
            if format == "x":
                format = "%0*x"
            else:
                print("invalid format: %r" % format)
                return False
                
            print("0x%08x:" % address, " ".join([(format % (unit_size_hex, item)) for item in data]), readable)
            
        else:
            print("i don't know what %r is." % " ".join(cmd))
            

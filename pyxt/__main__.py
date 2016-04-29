#!/usr/bin/env python

"""
pyxt - Main application for running a demo PyXT system.
"""

# Standard library imports
import os
import signal
from pprint import pprint
from optparse import OptionParser

# PyXT imports
from pyxt.constants import SIXTY_FOUR_KB, BIOS_LOCATION
from pyxt.cpu import CPU
from pyxt.debugger import Debugger
from pyxt.bus import SystemBus
from pyxt.memory import RAM, ROM
from pyxt.mda import CharacterGeneratorMDA_CGA_ROM, MonochromeDisplayAdapter, MDA_START_ADDRESS
from pyxt.ui import PygameManager

from pyxt.dma import DmaController
from pyxt.nmi_mask import NMIMaskRegister
from pyxt.ppi import *
from pyxt.onboard import ProgrammableInterruptController, ProgrammableIntervalTimer

# Logging setup
import logging
log = logging.getLogger(__name__)

# Constants
DEFAULT_DIP_SWITCHES = (SWITCHES_NORMAL_BOOT | SWITCHES_MEMORY_BANKS_FOUR | SWITCHES_VIDEO_MDA_HERC | SWITCHES_DISKETTES_ONE)

# Functions
def parse_cmdline():
    """ Parse the command line arguments. """
    parser = OptionParser()
    parser.add_option("--debug", action = "store_true", dest = "debug",
                      help = "Enable DEBUG log level.")
    parser.add_option("--bios", action = "store", dest = "bios",
                      help = "ROM BIOS image to load at 0xF0000.")
    parser.add_option("--mda-rom", action = "store", dest = "mda_rom",
                      help = "MDA ROM to use for the virtual MDA card.")
    parser.add_option("--dip-switches", action = "store", type = "int", dest = "dip_switches",
                      help = "DIP switch byte to use.", default = DEFAULT_DIP_SWITCHES)
    parser.add_option("--skip-memory-test", action = "store_true", dest = "skip_memory_test",
                      help = "Set the flag to skip the POST memory test.")
    return parser.parse_args()
    
def main():
    """ Main application that runs the PyXT machine. """
    options, args = parse_cmdline()
    
    log_level = logging.DEBUG if options.debug else logging.INFO
    logging.basicConfig(format = "%(asctime)s.%(msecs)03d %(name)s(%(levelname)s): %(message)s", datefmt="%m/%d %H:%M:%S", level = log_level)
    log.info("PyXT oh hai")
    
    bus = SystemBus()
    
    # 640KB OK
    for index in xrange(10):
        bus.install_device(index * SIXTY_FOUR_KB, RAM(SIXTY_FOUR_KB))
        
    # ROM BIOS
    if options.bios:
        bus.install_device(BIOS_LOCATION, ROM(SIXTY_FOUR_KB, init_file = options.bios))
        
    # Set the flag to skip the memory test if desired.
    # See the POST section here: http://www.bioscentral.com/misc/biosbasics.htm
    if options.skip_memory_test:
        bus.mem_write_word(0x0472, 0x1234)
        
    # Other onboard hardware devices.
    char_generator = CharacterGeneratorMDA_CGA_ROM(options.mda_rom, CharacterGeneratorMDA_CGA_ROM.MDA_FONT)
    mda_card = MonochromeDisplayAdapter(char_generator, randomize = True)
    bus.install_device(MDA_START_ADDRESS, mda_card)
    
    bus.install_device(None, DmaController(0x0000))
    nmi_mask = NMIMaskRegister(0x0A0)
    bus.install_device(None, nmi_mask)
    bus.install_device(None, ProgrammableInterruptController(0x020))
    
    pit = ProgrammableIntervalTimer(0x0040)
    pit.channels[0].gate = True
    pit.channels[1].gate = True
    pit.channels[2].gate = True
    bus.install_device(None, pit)
    
    ppi = ProgrammablePeripheralInterface(0x060)
    ppi.dip_switches = options.dip_switches
    log.info("dip_switches = 0x%02x", ppi.dip_switches)
    bus.install_device(None, ppi)
    
    if options.debug:
        print "\nSYSTEM BUS:"
        pprint(bus.devices)
        pprint(bus.io_decoder)
    
    cpu = CPU()
    cpu.install_bus(bus)
    
    debugger = Debugger(cpu, bus)
    for breakpoint in args:
        (cs, ip) = breakpoint.split(":")
        debugger.breakpoints.append((int(cs, 16), int(ip, 16)))
        
    if options.debug:
        signal.signal(signal.SIGINT, debugger.break_signal)
    
    cpu_or_debugger = debugger if options.debug else cpu
    
    pygame_manager = PygameManager(ppi, mda_card)
    
    try:
        while not cpu.hlt:
            pygame_manager.poll()
            pit.clock()
            cpu_or_debugger.fetch()
            
    except Exception:
        debugger.dump_all(logging.ERROR)
        log.exception("Unhandled exception at CS:IP 0x%04x:0x%04x", cpu.regs.CS, cpu.regs.IP)
        
        # Stop in the debugger one last time so we can inspect the state of the system.
        if options.debug:
            debugger.enter_debugger()
            
if __name__ == "__main__":
    if os.environ.get("PYXT_PROFILING"):
        import cProfile
        cProfile.run("main()", sort = "time")
    else:
        main()
    
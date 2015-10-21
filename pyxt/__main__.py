#!/usr/bin/env python

"""
pyxt - Main application for running a demo PyXT system.
"""

# Standard library imports
from pprint import pprint
from optparse import OptionParser

# PyXT imports
from pyxt.constants import *
from pyxt.cpu import CPU
from pyxt.iobus import *
from pyxt.bus import *

# Logging setup
import logging
log = logging.getLogger(__name__)

# Functions
def parse_cmdline():
    parser = OptionParser()
    parser.add_option("--bios", action = "store", dest = "bios", help = "ROM BIOS image to load at 0xF0000.")
    return parser.parse_args()
    
def main():
    logging.basicConfig(format = "%(asctime)s %(message)s", level = logging.DEBUG)
    log.info("PyXT oh hai")
    
    options, args = parse_cmdline()
    
    bus = SystemBus()
    
    # 640KB OK
    for x in xrange(10):
        bus.install_device(x * SIXTY_FOUR_KB, RAM(SIXTY_FOUR_KB))
        
    # ROM BIOS
    if options.bios:
        bus.install_device(BIOS_LOCATION, ROM(SIXTY_FOUR_KB, init_file = options.bios))
        
    print "\nSYSTEM BUS:"
    pprint(bus.devices)
    
    io_bus = InputOutputBus()
    io_bus.install_device(ProgrammableInterruptController(0x00A0))
    io_bus.install_device(ProgrammableIntervalTimer(0x0040))
    
    print "\nI/O BUS:"
    pprint(io_bus.devices)
    
    cpu = CPU()
    cpu.bus = bus
    cpu.io_bus = io_bus
    
    while not cpu.hlt:
        log.debug("")
        cpu.fetch()

if __name__ == "__main__":
    main()
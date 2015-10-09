#!/usr/bin/env python

"""
pyxt - Main application for running a demo PyXT system.
"""

# Standard library imports
from pprint import pprint
from optparse import OptionParser

# PyXT imports
from pyxt.constants import *
from pyxt.bus import SystemBus, RAM, ROM

# Constants

# Functions
def parse_cmdline():
    parser = OptionParser()
    parser.add_option("--bios", action = "store", dest = "bios", help = "ROM BIOS image to load at 0xF0000.")
    return parser.parse_args()
    
def main():
    options, args = parse_cmdline()
    
    bus = SystemBus()
    
    # 640KB OK
    for x in xrange(10):
        bus.install_device(x * SIXTY_FOUR_KB, RAM(SIXTY_FOUR_KB))
        
    # ROM BIOS
    if options.bios:
        bus.install_device(BIOS_LOCATION, ROM(SIXTY_FOUR_KB, init_file = options.bios))
        
    pprint(bus.devices)

if __name__ == "__main__":
    main()
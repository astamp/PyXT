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
from pyxt.bus import SystemBus
from pyxt.memory import RAM, ROM
from pyxt.mda import CharacterGeneratorMDA_CGA_ROM, MonochromeDisplayAdapter, MDA_START_ADDRESS

from pyxt.onboard import ProgrammableInterruptController, ProgrammableIntervalTimer

# Logging setup
import logging
log = logging.getLogger(__name__)

# Functions
def parse_cmdline():
    parser = OptionParser()
    parser.add_option("--bios", action = "store", dest = "bios", help = "ROM BIOS image to load at 0xF0000.")
    parser.add_option("--mda-rom", action = "store", dest = "mda_rom", help = "MDA ROM to use for the virtual MDA card.")
    return parser.parse_args()
    
def main():
    logging.basicConfig(format = "%(asctime)s %(message)s", level = logging.DEBUG)
    log.info("PyXT oh hai")
    
    options, args = parse_cmdline()
    
    bus = SystemBus()
    
    # 640KB OK
    for index in xrange(10):
        bus.install_device(index * SIXTY_FOUR_KB, RAM(SIXTY_FOUR_KB))
        
    # ROM BIOS
    if options.bios:
        bus.install_device(BIOS_LOCATION, ROM(SIXTY_FOUR_KB, init_file = options.bios))
        
    # Other onboard hardware devices.
    char_generator = CharacterGeneratorMDA_CGA_ROM(options.mda_rom, CharacterGeneratorMDA_CGA_ROM.MDA_FONT)
    mda_card = MonochromeDisplayAdapter(char_generator)
    # mda_card.reset()
    bus.install_device(MDA_START_ADDRESS, mda_card)
    
    bus.install_device(None, ProgrammableInterruptController(0x00A0))
    bus.install_device(None, ProgrammableIntervalTimer(0x0040))
    
    print "\nSYSTEM BUS:"
    pprint(bus.devices)
    
    cpu = CPU()
    cpu.bus = bus
    
    while not cpu.hlt:
        log.debug("")
        cpu.fetch()

if __name__ == "__main__":
    main()
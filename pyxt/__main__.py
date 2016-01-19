#!/usr/bin/env python

"""
pyxt - Main application for running a demo PyXT system.
"""

# Standard library imports
import os
from pprint import pprint
from optparse import OptionParser

# PyXT imports
from pyxt.constants import SIXTY_FOUR_KB, BIOS_LOCATION
from pyxt.cpu import CPU
from pyxt.bus import SystemBus
from pyxt.memory import RAM, ROM
from pyxt.mda import CharacterGeneratorMDA_CGA_ROM, MonochromeDisplayAdapter, MDA_START_ADDRESS

from pyxt.dma import DmaController
from pyxt.onboard import ProgrammableInterruptController, ProgrammableIntervalTimer

# Logging setup
import logging
log = logging.getLogger(__name__)

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
    return parser.parse_args()
    
def main():
    """ Main application that runs the PyXT machine. """
    options, args = parse_cmdline()
    
    log_level = logging.DEBUG if options.debug else logging.INFO
    logging.basicConfig(format = "%(asctime)s %(message)s", level = log_level)
    log.info("PyXT oh hai")
    
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
    
    bus.install_device(None, DmaController(0x0000))
    bus.install_device(None, ProgrammableInterruptController(0x00A0))
    
    pit = ProgrammableIntervalTimer(0x0040)
    pit.channels[0].gate = True
    pit.channels[1].gate = True
    bus.install_device(None, pit)
    
    print "\nSYSTEM BUS:"
    pprint(bus.devices)
    pprint(bus.io_decoder)
    
    cpu = CPU()
    cpu.install_bus(bus)
    
    while not cpu.hlt:
        pit.clock()
        cpu.fetch()
        
if __name__ == "__main__":
    if os.environ.get("PYXT_PROFILING"):
        import cProfile
        cProfile.run("main()", sort = "time")
    else:
        main()
    
#!/usr/bin/env python

"""
pyxt - Main application for running a demo PyXT system.
"""

from __future__ import print_function

# Standard library imports
import os
import signal
from pprint import pprint
from optparse import OptionParser

# Six imports
from six.moves import range # pylint: disable=redefined-builtin

# PyXT imports
from pyxt.constants import SIXTY_FOUR_KB, BIOS_LOCATION
from pyxt.cpu import CPU
from pyxt.debugger import Debugger
from pyxt.bus import SystemBus
from pyxt.memory import RAM, ROM
from pyxt.mda import CharacterGeneratorMDA_CGA_ROM, MonochromeDisplayAdapter, MDA_START_ADDRESS
from pyxt.cga import ColorGraphicsAdapter, CGA_START_ADDRESS, CharacterGeneratorCGA
from pyxt.ui import PygameManager

from pyxt.fdc import FloppyDisketteController, FloppyDisketteDrive, FIVE_INCH_360_KB
from pyxt.dma import DmaController
from pyxt.nmi_mask import NMIMaskRegister
from pyxt.ppi import *
from pyxt.timer import ProgrammableIntervalTimer
from pyxt.pic import ProgrammableInterruptController

# Logging setup
import logging
log = logging.getLogger("pyxt")

# Constants
DEFAULT_DIP_SWITCHES = (SWITCHES_NORMAL_BOOT | SWITCHES_MEMORY_BANKS_FOUR | SWITCHES_VIDEO_MDA_HERC | SWITCHES_DISKETTES_TWO)

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
    parser.add_option("--display", action = "store", dest = "display", default = "mda",
                      help = "Display adapter type to use, default: mda.")
    parser.add_option("--dip-switches", action = "store", type = "int", dest = "dip_switches",
                      help = "DIP switch byte to use.", default = DEFAULT_DIP_SWITCHES)
    parser.add_option("--skip-memory-test", action = "store_true", dest = "skip_memory_test",
                      help = "Set the flag to skip the POST memory test.")
    parser.add_option("--no-collapse-delay-loops", action = "store_false", dest = "collapse_delay_loops", default = True,
                      help = "Set this flag to use the proper LOOP handler that doesn't optimize LOOP back to itself.")
    parser.add_option("--diskette", action = "store", dest = "diskette",
                      help = "Diskette image to load into the first drive (A:).")
    parser.add_option("--no-wp-a", action = "store_false", dest = "diskette_write_protect", default = True,
                      help = "Disable write protection for the first drive (A:).")
    parser.add_option("--diskette2", action = "store", dest = "diskette2",
                      help = "Diskette image to load into the second drive (B:).")
    parser.add_option("--no-wp-b", action = "store_false", dest = "diskette2_write_protect", default = True,
                      help = "Disable write protection for the second drive (B:).")
    parser.add_option("--log-file", action = "store", dest = "log_file",
                      help = "File to output debugging log.")
    parser.add_option("--log-filter", action = "store", dest = "log_filter",
                      help = "Log filter to apply to stderr handler.")
    return parser.parse_args()
    
def main():
    """ Main application that runs the PyXT machine. """
    options, args = parse_cmdline()
    
    log_level = logging.DEBUG if options.debug else logging.INFO
    log_formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(name)s(%(levelname)s): %(message)s", "%m/%d %H:%M:%S")
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(log_formatter)
    if options.log_filter:
        stderr_handler.addFilter(logging.Filter(options.log_filter))
    root_logger = logging.root
    root_logger.setLevel(log_level)
    root_logger.addHandler(stderr_handler)
    
    log.info("PyXT oh hai")
    
    if options.log_file:
        log.addHandler(logging.FileHandler(options.log_file))
        
    # The PIC and DMA controller are integral to the ISA/XT bus and need to be part of the bus.
    # They will also be installed below so they can be configured via I/O ports.
    pic = ProgrammableInterruptController(0x020)
    dma_controller = DmaController(0x0000, (0x087, 0x083, 0x081, 0x082))
    
    bus = SystemBus(pic, dma_controller)
    
    # 640KB OK
    for index in range(10):
        bus.install_device(index * SIXTY_FOUR_KB, RAM(SIXTY_FOUR_KB))
        
    # ROM BIOS
    if options.bios:
        bus.install_device(BIOS_LOCATION, ROM(SIXTY_FOUR_KB, init_file = options.bios))
        
    # Set the flag to skip the memory test if desired.
    # See the POST section here: http://www.bioscentral.com/misc/biosbasics.htm
    if options.skip_memory_test:
        bus.mem_write_word(0x0472, 0x1234)
        
    # Other onboard hardware devices.
    video_card = None
    if options.display == "mda":
        char_generator = CharacterGeneratorMDA_CGA_ROM(options.mda_rom, CharacterGeneratorMDA_CGA_ROM.MDA_FONT)
        video_card = MonochromeDisplayAdapter(char_generator, randomize = True)
        bus.install_device(MDA_START_ADDRESS, video_card)
    elif options.display == "cga":
        char_generator = CharacterGeneratorCGA(options.mda_rom, CharacterGeneratorMDA_CGA_ROM.CGA_WIDE_FONT)
        video_card = ColorGraphicsAdapter(char_generator, randomize = True)
        # Use MDA start address until devices can be installed on non-64k boundaries.
        bus.install_device(MDA_START_ADDRESS, video_card)
    else:
        log.error("Unsupported display type: %r", options.display)
        
    diskette_controller = FloppyDisketteController(0x3F0)
    bus.install_device(None, diskette_controller)
    a_drive = FloppyDisketteDrive(FIVE_INCH_360_KB)
    diskette_controller.attach_drive(a_drive, 0)
    b_drive = FloppyDisketteDrive(FIVE_INCH_360_KB)
    diskette_controller.attach_drive(b_drive, 1)
    
    if options.diskette:
        a_drive.load_diskette(options.diskette, options.diskette_write_protect)
        
    if options.diskette2:
        b_drive.load_diskette(options.diskette2, options.diskette2_write_protect)
        
    bus.install_device(None, dma_controller)
    nmi_mask = NMIMaskRegister(0x0A0)
    bus.install_device(None, nmi_mask)
    bus.install_device(None, pic)
    
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
        print("\nSYSTEM BUS:")
        pprint(bus.devices)
        pprint(bus.io_decoder)
    
    cpu = CPU()
    bus.install_cpu(cpu)
    
    # Select the desired LOOP instruction handler.
    cpu.collapse_delay_loops(options.collapse_delay_loops)
    
    debugger = Debugger(cpu, bus)
    for breakpoint in args:
        (cs, ip) = breakpoint.split(":")
        debugger.breakpoints.append((int(cs, 16), int(ip, 16)))
        
    if options.debug:
        signal.signal(signal.SIGINT, debugger.break_signal)
    
    cpu_or_debugger = debugger if options.debug else cpu
    
    pygame_manager = PygameManager(ppi, video_card)
    
    try:
        while True:
            pygame_manager.poll()
            
            # Run 50 iterations of PyXT between calls to the Pygame machine.
            for _ in range(50):
                pit.clock()
                dma_controller.clock()
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
    
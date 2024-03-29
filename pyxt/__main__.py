#!/usr/bin/env python

"""
pyxt - Main application for running a demo PyXT system.
"""

from __future__ import print_function

# Standard library imports
import os
import signal
from pprint import pprint
from optparse import OptionParser, OptionGroup

# Six imports
from six.moves import range # pylint: disable=redefined-builtin

# PyXT imports
from pyxt.constants import SIXTY_FOUR_KB, BIOS_LOCATION
from pyxt.cpu import CPU
from pyxt.debugger import Debugger
from pyxt.bus import SystemBus
from pyxt.memory import RAM, ROM
from pyxt.chargen import CharacterGeneratorMDA_CGA_ROM
from pyxt.mda import MonochromeDisplayAdapter, MDA_START_ADDRESS, MONO_PALETTES
from pyxt.cga import ColorGraphicsAdapter, CGA_START_ADDRESS
from pyxt.cpi import CharacterGeneratorCPI, CPI_MDA_SIZE, CPI_CGA_SIZE
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
DEFAULT_RAM_SIZE_KB = 640

# Functions
def parse_cmdline():
    """ Parse the command line arguments. """
    parser = OptionParser()
    
    system_group = OptionGroup(parser, "System Options")
    system_group.add_option("--bios", action = "store", dest = "bios",
                            help = "ROM BIOS image to load at 0xF0000.")
    system_group.add_option("--dip-switches", action = "store", type = "int", dest = "dip_switches",
                            help = "DIP switch byte to use.", default = DEFAULT_DIP_SWITCHES)
    system_group.add_option("--ram-size", action = "store", dest = "ram_size", default = DEFAULT_RAM_SIZE_KB, type = "int",
                            help = "Amount of RAM to add to the system in KB, default: 640.")
    parser.add_option_group(system_group)
    
    diskette_group = OptionGroup(parser, "Diskette Options")
    diskette_group.add_option("--diskette", action = "store", dest = "diskette",
                              help = "Diskette image to load into the first drive (A:).")
    diskette_group.add_option("--no-wp-a", action = "store_false", dest = "diskette_write_protect", default = True,
                              help = "Disable write protection for the first drive (A:).")
    diskette_group.add_option("--diskette2", action = "store", dest = "diskette2",
                              help = "Diskette image to load into the second drive (B:).")
    diskette_group.add_option("--no-wp-b", action = "store_false", dest = "diskette2_write_protect", default = True,
                              help = "Disable write protection for the second drive (B:).")
    parser.add_option_group(diskette_group)
                      
    display_group = OptionGroup(parser, "Display Options")
    display_group.add_option("--display", action = "store", dest = "display", default = "mda",
                             type = "choice", choices = ("mda", "cga"),
                             help = "Display adapter type to use, default: mda.")
    display_group.add_option("--mono-palette", action = "store", dest = "mono_palette",
                             default = "green", type = "choice", choices = list(MONO_PALETTES.keys()),
                             help = "Monochrome display color palette, default: green.")
    parser.add_option_group(display_group)
    
    chargen_group = OptionGroup(parser, "Character Generator Options")
    chargen_group.add_option("--mda-rom", "--cga-rom", action = "store", dest = "mda_cga_rom",
                             help = "MDA/CGA ROM to use for a virtual MDA/CGA card.")
    chargen_group.add_option("--cpi-file", action = "store", dest = "cpi_file",
                             help = "DOS CPI file to load character glyphs from.")
    chargen_group.add_option("--cpi-codepage", action = "store", type = "int", dest = "cpi_codepage",
                             help = "Codepage to use in CPI file.")
    parser.add_option_group(chargen_group)
    
    optimization_group = OptionGroup(parser, "Optimization Options")
    optimization_group.add_option("--skip-memory-test", action = "store_true", dest = "skip_memory_test",
                                  help = "Set the flag to skip the POST memory test.")
    optimization_group.add_option("--no-collapse-delay-loops", action = "store_false", dest = "collapse_delay_loops", default = True,
                                  help = "Set this flag to use the proper LOOP handler that doesn't optimize LOOP back to itself.")
    parser.add_option_group(optimization_group)
                  
    debugging_group = OptionGroup(parser, "Debugging Options")
    debugging_group.add_option("--debug", action = "store_true", dest = "debug",
                               help = "Enable DEBUG log level.")
    debugging_group.add_option("--log-file", action = "store", dest = "log_file",
                               help = "File to output debugging log.")
    debugging_group.add_option("--log-filter", action = "store", dest = "log_filter",
                               help = "Log filter to apply to stderr handler.")
    parser.add_option_group(debugging_group)
    
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
    
    # Round up to the next 64k.
    ram_blocks = (options.ram_size + 63) // 64
    for index in range(ram_blocks):
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
        if options.mda_cga_rom:
            char_generator = CharacterGeneratorMDA_CGA_ROM(options.mda_cga_rom, CharacterGeneratorMDA_CGA_ROM.MDA_FONT)
        elif options.cpi_file and options.cpi_codepage:
            char_generator = CharacterGeneratorCPI(options.cpi_file, options.cpi_codepage, CPI_MDA_SIZE, width_override = 9)
        else:
            raise ValueError("No character ROM provided for the MonochromeDisplayAdapter.")
            
        video_card = MonochromeDisplayAdapter(char_generator, randomize = True, palette = MONO_PALETTES[options.mono_palette])
        bus.install_device(MDA_START_ADDRESS, video_card)
    elif options.display == "cga":
        if options.mda_cga_rom:
            char_generator = CharacterGeneratorMDA_CGA_ROM(options.mda_cga_rom, CharacterGeneratorMDA_CGA_ROM.CGA_WIDE_FONT)
        elif options.cpi_file and options.cpi_codepage:
            char_generator = CharacterGeneratorCPI(options.cpi_file, options.cpi_codepage, CPI_CGA_SIZE)
        else:
            raise ValueError("No character ROM provided for the ColorGraphicsAdapter.")
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
    
    pygame_manager = PygameManager(ppi, video_card, debugger if options.debug else None)
    
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
    
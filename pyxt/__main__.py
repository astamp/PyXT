#!/usr/bin/env python

"""
pyxt - Main application for running a demo PyXT system.
"""

# Standard library imports
from pprint import pprint
from argparse import ArgumentParser

# PyXT imports
from pyxt.bus import SystemBus, RAM, ROM

# Constants

# Functions
def parse_cmdline():
    parser = ArgumentParser()
    parser.add_argument("--rom", nargs=2, action="append", dest="roms")
    return parser.parse_args()

def main():
    args = parse_cmdline()
    
    bus = SystemBus()
    
    for x in xrange(20):
        bus.add_device(x * 0x8000, RAM, 0x8000)
    
    if args.roms:
        for address, filepath in args.roms:
            print address, filepath
            bus.add_device(int(address, 0), ROM, 0x8000, init_file=filepath)
    
    pprint(bus.devices)

if __name__ == "__main__":
    main()
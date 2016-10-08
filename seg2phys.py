#!/usr/bin/env python

"""
Seg2Phys - Converts a segment:offset pair to a physical memory address.
"""

from __future__ import print_function

# Standard library imports
import sys

# PyXT imports
from pyxt.helpers import segment_offset_to_address

def main():
    """ Main application. """
    segment, offset = [int(x, 16) for x in sys.argv[1].split(":")]
    print("%04x:%04x = 0x%05x" % (segment, offset, segment_offset_to_address(segment, offset)))
    
if __name__ == "__main__":
    main()
    
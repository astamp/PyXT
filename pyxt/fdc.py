"""
pyxt.fdc - Floppy diskette controller for PyXT.
"""

# Standard library imports

# Six imports
from six.moves import range # pylint: disable=redefined-builtin

# PyXT imports
from pyxt.bus import Device

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants
FDC_CONTROL = 2 # Digital output register, external to the actual controller.
FDC_STATUS = 4
FDC_DATA = 5

# Classes
class FloppyDisketteController(Device):
    def __init__(self, base, **kwargs):
        super(FloppyDisketteController, self).__init__(**kwargs)
        self.base = base
        
    # Device interface.
    def get_ports_list(self):
        return [self.base + FDC_CONTROL, self.base + FDC_STATUS, self.base + FDC_DATA]
        
    def io_read_byte(self, port):
        offset = port - self.base
        if offset == FDC_STATUS:
            return 0
        elif offset == FDC_DATA:
            return 0
        else:
            log.warning("Invalid FDC port read: 0x%03x, returning 0x00.", port)
            return 0x00
            
    def io_write_byte(self, port, value):
        offset = port - self.base
        if offset == FDC_CONTROL:
            pass
        elif offset == FDC_STATUS:
            pass
        elif offset == FDC_DATA:
            pass
        else:
            log.warning("Invalid FDC port write: 0x%03x, with: 0x%02x.", port, value)
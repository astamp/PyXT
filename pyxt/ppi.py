"""
pyxt.ppi - Programmable peripheral interface (keyboard controller & more) for the XT and clones.
"""

# Standard library imports

# PyXT imports
from pyxt.bus import Device

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Classes
class ProgrammablePeripheralInterface(Device):
    def __init__(self, base, **kwargs):
        super(ProgrammablePeripheralInterface, self).__init__(**kwargs)
        self.base = base
        
    def get_ports_list(self):
        return [x for x in xrange(self.base, self.base + 4)]
        
    def io_read_byte(self, port):
        offset = port - self.base
        return 0
        
    def io_write_byte(self, port, value):
        offset = port - self.base
        if offset == 0:
            self.diag_port_output(value)
            
    def diag_port_output(self, value):
        log.info("Diag port output: 0x%02x", value)
        
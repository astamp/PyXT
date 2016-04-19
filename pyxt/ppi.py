"""
pyxt.ppi - Programmable peripheral interface (keyboard controller & more) for the XT and clones.

See PORTS.A from Ralf Brown's Interrupt List for more info.
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
        self.last_scancode = 0x00
        self.port_b_output = 0x00
        
    def get_ports_list(self):
        return [x for x in xrange(self.base, self.base + 4)]
        
    def io_read_byte(self, port):
        offset = port - self.base
        if offset == 0:
            return self.last_scancode
        elif offset == 1:
            return self.port_b_output
        else:
            return 0
        
    def io_write_byte(self, port, value):
        offset = port - self.base
        if offset == 0:
            self.write_diag_port(value)
        elif offset == 1:
            self.write_port_b(value)
            
    def write_diag_port(self, value):
        """ Write a value to the diag port, 0x060. """
        log.info("Diag port output: 0x%02x", value)
        
    def write_port_b(self, value):
        """ Writes a value to the PORT B output, 0x061. """
        self.port_b_output = value
        

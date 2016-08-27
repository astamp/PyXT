"""
pyxt.serial - RS-232 serial port for PyXT.

See PORTS.B from Ralf Brown's Interrupt List for more info. (http://www.cs.cmu.edu/~ralf/files.html)
"""

# Standard library imports

# Six imports
# from six.moves import range # pylint: disable=redefined-builtin

# PyXT imports
from pyxt.bus import Device

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants

# Classes
class SerialAdapter(Device):
    def __init__(self, base, irq, **kwargs):
        super(SerialAdapter, self).__init__(**kwargs)
        self.base = base
        self.irq = irq
        self.scratch_register = 0x00
        
    # Device interface.
    def get_ports_list(self):
        return [x for x in range(self.base, self.base + 8)]
        
    def io_read_byte(self, port):
        offset = port - self.base
        if offset == 7:
            return self.scratch_register
        else:
            return 0x00
        
    def io_write_byte(self, port, value):
        offset = port - self.base
        if offset == 7:
            self.scratch_register = value
            
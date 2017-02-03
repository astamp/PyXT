"""
pyxt.parallel - Centronics/IEEE1284 parallel port for PyXT.

http://retired.beyondlogic.org/spp/parallel.htm
https://en.wikipedia.org/wiki/Parallel_port
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
class ParallelAdapter(Device):
    def __init__(self, base, irq, **kwargs):
        super(ParallelAdapter, self).__init__(**kwargs)
        self.base = base
        self.irq = irq
        
    # Device interface.
    def get_ports_list(self):
        return [x for x in range(self.base, self.base + 3)]
        
    def io_read_byte(self, port):
        offset = port - self.base
        return 0x00
        
    def io_write_byte(self, port, value):
        offset = port - self.base
        
            
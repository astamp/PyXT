"""
pyxt.parallel - Centronics/IEEE1284 parallel port for PyXT.

http://retired.beyondlogic.org/spp/parallel.htm
https://en.wikipedia.org/wiki/Parallel_port
http://pinouts.ru/ParallelPorts/ParallelPC_pinout.shtml
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
LPT1_BASE = 0x3BC
LPT2_BASE = 0x378
LPT3_BASE = 0x278

LPT1_IRQ = LPT2_IRQ = 7
LPT3_IRQ = 5

DATA_PORT = 0
STATUS_PORT = 1
CONTROL_PORT = 2

STATUS_ERROR = 0x08
STATUS_SELECT = 0x10
STATUS_PAPER_OUT = 0x20
STATUS_ACK = 0x40
STATUS_BUSY = 0x80

CONTROL_N_STROBE = 0x01
CONTROL_N_AUTO_LINEFEED = 0x02
CONTROL_INITIALIZE = 0x04
CONTROL_N_SELECT_PRINTER = 0x08
CONTROL_IRQ_ENABLE = 0x10

# Classes
class ParallelDevice(object):
    """ Device that is connected to a parallel port. """
    def __init__(self):
        self.adapter = None
        
    def write_byte(self, value):
        """ Function called when a byte is written to the data port. """
        raise NotImplementedError
        
class ParallelAdapter(Device):
    def __init__(self, base, irq, **kwargs):
        super(ParallelAdapter, self).__init__(**kwargs)
        self.base = base
        self.irq = irq
        
        self.last_data_byte = 0x00
        self.irq_enable = False
        
        self.device = None
        
    # Device interface.
    def get_ports_list(self):
        return [x for x in range(self.base, self.base + 3)]
        
    def io_read_byte(self, port):
        offset = port - self.base
        if offset == DATA_PORT:
            return self.last_data_byte
        else:
            return 0x00
            
    def io_write_byte(self, port, value):
        offset = port - self.base
        if offset == DATA_PORT:
            self.last_data_byte = value
            if self.device is not None:
                self.device.write_byte(value)
        elif offset == CONTROL_PORT:
            self.irq_enable = value & CONTROL_IRQ_ENABLE == CONTROL_IRQ_ENABLE
            
    def connect(self, device):
        """ Connects a parallel device to this adapter. """
        self.device = device
        self.device.adapter = self
        
"""
pyxt.nmi_mask - Non-maskable interrupt mask register... really.
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

# Classes
class NMIMaskRegister(Device):
    def __init__(self, base, **kwargs):
        super(NMIMaskRegister, self).__init__(**kwargs)
        self.base = base
        self.masked = False
        
    def get_ports_list(self):
        return [x for x in range(self.base, self.base + 1)]
        
    def io_read_byte(self, port):
        # TODO: What does a real XT class PC do when you read this port?
        return 0x00 if self.masked else 0x80
        
    def io_write_byte(self, port, value):
        # TODO: What do other values do?
        assert value == 0x00 or value == 0x80
        self.masked = value == 0x00
        
"""
pyxt.dma - Virtual DMA controller for PyXT.
"""

# Standard library imports

# PyXT imports
from pyxt.bus import Device

# Classes
class DmaController(Device):
    """ A Device emulating an 8237 DMA controller. """
    
    def __init__(self, base, **kwargs):
        super(DmaController, self).__init__(**kwargs)
        self.base = base
        
    def get_ports_list(self):
        return [x for x in xrange(self.base, self.base + 16)]
        
    def clock(self):
        pass
        
    def io_read_byte(self, port):
        offset = port - self.base
        
    def io_write_byte(self, port, value):
        offset = port - self.base
        
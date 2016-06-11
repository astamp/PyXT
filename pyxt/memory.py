"""
pyxt.memory - Memory devices for PyXT.
"""

# Standard library imports
import array

# Six imports
import six

# PyXT imports
from pyxt.bus import Device
from pyxt.helpers import bytes_to_word, word_to_bytes

# Classes

# These 2 classes are memory only devices and do no implement I/O port operations.
class RAM(Device): # pylint:disable=abstract-method
    """ A device emulating a RAM storage device. """
    def __init__(self, size, **kwargs):
        super(RAM, self).__init__(**kwargs)
        self.contents = array.array("B", (0,) * size)
        
        # Inline these calls directly to the array object for speed.
        self.mem_read_byte = self.contents.__getitem__
        self.mem_write_byte = self.contents.__setitem__
        
    def __repr__(self):
        return "<%s(size=0x%x)>" % (self.__class__.__name__, len(self.contents))
        
    # def mem_read_byte(self, offset):
        # return self.contents[offset]
        
    def mem_read_word(self, offset):
        return bytes_to_word((self.contents[offset], self.contents[offset + 1]))
        
    # def mem_write_byte(self, offset, value):
        # self.contents[offset] = value
        
    def mem_write_word(self, offset, value):
        self.contents[offset], self.contents[offset + 1] = word_to_bytes(value)
        
class ROM(RAM): # pylint:disable=abstract-method
    """ A device emulating a ROM storage device. """
    def __init__(self, size, init_file = None, **kwargs):
        super(ROM, self).__init__(size, **kwargs)
        if init_file is not None:
            self.load_from_file(init_file)
            
        # Ensure this points at a version that doesn't allow setting.
        self.mem_write_byte = self.local_mem_write_byte
        
    def load_from_file(self, filename, offset = 0):
        """ Load this ROM with the contents of a file. """
        with open(filename, "rb") as fileptr:
            data = fileptr.read()
            
        for index, byte in enumerate(six.iterbytes(data), start = offset):
            self.contents[index] = byte
            
    def local_mem_write_byte(self, offset, value):
        pass
        
    def mem_write_word(self, offset, value):
        pass
        
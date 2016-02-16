"""
pyxt.exceptions - PyXT-specific exceptions.
"""

# Standard library imports

# PyXT imports


# Constants
WORD, LOW, HIGH = range(3)

# Classes
class PyXTException(Exception):
    """ Base class for all PyXT exceptions. """
    
class InvalidOpcodeException(PyXTException):
    """ Exception raised when an invalid opcode is encountered. """
    def __init__(self, opcode, cs, ip, prefixes = None):
        super(InvalidOpcodeException, self).__init__()
        self.opcode = opcode
        self.cs = cs
        self.ip = ip
        
    def __str__(self):
        return "Invalid opcode: 0x%02x at CS:IP %04x:%04x" % (self.opcode, self.cs, self.ip)
        
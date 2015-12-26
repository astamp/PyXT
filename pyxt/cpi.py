"""
pyxt.cpi - Code Page Information (CPI) decoder for PyXT.

See this site for more info:
http://www.seasip.info/DOS/CPI/cpi.html
"""

# Standard library imports
import array

# PyXT imports
from pyxt.hlstruct import Struct, Format, Type
from pyxt.chargen import CharacterGenerator

# Constants
FONT_ID_BYTE = b"\xFF"
FONT_ID_STR = b"FONT   "

DEVICE_TYPE_SCREEN = 1
DEVICE_TYPE_PRINTER = 2

# Structures
class FontFileHeader(Struct):
    """ CPI file FontFileHeader. """
    _format = Format.LittleEndian
    id0 = Type.UnsignedByte
    id = Type.String[7]
    reserved = Type.UnsignedByte[8]
    pnum = Type.UnsignedShort
    ptyp = Type.UnsignedByte
    fih_offset = Type.UnsignedLong
    
assert len(FontFileHeader) == 23

class FontInfoHeader(Struct):
    """ CPI file FontInfoHeader. """
    _format = Format.LittleEndian
    num_codepages = Type.UnsignedShort
    
assert len(FontInfoHeader) == 2

class CodePageEntryHeader(Struct):
    """ CPI file CodePageEntryHeader. """
    _format = Format.LittleEndian
    cpeh_header = Type.UnsignedShort
    next_cpeh_offset = Type.UnsignedLong
    device_type = Type.UnsignedShort
    device_name = Type.String[8]
    codepage = Type.UnsignedShort
    reserved = Type.UnsignedByte[6]
    cpih_offset = Type.UnsignedLong

assert len(CodePageEntryHeader) == 28

# Classes
class CharacterGeneratorCPIFile(CharacterGenerator):
    def __init__(self, cpi_file, codepage):
        with open(cpi_file, "rb") as fileptr:
            self.load_from_file(fileptr, codepage)
        
    def load_from_file(self, fileptr, codepage):
        """ Read in the CPI file from a file-like. """
        data = fileptr.read(len(FontFileHeader))
        if data[0] != FONT_ID_BYTE:
            raise ValueError("Invalid ID byte: %r" % data[0])
            
        file_header = FontFileHeader(data)
        if file_header.id != FONT_ID_STR:
            raise ValueError("Invalid font type: %r" % file_header.id)
            
        # These must both be 1 per the website above.
        if file_header.pnum != 1:
            raise ValueError("Invalid number of pointers: %r" % file_header.pnum)
        if file_header.ptyp != 1:
            raise ValueError("Invalid pointer type: %r" % file_header.ptyp)
            
        if file_header.fih_offset != fileptr.tell():
            raise ValueError("FontInfoHeader does not immediately follow the FontFileHeader!")
            
        data = fileptr.read(len(FontInfoHeader))
        info_header = FontInfoHeader(data)
        
        next_cpeh_offset = None
        for index in xrange(info_header.num_codepages):
            # If not the first entry follow the linked list offset.
            if next_cpeh_offset is not None:
                fileptr.seek(next_cpeh_offset)
                next_cpeh_offset = None
                
            data = fileptr.read(len(CodePageEntryHeader))
            entry_header = CodePageEntryHeader(data)
            print "aaaaaaaaaaaaaaaaaaaaaaaa"
            print entry_header.cpeh_header
            # Link to the next codepage in the file.
            next_cpeh_offset = entry_header.next_cpeh_offset
            print entry_header.device_type
            print entry_header.device_name
            print entry_header.codepage
            print entry_header.cpih_offset
        
# Test application.
def main():
    """ Test application for the CPI parsing module. """
    import sys
    
    print "CPI test application."
    cpi = CharacterGeneratorCPIFile(sys.argv[1], sys.argv[2])
    
    
if __name__ == "__main__":
    main()
    
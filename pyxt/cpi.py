"""
pyxt.cpi - Code Page Information (CPI) decoder for PyXT.

See this site for more info:
http://www.seasip.info/DOS/CPI/cpi.html
"""

from __future__ import print_function

# Standard library imports
import os
import array
from io import BytesIO
from collections import namedtuple

# PyXT imports
from pyxt.hlstruct import Struct, Format, Type
from pyxt.chargen import CharacterGenerator

# Six imports
import six
from six.moves import range # pylint: disable=redefined-builtin

# Constants
FONT_ID_BYTE = b"\xFF"
FONT_ID_STR = b"FONT   "

DEVICE_TYPE_SCREEN = 1
DEVICE_TYPE_PRINTER = 2

NUM_CHARS = 256

FontSize = namedtuple("FontSize", ["height", "width"])
EGA_VGA_SIZE = FontSize(16, 8)
MDA_SIZE = FontSize(14, 8)
CGA_SIZE = FontSize(8, 8)

BITS_7_TO_0 = (0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01)

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
    cpeh_size = Type.UnsignedShort
    next_cpeh_offset = Type.UnsignedLong
    device_type = Type.UnsignedShort
    device_name = Type.String[8]
    codepage = Type.UnsignedShort
    reserved = Type.UnsignedByte[6]
    cpih_offset = Type.UnsignedLong

assert len(CodePageEntryHeader) == 28

class CodePageInfoHeader(Struct):
    """ CPI file CodePageInfoHeader. """
    _format = Format.LittleEndian
    version = Type.UnsignedShort
    num_fonts = Type.UnsignedShort
    size = Type.UnsignedShort

assert len(CodePageInfoHeader) == 6

class ScreenFontHeader(Struct):
    """ CPI file ScreenFontHeader. """
    _format = Format.LittleEndian
    height = Type.UnsignedByte
    width = Type.UnsignedByte
    yaspect = Type.UnsignedByte
    xaspect = Type.UnsignedByte
    num_chars = Type.UnsignedShort

assert len(ScreenFontHeader) == 6

# Classes
class CodePageInformationFile(object):
    """ Class for decoding DOS CPI files. """
    def __init__(self):
        self.font_data = None
        self.supported_sizes = []
        
        self.codepages = {}
        
    def load_from_file(self, filename):
        """ Read in the CPI file from data. """
        with open(filename, "rb") as fileptr:
            self.font_data = BytesIO(fileptr.read())
        self._load_from_filelike(self.font_data)
        
    def load_from_data(self, data):
        """ Read in the CPI file from data. """
        self.font_data = BytesIO(data)
        self._load_from_filelike(self.font_data)
        
    def _load_from_filelike(self, fileptr):
        """ Read in the CPI file from a file-like. """
        # TODO: Remove these:
        codepage = 437
        font_size = MDA_SIZE
        
        data = fileptr.read(len(FontFileHeader))
        if data[0:1] != FONT_ID_BYTE:
            raise ValueError("Invalid ID byte: %r" % data[0:1])
            
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
        
        cpeh = None
        cpeh_offset = None
        
        next_cpeh_offset = None
        for index in range(info_header.num_codepages):
            # If not the first entry follow the linked list offset.
            if next_cpeh_offset is not None:
                fileptr.seek(next_cpeh_offset)
                
            this_cpeh_offset = fileptr.tell()
            data = fileptr.read(len(CodePageEntryHeader))
            entry_header = CodePageEntryHeader(data)
            
            if entry_header.cpeh_size != 28:
                raise ValueError("Invalid code page header size: %r" % entry_header.cpeh_size)
                
            if entry_header.device_type == DEVICE_TYPE_SCREEN:
                self.codepages[entry_header.codepage] = entry_header
                
            # Follow the linked list to the next codepage in the file.
            next_cpeh_offset = entry_header.next_cpeh_offset
                
        # TODO: Remove this.
        return
        
        if cpeh is None or cpeh_offset is None:
            raise ValueError("Did not find codepage %d in this file!" % codepage)
            
        fileptr.seek(cpeh.cpih_offset)
        data = fileptr.read(len(CodePageInfoHeader))
        info_header = CodePageInfoHeader(data)
        if info_header.version != 1:
            raise ValueError("Only version 1 info headers are supported!")
            
        # Loop through the various fonts (sizes) for this codepage until we find the one we want.
        for font in range(info_header.num_fonts):
            data = fileptr.read(len(ScreenFontHeader))
            screen_font_header = ScreenFontHeader(data)
                
            # If this isn't the size we need, seek past the bitmaps.
            if font_size.height != screen_font_header.height or font_size.width != screen_font_header.width:
                fileptr.seek((screen_font_header.width // 8) * screen_font_header.height * screen_font_header.num_chars, os.SEEK_CUR)
                continue
                
            if screen_font_header.num_chars != NUM_CHARS:
                raise ValueError("Font did not contain 256 characters! Had: %d" % screen_font_header.num_chars)
                
            # Dump out the characters to the display.
            for ordinal in range(screen_font_header.num_chars):
                print("   +-" + ("-" * (screen_font_header.width * 2)) + "+")
                for y in range(screen_font_header.height):
                    print("%2d |" % y, end = " ")
                    row = fileptr.read(screen_font_header.width // 8)
                    for byte in six.iterbytes(row):
                        for bit in BITS_7_TO_0:
                            print("#" if bit & byte else " ", end = " ")
                    print("|")
                print("   +-" + ("-" * (screen_font_header.width * 2)) + "+")
            break
            
    @property
    def supported_codepages(self):
        """ Returns a list of the supported codepages in the file. """
        return list(self.codepages.keys())
        
# Test application.
def main():
    """ Test application for the CPI parsing module. """
    import sys
    
    print("CPI test application.")
    cpi = CharacterGeneratorCPIFile(sys.argv[1], int(sys.argv[2]), MDA_SIZE)
    
    
if __name__ == "__main__":
    main()
    
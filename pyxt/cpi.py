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

FontSize = namedtuple("FontSize", ["width", "height"])
EGA_VGA_SIZE = FontSize(8, 16)
MDA_SIZE = FontSize(8, 14)
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
    
    def __init__(self, *args, **kwargs):
        super(ScreenFontHeader, self).__init__(*args, **kwargs)
        
        # Keep track of the offset in the font data for this header without affecting the struct size.
        # This offset should point to right after this header.
        self.glyph_data_offset = 0
        
assert len(ScreenFontHeader) == 6

# Classes
class CodePageInformationFile(object):
    """ Class for decoding DOS CPI files. """
    def __init__(self):
        self.font_data = None
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
            
    def _get_font_headers(self, codepage):
        """
        Returns a list of ScreenFontHeader for a given codepage.
        
        This parses the CodePageInfoHeader and walks the linked list of ScreenFontHeader(s).
        """
        cpeh = self.codepages.get(codepage, None)
        if cpeh is None:
            raise ValueError("Codepage %d not found!" % codepage)
        
        self.font_data.seek(cpeh.cpih_offset)
        
        data = self.font_data.read(len(CodePageInfoHeader))
        info_header = CodePageInfoHeader(data)
        if info_header.version != 1:
            raise ValueError("Invalid code page info version: %r" % info_header.version)
            
        # Loop through the various fonts (sizes) for this codepage, collecting the headers.
        font_headers = []
        for font in range(info_header.num_fonts):
            
            data = self.font_data.read(len(ScreenFontHeader))
            screen_font_header = ScreenFontHeader(data)
            screen_font_header.glyph_data_offset = self.font_data.tell()
            
            if screen_font_header.num_chars != NUM_CHARS:
                raise ValueError("Invalid number of characters in font: %d" % screen_font_header.num_chars)
                
            font_headers.append(screen_font_header)
            
            # Seek past the bitmaps to the next ScreenFontHeader.
            self.font_data.seek((screen_font_header.width // 8) * screen_font_header.height * screen_font_header.num_chars, os.SEEK_CUR)
            
        return font_headers
        
    def load_character_data(self, codepage, size, callback):
        """
        Calls `callback` with the data for each character.
        
        Signature of callback is:
            def callback(index, data, row_byte_width=1)
        """
        font_headers = self._get_font_headers(codepage)
        for screen_font_header in font_headers:
            # Check if this is the size requested.
            if (screen_font_header.width, screen_font_header.height) == size:
                
                # Seek to the beginning of this font data.
                self.font_data.seek(screen_font_header.glyph_data_offset)
                
                # Dump out the characters to the display.
                for ordinal in range(screen_font_header.num_chars):
                    self.dump_character(ordinal, self.font_data.read((screen_font_header.width // 8) * screen_font_header.height), screen_font_header.width // 8)
                    
                break
                
        # If we didn't find our size and break, throw an error.
        else:
            raise ValueError("Size (%d, %d) not found in codepage %d!" % (size[0], size[1], codepage))
            
    def dump_font(self, codepage, size):
        """ Print out an ASCII representation of a given font in a codepage. """
        self.load_character_data(codepage, size, self.dump_character)
        
    @staticmethod
    def dump_character(index, data, row_byte_width = 1):
        """ Print out an ASCII representation of a given character. """
        height = len(data)
        width = row_byte_width * 8
        
        print("Character %d (0x%02x):" % (index, index))
        print("   +-" + ("-" * (width * 2)) + "+")
        for y in range(height):
            print("%2d |" % y, end = " ")
            row = data[y * row_byte_width: (y + 1) * row_byte_width]
            for byte in six.iterbytes(row):
                for bit in BITS_7_TO_0:
                    print("#" if bit & byte else " ", end = " ")
            print("|")
        print("   +-" + ("-" * (width * 2)) + "+")
        
    def supported_codepages(self):
        """ Returns a list of the supported codepages in the file. """
        return list(self.codepages.keys())
        
    def supported_sizes(self, codepage):
        """ Returns a list of the supported sizes in a given codepage. """
        return [(font_header.width, font_header.height) for font_header in self._get_font_headers(codepage)]
        
        
# Test application.
def main():
    """ Test application for the CPI parsing module. """
    import sys
    
    print("CPI test application.")
    cpi = CodePageInformationFile()
    cpi.load_from_file(sys.argv[1])
    cpi.dump_font(int(sys.argv[2]), (int(sys.argv[3]), int(sys.argv[4])))
    
if __name__ == "__main__":
    main()
    
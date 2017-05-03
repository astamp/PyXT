from __future__ import print_function

import os
import inspect
import unittest

import six
from pyxt.cpi import *

def get_cpi_file(suite, filename):
    """ Get the path to a test file for a given suite. """
    return os.path.join(
        os.path.dirname(inspect.getfile(suite.__class__)), # tests
        "..", # pyxt
        "..", # root
        "files", "cpidos11", "BIN", "CPI",
        filename,
    )

class CPIFileTests(unittest.TestCase):
    def test_initial_state(self):
        blank_cpi = CodePageInformationFile()
        self.assertIsNone(blank_cpi.font_data)
        self.assertEqual(blank_cpi.supported_sizes, [])
        self.assertEqual(blank_cpi.supported_codepages, [])
        
    def test_load_from_data(self):
        test_cpi = CodePageInformationFile()
        with open(get_cpi_file(self, "ega.cpi"), "rb") as fileptr:
            data = fileptr.read()
        test_cpi.load_from_data(data)
        
        self.assertIsNotNone(test_cpi.font_data)
        test_cpi.font_data.seek(0, os.SEEK_END)
        self.assertEqual(test_cpi.font_data.tell(), 58880) # Size of file.
        
    def test_load_from_file(self):
        test_cpi = CodePageInformationFile()
        test_cpi.load_from_file(get_cpi_file(self, "ega.cpi"))
        
        self.assertIsNotNone(test_cpi.font_data)
        test_cpi.font_data.seek(0, os.SEEK_END)
        self.assertEqual(test_cpi.font_data.tell(), 58880) # Size of file.
        
    def test_invalid_font_id_byte(self):
        test_cpi = CodePageInformationFile()
        with six.assertRaisesRegex(self, ValueError, "Invalid ID byte: b?'t'") as context:
            test_cpi.load_from_data(b"this is not a font file")
            
    def test_invalid_font_id_string(self):
        test_cpi = CodePageInformationFile()
        with six.assertRaisesRegex(self, ValueError, "Invalid font type: b?'.+'") as context:
            test_cpi.load_from_data(b"\xFFthis is also not a font file")
            
    def test_invalid_number_of_pointers(self):
        test_cpi = CodePageInformationFile()
        with six.assertRaisesRegex(self, ValueError, "Invalid number of pointers: \d+") as context:
            test_cpi.load_from_data(b"\xFFFONT   ????????\x02\xAA\x01\x17\x00\x00\x00")
            
    def test_invalid_pointer_type(self):
        test_cpi = CodePageInformationFile()
        with six.assertRaisesRegex(self, ValueError, "Invalid pointer type: \d+") as context:
            test_cpi.load_from_data(b"\xFFFONT   ????????\x01\x00\xA5\x17\x00\x00\x00")
            
    def test_fih_does_not_immediately_follow(self):
        test_cpi = CodePageInformationFile()
        with six.assertRaisesRegex(self, ValueError, "FontInfoHeader does not immediately follow the FontFileHeader!") as context:
            test_cpi.load_from_data(b"\xFFFONT   ????????\x01\x00\x01\x18\x00\x00\x00")
            
class CPIFileAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.cpi = CodePageInformationFile()
        self.cpi.load_from_file(get_cpi_file(self, "ega.cpi"))
        
    def test_supported_codepages(self):
        self.assertEqual(set(self.cpi.supported_codepages), set([437, 850, 858, 852, 853, 857]))
        
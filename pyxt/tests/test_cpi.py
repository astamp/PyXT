from __future__ import print_function

import os
import inspect
import unittest

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
    def setUp(self):
        self.cpi = CodePageInformationFile()
        self.cpi.load_from_file(get_cpi_file(self, "ega.cpi"))
        
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
        
        self.assertIsNotNone(self.cpi.font_data)
        self.cpi.font_data.seek(0, os.SEEK_END)
        self.assertEqual(self.cpi.font_data.tell(), 58880) # Size of file.
        
    def test_load_from_file(self):
        self.assertIsNotNone(self.cpi.font_data)
        self.cpi.font_data.seek(0, os.SEEK_END)
        self.assertEqual(self.cpi.font_data.tell(), 58880) # Size of file.
        
import unittest

from pyxt.exceptions import *

class ExceptionTests(unittest.TestCase):
    def test_pyxt_exception(self):
        with self.assertRaises(PyXTException) as context:
            raise PyXTException("ham")
            
        self.assertEqual(str(context.exception), "ham")
        
    def test_invalid_opcode_exception(self):
        self.assertTrue(issubclass(InvalidOpcodeException, PyXTException))
        
        with self.assertRaises(InvalidOpcodeException) as context:
            raise InvalidOpcodeException(0x0f, 0xf000, 0x0010)
            
        self.assertEqual(str(context.exception), "Invalid opcode: 0x0f at CS:IP f000:0010")
        self.assertEqual(context.exception.opcode, 0x0f)
        self.assertEqual(context.exception.cs, 0xf000)
        self.assertEqual(context.exception.ip, 0x0010)
        
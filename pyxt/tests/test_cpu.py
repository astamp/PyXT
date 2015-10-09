import unittest

from pyxt.cpu import *

class FlagsRegisterTest(unittest.TestCase):
    def setUp(self):
        self.obj = FLAGS()
        
    def test_initialized_to_zero(self):
        self.assertEqual(self.obj.value, 0)
        
    def test_set(self):
        self.obj.value = FLAGS.CARRY
        self.obj.set(FLAGS.PARITY)
        self.assertEqual(self.obj.value, FLAGS.CARRY | FLAGS.PARITY)
        
    def test_clear(self):
        self.obj.value = FLAGS.CARRY | FLAGS.PARITY
        self.obj.clear(FLAGS.PARITY)
        self.assertEqual(self.obj.value, FLAGS.CARRY)
        
    def test_assign(self):
        self.obj.value = FLAGS.CARRY
        self.obj.assign(FLAGS.ZERO, True)
        self.assertEqual(self.obj.value, FLAGS.CARRY | FLAGS.ZERO)
        self.obj.assign(FLAGS.ZERO, False)
        self.assertEqual(self.obj.value, FLAGS.CARRY)
        
    def test_read(self):
        self.obj.value = FLAGS.CARRY | FLAGS.PARITY
        self.assertTrue(self.obj.read(FLAGS.CARRY))
        self.assertFalse(self.obj.read(FLAGS.ZERO))
        
    # Property tests.
    def test_carry_flag_property_get(self):
        self.assertFalse(self.obj.cf)
        self.obj.value |= FLAGS.CARRY
        self.assertTrue(self.obj.cf)
        
    def test_carry_flag_property_set(self):
        self.assertEqual(self.obj.value, 0)
        self.obj.cf = True
        self.assertEqual(self.obj.value, FLAGS.CARRY)
        self.obj.cf = False
        self.assertEqual(self.obj.value, 0)
        
    def test_parity_flag_property_get(self):
        self.assertFalse(self.obj.pf)
        self.obj.value |= FLAGS.PARITY
        self.assertTrue(self.obj.pf)
        
    def test_parity_flag_property_set(self):
        self.assertEqual(self.obj.value, 0)
        self.obj.pf = True
        self.assertEqual(self.obj.value, FLAGS.PARITY)
        self.obj.pf = False
        self.assertEqual(self.obj.value, 0)
        
    def test_adjust_flag_property_get(self):
        self.assertFalse(self.obj.af)
        self.obj.value |= FLAGS.ADJUST
        self.assertTrue(self.obj.af)
        
    def test_adjust_flag_property_set(self):
        self.assertEqual(self.obj.value, 0)
        self.obj.af = True
        self.assertEqual(self.obj.value, FLAGS.ADJUST)
        self.obj.af = False
        self.assertEqual(self.obj.value, 0)
        
    def test_zero_flag_property_get(self):
        self.assertFalse(self.obj.zf)
        self.obj.value |= FLAGS.ZERO
        self.assertTrue(self.obj.zf)
        
    def test_zero_flag_property_set(self):
        self.assertEqual(self.obj.value, 0)
        self.obj.zf = True
        self.assertEqual(self.obj.value, FLAGS.ZERO)
        self.obj.zf = False
        self.assertEqual(self.obj.value, 0)
        
    def test_sign_flag_property_get(self):
        self.assertFalse(self.obj.sf)
        self.obj.value |= FLAGS.SIGN
        self.assertTrue(self.obj.sf)
        
    def test_sign_flag_property_set(self):
        self.assertEqual(self.obj.value, 0)
        self.obj.sf = True
        self.assertEqual(self.obj.value, FLAGS.SIGN)
        self.obj.sf = False
        self.assertEqual(self.obj.value, 0)
        
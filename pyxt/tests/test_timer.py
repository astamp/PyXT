import unittest

from pyxt.timer import *

class PITDeviceTests(unittest.TestCase):
    def setUp(self):
        self.pit = ProgrammableIntervalTimer(0x0040)
        
    def test_ports_list(self):
        self.assertEqual(self.pit.get_ports_list(), [0x0040, 0x0041, 0x0042, 0x0043])
        
    def test_initial_state(self):
        self.assertEqual(self.pit.channels[0].value, 0)
        self.assertEqual(self.pit.channels[1].value, 0)
        self.assertEqual(self.pit.channels[2].value, 0)
        
    def test_decode_control_word(self):
        # Counter
        self.assertEqual(self.pit.decode_control_word(0x00)[0], 0)
        self.assertEqual(self.pit.decode_control_word(0x40)[0], 1)
        self.assertEqual(self.pit.decode_control_word(0x80)[0], 2)
        with self.assertRaises(AssertionError):
            self.pit.decode_control_word(0xC0)
        
        # Command
        self.assertEqual(self.pit.decode_control_word(0x00)[1], 0)
        self.assertEqual(self.pit.decode_control_word(0x10)[1], 1)
        self.assertEqual(self.pit.decode_control_word(0x20)[1], 2)
        self.assertEqual(self.pit.decode_control_word(0x30)[1], 3)
        
        # Mode
        self.assertEqual(self.pit.decode_control_word(0x00)[2], 0)
        self.assertEqual(self.pit.decode_control_word(0x02)[2], 1)
        self.assertEqual(self.pit.decode_control_word(0x04)[2], 2)
        self.assertEqual(self.pit.decode_control_word(0x06)[2], 3)
        self.assertEqual(self.pit.decode_control_word(0x08)[2], 4)
        self.assertEqual(self.pit.decode_control_word(0x0A)[2], 5)
        self.assertEqual(self.pit.decode_control_word(0x0C)[2], 2)
        self.assertEqual(self.pit.decode_control_word(0x0E)[2], 3)
        
        # BCD
        self.assertEqual(self.pit.decode_control_word(0x00)[3], 0)
        self.assertEqual(self.pit.decode_control_word(0x01)[3], 1)
        
class PITCounterTests(unittest.TestCase):
    def setUp(self):
        self.last_callback = None
        self.counter = Counter(self.output_changed_callback)
        
    def output_changed_callback(self, value):
        self.last_callback = value
        
    def test_initial_state(self):
        self.assertEqual(self.counter.count, 0)
        self.assertEqual(self.counter.value, 0)
        self.assertEqual(self.counter.latched_value, None)
        # self.assertEqual(self.channel.state, PIT_STATE_NORMAL)
        
    def test_get_read_value(self):
        self.counter.value = 56
        self.counter.latched_value = 67
        self.assertEqual(self.counter.get_read_value(), 67)
        self.counter.latched_value = None
        self.assertEqual(self.counter.get_read_value(), 56)
        
    def test_latch(self):
        self.counter.value = 78
        self.assertEqual(self.counter.latched_value, None)
        self.counter.latch()
        self.assertEqual(self.counter.latched_value, 78)
        
    def test_reconfigure_mode_0(self):
        self.counter.output = True
        self.counter.reconfigure(PIT_READ_WRITE_BOTH, 0, 0)
        self.assertEqual(self.counter.mode, 0)
        self.assertFalse(self.counter.output)
        
    def test_write_mode_0(self):
        self.counter.enabled = True
        self.counter.count = 0x8888
        self.counter.value = 0x7777
        self.counter.reconfigure(PIT_READ_WRITE_BOTH, 0, 0)
        self.assertTrue(self.counter.enabled) # Doesn't disable until first byte written.
        
        self.counter.write(0xFE)
        self.assertEqual(self.counter.value, 0x8888) # Updated from reconfigure().
        self.assertFalse(self.counter.enabled)
        
        self.counter.write(0xCA)
        self.assertTrue(self.counter.enabled)
        self.assertEqual(self.counter.count, 0xCAFE)
        self.assertEqual(self.counter.value, 0xCAFE)
        
    def test_clock_mode_0(self):
        self.counter.reconfigure(PIT_READ_WRITE_BOTH, 0, 0)
        self.counter.write(0x03)
        self.counter.write(0x00)
        self.assertEqual(self.counter.value, 0x0003)
        self.assertFalse(self.counter.output)
        
        # Gate low inhibits counting.
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0003)
        self.assertFalse(self.counter.output)
        
        # Gate high allows counting.
        self.counter.gate = True
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0002)
        self.assertFalse(self.counter.output)
        
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0001)
        self.assertFalse(self.counter.output)
        
        # On hitting zero, it raises the output line.
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0000)
        self.assertTrue(self.counter.output)
        
        # The timer keeps decrementing, but output stays high.
        self.counter.clock()
        self.assertEqual(self.counter.value, 0xFFFF) # Not sure if this should roll over to 0x0003?
        self.assertTrue(self.counter.output)
        
        # Reselecting the mode should restart the timer.
        self.counter.reconfigure(PIT_READ_WRITE_BOTH, 0, 0)
        self.assertEqual(self.counter.value, 0x0003)
        self.assertFalse(self.counter.output)
        
    def test_reconfigure_mode_2(self):
        self.counter.output = True
        self.counter.reconfigure(PIT_READ_WRITE_BOTH, 2, 0)
        self.assertEqual(self.counter.mode, 2)
        self.assertTrue(self.counter.output) # Not affected by reconfigure().
        
    def test_write_mode_2(self):
        self.counter.enabled = True
        self.counter.count = 0x8888
        self.counter.value = 0x7777
        
        self.counter.reconfigure(PIT_READ_WRITE_BOTH, 2, 0)
        self.assertEqual(self.counter.value, 0x7777) # Unaffected by reconfigure or writing the value.
        self.assertTrue(self.counter.enabled) # Should always stay enabled during this.
        
        self.counter.write(0xFE)
        self.assertEqual(self.counter.value, 0x7777) # Unaffected by reconfigure or writing the value.
        self.assertTrue(self.counter.enabled) # Should always stay enabled during this.
        
        self.counter.write(0xCA)
        self.assertEqual(self.counter.value, 0x7777) # Unaffected by reconfigure or writing the value.
        self.assertTrue(self.counter.enabled) # Should always stay enabled during this.
        self.assertEqual(self.counter.count, 0xCAFE)
        
    def test_clock_mode_2(self):
        self.counter.reconfigure(PIT_READ_WRITE_BOTH, 2, 0)
        
        # Gate low stops counting and raises output.
        self.counter.gate = False
        self.assertTrue(self.counter.output)
        self.assertFalse(self.counter.enabled)
        
        # Writing the value enables counting.
        self.counter.write(0x03)
        self.counter.write(0x00)
        self.assertTrue(self.counter.enabled)
        
        # These should not have changed.
        self.assertEqual(self.counter.value, 0x0000)
        self.assertTrue(self.counter.output)
        
        # Gate high reloads and starts.
        self.counter.gate = True
        self.assertEqual(self.counter.value, 0x0003)
        self.assertTrue(self.counter.output)
        self.assertTrue(self.counter.enabled)
        
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0002)
        self.assertTrue(self.counter.output)
        
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0001)
        self.assertFalse(self.counter.output) # Gets deasserted on 1.
        
        # On hitting zero, it reloads and raises the output line.
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0003)
        self.assertTrue(self.counter.output) # Gets asserted on reload.
        
        # Then it resets.
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0002)
        self.assertTrue(self.counter.output)
        
    def test_reconfigure_mode_3(self):
        # Should be same as mode 2.
        self.counter.output = True
        self.counter.reconfigure(PIT_READ_WRITE_BOTH, 3, 0)
        self.assertEqual(self.counter.mode, 3)
        self.assertTrue(self.counter.output) # Not affected by reconfigure().
        
    def test_write_mode_3(self):
        # Should be same as mode 3.
        self.counter.enabled = True
        self.counter.count = 0x8888
        self.counter.value = 0x7777
        
        self.counter.reconfigure(PIT_READ_WRITE_BOTH, 3, 0)
        self.assertEqual(self.counter.value, 0x7777) # Unaffected by reconfigure or writing the value.
        self.assertTrue(self.counter.enabled) # Should always stay enabled during this.
        
        self.counter.write(0xFE)
        self.assertEqual(self.counter.value, 0x7777) # Unaffected by reconfigure or writing the value.
        self.assertTrue(self.counter.enabled) # Should always stay enabled during this.
        
        self.counter.write(0xCA)
        self.assertEqual(self.counter.value, 0x7777) # Unaffected by reconfigure or writing the value.
        self.assertTrue(self.counter.enabled) # Should always stay enabled during this.
        self.assertEqual(self.counter.count, 0xCAFE)
        
    def test_clock_mode_3_odd(self):
        self.counter.reconfigure(PIT_READ_WRITE_BOTH, 3, 0)
        
        # Gate low stops counting and raises output.
        self.counter.gate = False
        self.assertTrue(self.counter.output)
        self.assertFalse(self.counter.enabled)
        
        # Writing the value enables counting.
        self.counter.write(0x07)
        self.counter.write(0x00)
        self.assertTrue(self.counter.enabled)
        
        # These should not have changed.
        self.assertEqual(self.counter.value, 0x0000)
        self.assertTrue(self.counter.output)
        
        # Gate high reloads and starts.
        self.counter.gate = True
        self.assertEqual(self.counter.value, 0x0007)
        self.assertTrue(self.counter.output)
        self.assertTrue(self.counter.enabled)
        
        # Output high and odd should decrement by 1.
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0006)
        self.assertTrue(self.counter.output)
        
        # Output high and even should decrement by 2.
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0004)
        self.assertTrue(self.counter.output)
        
        # Output high and even should decrement by 2 (repeat).
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0002)
        self.assertTrue(self.counter.output)
        
        # On hitting zero with output high, lowers output and reloads count.
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0007)
        self.assertFalse(self.counter.output)
        
        # Output low and odd should decrement by 3.
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0004)
        self.assertFalse(self.counter.output)
        
        # Output low and even should decrement by 2.
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0002)
        self.assertFalse(self.counter.output)
        
        # On hitting zero with output low, raises output and reloads count.
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0007)
        self.assertTrue(self.counter.output)
        
        # Make sure this loops forever...
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0006)
        self.assertTrue(self.counter.output)
        self.counter.clock()
        self.assertEqual(self.counter.value, 0x0004)
        self.assertTrue(self.counter.output)
        # ... and so on.
        
    def test_clock_mode_3_starting_at_zero(self):
        self.counter.reconfigure(PIT_READ_WRITE_BOTH, 3, 0)
        
        # Gate low stops counting and raises output.
        self.counter.gate = False
        self.assertTrue(self.counter.output)
        self.assertFalse(self.counter.enabled)
        
        # Writing the value enables counting.
        self.counter.write(0x00)
        self.counter.write(0x00)
        self.assertTrue(self.counter.enabled)
        
        # These should not have changed.
        self.assertEqual(self.counter.value, 0x0000)
        self.assertTrue(self.counter.output)
        
        # Gate high reloads and starts.
        self.counter.gate = True
        self.assertEqual(self.counter.value, 0x0000)
        self.assertTrue(self.counter.output)
        self.assertTrue(self.counter.enabled)
        
        # Output high and even should decrement by 2, should roll over not go negative.
        self.counter.clock()
        self.assertEqual(self.counter.value, 0xFFFE)
        self.assertTrue(self.counter.output)
        
        # Output high and even should decrement by 2.
        self.counter.clock()
        self.assertEqual(self.counter.value, 0xFFFC)
        self.assertTrue(self.counter.output)
        
        # ... and so on.
        
    def test_output_changed_callback_not_called_at_creation(self):
        self.assertIsNone(self.last_callback)
        
    def test_output_changed_callback_negative_going_transition(self):
        # Must first be positive to go negative.
        self.counter.output = True
        self.last_callback = None
        
        self.counter.output = False
        self.assertTrue(self.last_callback is False)
        self.assertFalse(self.counter.output)
        
    def test_output_changed_callback_positive_going_transition(self):
        self.counter.output = True
        self.assertTrue(self.last_callback is True)
        self.assertTrue(self.counter.output)
        
    def test_output_changed_callback_no_double_jeopardy(self):
        self.counter.output = True
        self.assertTrue(self.last_callback)
        self.last_callback = None
        
        self.counter.output = True
        self.assertIsNone(self.last_callback)
        
import unittest

from pyxt.pic import *

class PICTests(unittest.TestCase):
    def setUp(self):
        self.obj = ProgrammableInterruptController(0x00A0)
        
    def test_address_list(self):
        self.assertEqual(self.obj.get_ports_list(), [0x00A0, 0x00A1])
        
    def test_initial_state(self):
        self.assertEqual(self.obj.mask, 0x00)
        self.assertEqual(self.obj.interrupt_request_register, 0x00)
        self.assertEqual(self.obj.interrupt_in_service_register, 0x00)
        self.assertEqual(self.obj.read_register, ProgrammableInterruptController.READ_NONE)
        self.assertEqual(self.obj.priorities, [0, 1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(self.obj.icws_state, 0)
        self.assertEqual(self.obj.icw4_needed, False)
        self.assertEqual(self.obj.trigger_mode, ProgrammableInterruptController.EDGE_TRIGGERED)
        
    # ***** ICW1 Tests *****
    def test_icw1_starts_icws_state_machine(self):
        self.obj.icws_state = 8
        self.obj.icw4_needed = True
        self.obj.trigger_mode = 5
        self.obj.io_write_byte(0x00A0, 0x10)
        self.assertEqual(self.obj.icws_state, 2)
        self.assertEqual(self.obj.icw4_needed, False)
        self.assertEqual(self.obj.trigger_mode, ProgrammableInterruptController.EDGE_TRIGGERED)
        
    def test_icw1_needs_icw4(self):
        self.obj.io_write_byte(0x00A0, 0x11)
        self.assertEqual(self.obj.icws_state, 2)
        self.assertEqual(self.obj.icw4_needed, True)
        
        # Setting bit 4 and address 0 should restart the init sequence.
        self.obj.io_write_byte(0x00A0, 0x10)
        self.assertEqual(self.obj.icws_state, 2)
        self.assertEqual(self.obj.icw4_needed, False)
        
    def test_icw1_single_vs_cascade(self):
        self.obj.io_write_byte(0x00A0, 0x12)
        self.assertEqual(self.obj.icws_state, 2)
        self.assertEqual(self.obj.cascade, False)
        
        # Setting bit 4 and address 0 should restart the init sequence.
        self.obj.io_write_byte(0x00A0, 0x10)
        self.assertEqual(self.obj.icws_state, 2)
        self.assertEqual(self.obj.cascade, True)
        
    def test_icw1_address_interval(self):
        self.obj.io_write_byte(0x00A0, 0x10)
        self.assertEqual(self.obj.icws_state, 2)
        self.assertEqual(self.obj.address_interval, 8)
        
        # Setting bit 4 and address 0 should restart the init sequence.
        self.obj.io_write_byte(0x00A0, 0x14)
        self.assertEqual(self.obj.icws_state, 2)
        self.assertEqual(self.obj.address_interval, 4)
        
    def test_icw1_trigger_mode(self):
        self.obj.io_write_byte(0x00A0, 0x14)
        self.assertEqual(self.obj.icws_state, 2)
        self.assertEqual(self.obj.trigger_mode, ProgrammableInterruptController.LEVEL_TRIGGERED)
        
        # Setting bit 4 and address 0 should restart the init sequence.
        self.obj.io_write_byte(0x00A0, 0x10)
        self.assertEqual(self.obj.icws_state, 2)
        self.assertEqual(self.obj.trigger_mode, ProgrammableInterruptController.EDGE_TRIGGERED)
        
    # ***** ICW2 Tests *****
    def test_icw2_set_vector_base(self):
        self.obj.io_write_byte(0x00A0, 0x10)
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.assertEqual(self.obj.vector_base, 0xF8)
        
    def test_icw2_skip_icw3_and_icw4(self):
        self.obj.io_write_byte(0x00A0, 0x12)
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.assertEqual(self.obj.icws_state, 0)
        
    def test_icw2_skip_icw3_not_icw4(self):
        self.obj.io_write_byte(0x00A0, 0x13)
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.assertEqual(self.obj.icws_state, 4)
        
    # The next 2 tests ensure the states transition in the proper priority.
    def test_icw2_to_icw3_and_icw4(self):
        self.obj.io_write_byte(0x00A0, 0x11)
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.assertEqual(self.obj.icws_state, 3)
        
    def test_icw2_to_icw3_skip_icw4(self):
        self.obj.io_write_byte(0x00A0, 0x10)
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.assertEqual(self.obj.icws_state, 3)
        
    # ***** ICW3 Tests *****
    def test_icw3_to_icw4(self):
        self.obj.io_write_byte(0x00A0, 0x11)
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.obj.io_write_byte(0x00A1, 0x00)
        self.assertEqual(self.obj.icws_state, 4)
        
    def test_icw3_skip_icw4(self):
        self.obj.io_write_byte(0x00A0, 0x12)
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.obj.io_write_byte(0x00A1, 0x00)
        self.assertEqual(self.obj.icws_state, 0)
        
    # ***** ICW4 Tests *****
    def test_icw4_ends_init_sequence(self):
        self.obj.io_write_byte(0x00A0, 0x13)
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.obj.io_write_byte(0x00A1, 0x00)
        self.obj.io_write_byte(0x00A1, 0x00)
        self.assertEqual(self.obj.icws_state, 0)
        
    def test_icw4_8086_8088_vs_mcs80_8085_mode(self):
        self.obj.io_write_byte(0x00A0, 0x11) # Skip ICW3
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.obj.io_write_byte(0x00A1, 0x00)
        self.assertEqual(self.obj.i8086_8088_mode, False)
        
        self.obj.io_write_byte(0x00A0, 0x13) # Skip ICW3
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.obj.io_write_byte(0x00A1, 0x01)
        self.assertEqual(self.obj.i8086_8088_mode, True)
        
        # Ensure MCS-80/8085 when skipped.
        self.obj.io_write_byte(0x00A0, 0x10) # Skip ICW3 and ICW4
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.assertEqual(self.obj.i8086_8088_mode, False)
        
    def test_icw4_eoi_mode(self):
        self.obj.io_write_byte(0x00A0, 0x13) # Skip ICW3
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.obj.io_write_byte(0x00A1, 0x00)
        self.assertEqual(self.obj.auto_eoi, False)
        
        self.obj.io_write_byte(0x00A0, 0x13) # Skip ICW3
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.obj.io_write_byte(0x00A1, 0x02)
        self.assertEqual(self.obj.auto_eoi, True)
        
        # Ensure normal EOI when skipped.
        self.obj.io_write_byte(0x00A0, 0x12) # Skip ICW3 and ICW4
        self.obj.io_write_byte(0x00A1, 0xFF)
        self.assertEqual(self.obj.auto_eoi, False)
        
    # ***** OCW1 Tests *****
    def test_ocw1_sets_mask(self):
        self.obj.io_write_byte(0x00A1, 0x56)
        self.assertEqual(self.obj.mask, 0x56)
        
        self.obj.io_write_byte(0x00A1, 0x00)
        self.assertEqual(self.obj.mask, 0x00)
        
    # ***** OCW2 Tests *****
    
    # ***** OCW3 Tests *****
    def test_ocw3_read_register(self):
        self.obj.interrupt_request_register = 0xAA
        self.obj.interrupt_in_service_register = 0x55
        
        # Read none.
        self.obj.io_write_byte(0x0A0, 0x08)
        self.assertEqual(self.obj.io_read_byte(0x0A0), 0x00)
        
        # Another read none.
        self.obj.io_write_byte(0x0A0, 0x09)
        self.assertEqual(self.obj.io_read_byte(0x0A0), 0x00)
        
        # Read interrupt request register.
        self.obj.io_write_byte(0x0A0, 0x0A)
        self.assertEqual(self.obj.io_read_byte(0x0A0), 0xAA)
        
        # Read in-service register.
        self.obj.io_write_byte(0x0A0, 0x0B)
        self.assertEqual(self.obj.io_read_byte(0x0A0), 0x55)
        
    # ***** IRQ Tests *****
    def test_irq_not_masked(self):
        self.obj.interrupt_request(4)
        self.assertEqual(self.obj.interrupt_request_register, 0x10)
        
    def test_irq_when_masked(self):
        self.obj.io_write_byte(0x0A1, 0xFF) # Mask all interrupts.
        self.obj.interrupt_request(4)
        self.assertEqual(self.obj.interrupt_request_register, 0x00)
        
    def test_interrupt_pending_no(self):
        self.assertFalse(self.obj.interrupt_pending())
        
    def test_interrupt_pending_yes(self):
        self.obj.interrupt_request(4)
        self.assertTrue(self.obj.interrupt_pending())
        
    def test_pop_interrupt_vector_with_no_pending_interrupt(self):
        with self.assertRaises(RuntimeError):
            self.obj.pop_interrupt_vector()
            
    def test_pop_interrupt_vector(self):
        self.obj.vector_base = 0x08
        self.obj.interrupt_request(4)
        self.assertEqual(self.obj.interrupt_request_register, 0x10)
        self.assertEqual(self.obj.pop_interrupt_vector(), 0x0C)
        self.assertEqual(self.obj.interrupt_request_register, 0x00)
        
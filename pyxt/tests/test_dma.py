import unittest

from pyxt.dma import *

class DMATests(unittest.TestCase):
    def setUp(self):
        self.dma = DmaController(0x0000, (0x087, 0x083, 0x081, 0x082))
        self.terminal_count = False
        
    def test_address_list(self):
        self.assertEqual(self.dma.get_ports_list(), [0x0000, 0x0001, 0x0002, 0x0003,
                                                     0x0004, 0x0005, 0x0006, 0x0007,
                                                     0x0008, 0x0009, 0x000A, 0x000B,
                                                     0x000C, 0x000D, 0x000E, 0x000F,
                                                     0x087, 0x083, 0x081, 0x082])
        
    def test_initial_state(self):
        self.assertEqual(self.dma.state, STATE_SI)
        self.assertTrue(self.dma.low_byte)
        self.assertFalse(self.dma.enable)
        self.assertEqual(len(self.dma.channels), 4)
        
        for channel in self.dma.channels:
            self.assertFalse(channel.requested)
            self.assertTrue(channel.masked)
        
    def test_read_low_high(self):
        self.assertEqual(self.dma.read_low_high(0xCAFE), 0xFE)
        self.assertEqual(self.dma.read_low_high(0xCAFE), 0xCA)
        self.assertEqual(self.dma.read_low_high(0xCAFE), 0xFE)
        
    def test_write_low_high(self):
        self.assertEqual(self.dma.write_low_high(0x0000, 0xCE), 0x00CE)
        self.assertEqual(self.dma.write_low_high(0x00CE, 0xFA), 0xFACE)
        self.assertEqual(self.dma.write_low_high(0xFACE, 0xDE), 0xFADE)
        
    def test_io_write_byte_channel_regs(self):
        self.dma.io_write_byte(0x0000, 0x01)
        self.dma.io_write_byte(0x0000, 0x02)
        self.assertEqual(self.dma.channels[0].address, 0x0201)
        self.assertEqual(self.dma.channels[0].base_address, 0x0201)
        
        self.dma.io_write_byte(0x0001, 0x03)
        self.dma.io_write_byte(0x0001, 0x04)
        self.assertEqual(self.dma.channels[0].word_count, 0x0403)
        self.assertEqual(self.dma.channels[0].base_word_count, 0x0403)
        
        self.dma.io_write_byte(0x0002, 0x05)
        self.dma.io_write_byte(0x0002, 0x06)
        self.assertEqual(self.dma.channels[1].address, 0x0605)
        self.assertEqual(self.dma.channels[1].base_address, 0x0605)
        
        self.dma.io_write_byte(0x0003, 0x07)
        self.dma.io_write_byte(0x0003, 0x08)
        self.assertEqual(self.dma.channels[1].word_count, 0x0807)
        self.assertEqual(self.dma.channels[1].base_word_count, 0x0807)
        
        self.dma.io_write_byte(0x0004, 0x09)
        self.dma.io_write_byte(0x0004, 0x0A)
        self.assertEqual(self.dma.channels[2].address, 0x0A09)
        self.assertEqual(self.dma.channels[2].base_address, 0x0A09)
        
        self.dma.io_write_byte(0x0005, 0x0B)
        self.dma.io_write_byte(0x0005, 0x0C)
        self.assertEqual(self.dma.channels[2].word_count, 0x0C0B)
        self.assertEqual(self.dma.channels[2].base_word_count, 0x0C0B)
        
        self.dma.io_write_byte(0x0006, 0x0D)
        self.dma.io_write_byte(0x0006, 0x0E)
        self.assertEqual(self.dma.channels[3].address, 0x0E0D)
        self.assertEqual(self.dma.channels[3].base_address, 0x0E0D)
        
        self.dma.io_write_byte(0x0007, 0x0F)
        self.dma.io_write_byte(0x0007, 0x10)
        self.assertEqual(self.dma.channels[3].word_count, 0x100F)
        self.assertEqual(self.dma.channels[3].base_word_count, 0x100F)
        
    def test_io_read_byte_channel_regs(self):
        # We should not return the base values, so make sure they are invalid.
        for channel in self.dma.channels:
            channel.base_address = 0xFFFF
            channel.base_word_count = 0xFFFF
            
        self.dma.channels[0].address = 0x0011
        self.dma.channels[0].word_count = 0x2233
        
        self.dma.channels[1].address = 0x4455
        self.dma.channels[1].word_count = 0x6677
        
        self.dma.channels[2].address = 0x8899
        self.dma.channels[2].word_count = 0xAABB
        
        self.dma.channels[3].address = 0xCCDD
        self.dma.channels[3].word_count = 0xEEFF
        
        self.assertEqual(self.dma.io_read_byte(0x0000), 0x11)
        self.assertEqual(self.dma.io_read_byte(0x0000), 0x00)
        
        self.assertEqual(self.dma.io_read_byte(0x0001), 0x33)
        self.assertEqual(self.dma.io_read_byte(0x0001), 0x22)
        
        self.assertEqual(self.dma.io_read_byte(0x0002), 0x55)
        self.assertEqual(self.dma.io_read_byte(0x0002), 0x44)
        
        self.assertEqual(self.dma.io_read_byte(0x0003), 0x77)
        self.assertEqual(self.dma.io_read_byte(0x0003), 0x66)
        
        self.assertEqual(self.dma.io_read_byte(0x0004), 0x99)
        self.assertEqual(self.dma.io_read_byte(0x0004), 0x88)
        
        self.assertEqual(self.dma.io_read_byte(0x0005), 0xBB)
        self.assertEqual(self.dma.io_read_byte(0x0005), 0xAA)
        
        self.assertEqual(self.dma.io_read_byte(0x0006), 0xDD)
        self.assertEqual(self.dma.io_read_byte(0x0006), 0xCC)
        
        self.assertEqual(self.dma.io_read_byte(0x0007), 0xFF)
        self.assertEqual(self.dma.io_read_byte(0x0007), 0xEE)
        
    def test_set_low_high_flipflop_low(self):
        self.dma.low_byte = True
        self.dma.io_write_byte(0x0C, 0)
        self.assertTrue(self.dma.low_byte) # Shouldn't toggle.
        
        self.dma.low_byte = False
        self.dma.io_write_byte(0x0C, 0)
        self.assertTrue(self.dma.low_byte) # Should set to low byte.
        
    def test_read_status_register(self):
        self.dma.channels[1].requested = True
        self.dma.channels[2].word_count = 0xFFFF
        self.assertEqual(self.dma.io_read_byte(0x08), 0x24)
        
    def test_command_register_enable_disable(self):
        self.dma.io_write_byte(0x08, 0x00)
        self.assertTrue(self.dma.enable)
        self.dma.io_write_byte(0x08, 0x04)
        self.assertFalse(self.dma.enable)
        
    def test_master_clear(self):
        # Set the controller into a non-default state.
        self.dma.enable = True
        self.dma.low_byte = False
        self.dma.state = 5643
        self.dma.channels[0].requested = True
        self.dma.channels[0].masked = False
        
        self.dma.io_write_byte(0x0D, 0)
        
        # Should be the same as a reset, so call the initial state test.
        self.test_initial_state()
        
    def test_write_mode_register(self):
        self.dma.io_write_byte(0x0B, 0x74)
        self.assertEqual(self.dma.channels[0].transfer_type, TYPE_WRITE)
        self.assertEqual(self.dma.channels[0].mode, MODE_SINGLE)
        self.assertTrue(self.dma.channels[0].auto_init)
        self.assertEqual(self.dma.channels[0].increment, -1)
        
        self.dma.io_write_byte(0x0B, 0x89)
        self.assertEqual(self.dma.channels[1].transfer_type, TYPE_READ)
        self.assertEqual(self.dma.channels[1].mode, MODE_BLOCK)
        self.assertFalse(self.dma.channels[1].auto_init)
        self.assertEqual(self.dma.channels[1].increment, 1)
        
    def test_write_all_mask_bits(self):
        self.dma.io_write_byte(0x0F, 0xCA)
        self.assertFalse(self.dma.channels[0].masked)
        self.assertTrue(self.dma.channels[1].masked)
        self.assertFalse(self.dma.channels[2].masked)
        self.assertTrue(self.dma.channels[3].masked)
        
    def test_write_single_mask_bit(self):
        # Unmask channel 1.
        self.dma.io_write_byte(0x0A, 0x01)
        self.assertTrue(self.dma.channels[0].masked)
        self.assertFalse(self.dma.channels[1].masked)
        self.assertTrue(self.dma.channels[2].masked)
        self.assertTrue(self.dma.channels[3].masked)
        
        # Mask channel 1.
        self.dma.io_write_byte(0x0A, 0x05)
        self.assertTrue(self.dma.channels[0].masked)
        self.assertTrue(self.dma.channels[1].masked)
        self.assertTrue(self.dma.channels[2].masked)
        self.assertTrue(self.dma.channels[3].masked)
        
    def test_clock(self):
        self.dma.channels[0].mode = MODE_SINGLE
        self.dma.channels[0].requested = True
        self.dma.channels[0].word_count = 4
        self.dma.channels[0].address = 0
        
        # Nothing should happen when not enabled.
        self.dma.clock()
        self.assertEqual(self.dma.channels[0].word_count, 4)
        self.assertEqual(self.dma.channels[0].address, 0)
        
        # Enabling should allow DMA to work.
        self.dma.enable = True
        self.dma.clock()
        self.assertEqual(self.dma.channels[0].word_count, 3)
        self.assertEqual(self.dma.channels[0].address, 1)
        
        self.dma.clock()
        self.assertEqual(self.dma.channels[0].word_count, 2)
        self.assertEqual(self.dma.channels[0].address, 2)
        
        self.dma.clock()
        self.assertEqual(self.dma.channels[0].word_count, 1)
        self.assertEqual(self.dma.channels[0].address, 3)
        
        self.dma.clock()
        self.assertEqual(self.dma.channels[0].word_count, 0)
        self.assertEqual(self.dma.channels[0].address, 4)
        
        # Nothing more to do.
        self.dma.clock()
        self.assertEqual(self.dma.channels[0].word_count, 0xFFFF) # Terminal count.
        self.assertEqual(self.dma.channels[0].address, 5)
        
    def test_writing_page_registers(self):
        self.dma.io_write_byte(0x087, 0xCA)
        self.assertEqual(self.dma.channels[0].page_register_value, 0xCA)
        self.dma.io_write_byte(0x083, 0xFE)
        self.assertEqual(self.dma.channels[1].page_register_value, 0xFE)
        self.dma.io_write_byte(0x081, 0xFA)
        self.assertEqual(self.dma.channels[2].page_register_value, 0xFA)
        self.dma.io_write_byte(0x082, 0xCE)
        self.assertEqual(self.dma.channels[3].page_register_value, 0xCE)
        
    def test_reading_page_registers(self):
        self.dma.channels[0].page_register_value = 0x11
        self.assertEqual(self.dma.io_read_byte(0x87), 0x11)
        self.dma.channels[1].page_register_value = 0x22
        self.assertEqual(self.dma.io_read_byte(0x83), 0x22)
        self.dma.channels[2].page_register_value = 0x33
        self.assertEqual(self.dma.io_read_byte(0x81), 0x33)
        self.dma.channels[3].page_register_value = 0x44
        self.assertEqual(self.dma.io_read_byte(0x82), 0x44)
        
    def signal_terminal_count(self):
        self.terminal_count = True
        
    def test_terminal_count(self):
        self.dma.enable = True
        self.dma.channels[0].mode = MODE_SINGLE
        self.dma.channels[0].word_count = 3
        self.dma.channels[0].address = 0
        self.dma.dma_request(0, 5643, self.signal_terminal_count)
        
        self.dma.clock()
        self.assertEqual(self.dma.channels[0].word_count, 2)
        self.assertEqual(self.dma.channels[0].address, 1)
        self.assertFalse(self.terminal_count)
        
        self.dma.clock()
        self.assertEqual(self.dma.channels[0].word_count, 1)
        self.assertEqual(self.dma.channels[0].address, 2)
        self.assertFalse(self.terminal_count)
        
        self.dma.clock()
        self.assertEqual(self.dma.channels[0].word_count, 0)
        self.assertEqual(self.dma.channels[0].address, 3)
        self.assertFalse(self.terminal_count)
        
        # Should call the terminal count callback.
        self.dma.clock()
        self.assertEqual(self.dma.channels[0].word_count, 0xFFFF) # Terminal count.
        self.assertEqual(self.dma.channels[0].address, 4)
        self.assertTrue(self.terminal_count)
        
        
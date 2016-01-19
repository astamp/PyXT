import unittest

from pyxt.dma import *

class DMATests(unittest.TestCase):
    def setUp(self):
        self.dma = DmaController(0x0000)
        
    def test_address_list(self):
        self.assertEqual(self.dma.get_ports_list(), [0x0000, 0x0001, 0x0002, 0x0003,
                                                     0x0004, 0x0005, 0x0006, 0x0007,
                                                     0x0008, 0x0009, 0x000A, 0x000B,
                                                     0x000C, 0x000D, 0x000E, 0x000F])
        
    def test_initial_state(self):
        self.assertEqual(self.dma.state, STATE_SI)
        self.assertEqual(self.dma.low_byte, True)
        
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
        
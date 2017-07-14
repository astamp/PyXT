"""
pyxt.ppi - Programmable peripheral interface (keyboard controller & more) for the XT and clones.

See PORTS.A from Ralf Brown's Interrupt List for more info. (http://www.cs.cmu.edu/~ralf/files.html)
Also see http://www.rci.rutgers.edu/~preid/pcxtsw.htm for info on DIP switches.
"""

# Standard library imports

# Six imports
from six.moves import range # pylint: disable=redefined-builtin

# PyXT imports
from pyxt.bus import Device
from pyxt.interface import KeyboardController
from pyxt.ui import PygameManager, KEYBOARD_RESET
from pyxt.speaker import GLOBAL_SPEAKER

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants
KEYBOARD_IRQ_LINE = 1

KEYBOARD_SELF_TEST_COMPLETE = 0xAA

PORT_B_TIMER_2_GATE = 0x01
PORT_B_SPEAKER_DATA = 0x02
PORT_B_SPEAKER_ENABLE = PORT_B_TIMER_2_GATE | PORT_B_SPEAKER_DATA
PORT_B_RESERVED = 0x04 # Or cassette motor in PC.
PORT_B_READ_SWITCHES_HIGH_NIBBLE = 0x08
PORT_B_NMI_RAM_PARITY_DISABLE = 0x10
PORT_B_NMI_IO_PARITY_DISABLE = 0x20
PORT_B_KEYBOARD_CLOCK_ENABLE = 0x40
PORT_B_CLEAR_KEYBOARD = 0x80

SWITCHES_NORMAL_BOOT = 0x01
SWITCHES_8087_PRESENT = 0x02
SWITCHES_MEMORY_BANKS_ONE = 0x00
SWITCHES_MEMORY_BANKS_TWO = 0x04
SWITCHES_MEMORY_BANKS_THREE = 0x08
SWITCHES_MEMORY_BANKS_FOUR = 0x0C
SWITCHES_MEMORY_BANKS_MASK = 0x0C
SWITCHES_VIDEO_NONE_EGA_VGA = 0x00
SWITCHES_VIDEO_CGA_40_COL = 0x10
SWITCHES_VIDEO_CGA_80_COL = 0x20
SWITCHES_VIDEO_MDA_HERC = 0x30
SWITCHES_VIDEO_MASK = 0x30
SWITCHES_DISKETTES_ONE = 0x00
SWITCHES_DISKETTES_TWO = 0x40
SWITCHES_DISKETTES_THREE = 0x80
SWITCHES_DISKETTES_FOUR = 0xC0
SWITCHES_DISKETTES_MASK = 0xC0

# Classes
class ProgrammablePeripheralInterface(Device, KeyboardController):
    def __init__(self, base, **kwargs):
        super(ProgrammablePeripheralInterface, self).__init__(**kwargs)
        self.base = base
        self.dip_switches = 0x00
        self.last_scancode = 0x00
        self.port_b_output = 0x00
        self.timer_2_gate_callable = None
        
    # Device interface.
    def get_ports_list(self):
        return [x for x in range(self.base, self.base + 4)]
        
    def io_read_byte(self, port):
        offset = port - self.base
        if offset == 0:
            return self.read_keyboard_port()
        elif offset == 1:
            return self.port_b_output
        elif offset == 2:
            return self.read_port_c()
        else:
            return 0
        
    def io_write_byte(self, port, value):
        offset = port - self.base
        if offset == 0:
            self.write_diag_port(value)
        elif offset == 1:
            self.write_port_b(value)
            
    # KeyboardController interface.
    def key_pressed(self, scancodes):
        # Scancode could be a tuple of multiple bytes in an AT keyboard, we will only ever have 1 byte.
        self.last_scancode = scancodes[0]
        self.bus.interrupt_request(KEYBOARD_IRQ_LINE)
        
    def self_test_complete(self):
        self.key_pressed((KEYBOARD_SELF_TEST_COMPLETE, ))
        
    # Local functions.
    def write_diag_port(self, value):
        """ Write a value to the diag port, 0x060. """
        log.info("Diag port output: 0x%02x", value)
        
    def read_keyboard_port(self):
        """ Read the last scancode from the keyboard port, 0x060. """
        return self.last_scancode
        
    def write_port_b(self, value):
        """ Writes a value to the PORT B output, 0x061. """
        # Clear the last scancode "shift register".
        if value & PORT_B_CLEAR_KEYBOARD:
            self.last_scancode = 0x00
            
        # Signal reset only on positive going transition of the clock line.
        if value & PORT_B_KEYBOARD_CLOCK_ENABLE and self.port_b_output & PORT_B_KEYBOARD_CLOCK_ENABLE == 0x00:
            self.signal_keyboard_reset()
            
        # Update the speaker to reflect the enable bits.
        self.speaker_control(value & PORT_B_SPEAKER_ENABLE == PORT_B_SPEAKER_ENABLE)
        
        # Gate the operation of timer 2.
        if callable(self.timer_2_gate_callable):
            self.timer_2_gate_callable(value & PORT_B_TIMER_2_GATE == PORT_B_TIMER_2_GATE)
            
        self.port_b_output = value
        
    def signal_keyboard_reset(self):
        """ Sends the "reset" signal to the keyboard. """
        PygameManager.set_timer(KEYBOARD_RESET, 500)
        
    def speaker_control(self, enable):
        """ Enables or disables the emulated PC speaker. """
        if enable:
            GLOBAL_SPEAKER.play()
        else:
            GLOBAL_SPEAKER.stop()
            
    def read_port_c(self):
        """ Reads the value from the PORT C input, 0x062. """
        value = 0x00
        
        # If bit 3 is set, read the high DIP switches.
        if self.port_b_output & PORT_B_READ_SWITCHES_HIGH_NIBBLE:
            value = value | ((self.dip_switches >> 4) & 0x0F)
        else:
            value = value | self.dip_switches & 0x0F
            
        return value
        
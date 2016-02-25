#!/usr/bin/env python

# Standard library imports
import sys
from collections import namedtuple

# PyGame Imports
import pygame
from pygame.locals import *

# PyXT imports
from pyxt.chargen import CharacterGeneratorBIOS

# Constants
ScanCode = namedtuple("XTScanCode", ["make_codes", "break_codes"])

def XTScanCode(value):
    """ Helper function for creating XT scan code entries. """
    if value > 83:
        raise ValueError("An XT keyboard only has 83 keys!")
        
    return ScanCode((value, ), (value | 0x80, ))
    
PYGAME_KEY_TO_XT_SCANCODES = {
    # Pylint cannot infer the constants from Pygame.
    # pylint: disable=undefined-variable
    
    # First row, left to right across the keyboard.
    K_F1 : XTScanCode(0x3B),
    K_F2 : XTScanCode(0x3C),
    K_ESCAPE : XTScanCode(0x01),
    K_1 : XTScanCode(0x02),
    K_2 : XTScanCode(0x03),
    K_3 : XTScanCode(0x04),
    K_4 : XTScanCode(0x05),
    K_5 : XTScanCode(0x06),
    K_6 : XTScanCode(0x07),
    K_7 : XTScanCode(0x08),
    K_8 : XTScanCode(0x09),
    K_9 : XTScanCode(0x0A),
    K_0 : XTScanCode(0x0B),
    K_MINUS : XTScanCode(0x0C),
    K_EQUALS : XTScanCode(0x0D),
    K_BACKSPACE : XTScanCode(0x0E),
    K_NUMLOCK : XTScanCode(0x45),
    K_SCROLLOCK : XTScanCode(0x46),
    
    # Second row.
    K_F3 : XTScanCode(0x3D),
    K_F4 : XTScanCode(0x3E),
    K_TAB : XTScanCode(0x0F),
    K_q : XTScanCode(0x10),
    K_w : XTScanCode(0x11),
    K_e : XTScanCode(0x12),
    K_r : XTScanCode(0x13),
    K_t : XTScanCode(0x14),
    K_y : XTScanCode(0x15),
    K_u : XTScanCode(0x16),
    K_i : XTScanCode(0x17),
    K_o : XTScanCode(0x18),
    K_p : XTScanCode(0x19),
    K_LEFTBRACKET : XTScanCode(0x1A),
    K_RIGHTBRACKET : XTScanCode(0x1B),
    K_RETURN : XTScanCode(0x1C),
    K_KP7 : XTScanCode(0x47),
    K_KP8 : XTScanCode(0x48),
    K_KP9 : XTScanCode(0x49),
    K_KP_MINUS : XTScanCode(0x4A),
    
    # Third row.
    K_F5 : XTScanCode(0x3F),
    K_F6 : XTScanCode(0x40),
    K_LCTRL : XTScanCode(0x1D),
    K_a : XTScanCode(0x1E),
    K_s : XTScanCode(0x1F),
    K_d : XTScanCode(0x20),
    K_f : XTScanCode(0x21),
    K_g : XTScanCode(0x22),
    K_h : XTScanCode(0x23),
    K_j : XTScanCode(0x24),
    K_k : XTScanCode(0x25),
    K_l : XTScanCode(0x26),
    K_SEMICOLON : XTScanCode(0x27),
    K_QUOTE : XTScanCode(0x28),
    K_BACKQUOTE : XTScanCode(0x29),
    # K_RETURN already on second row.
    K_KP4 : XTScanCode(0x4B),
    K_KP5 : XTScanCode(0x4C),
    K_KP6 : XTScanCode(0x4D),
    K_KP_PLUS : XTScanCode(0x4E),
    
    # Fourth row.
    K_F7 : XTScanCode(0x41),
    K_F8 : XTScanCode(0x42),
    K_LSHIFT : XTScanCode(0x2A),
    K_BACKSLASH : XTScanCode(0x2B),
    K_z : XTScanCode(0x2C),
    K_x : XTScanCode(0x2D),
    K_c : XTScanCode(0x2E),
    K_v : XTScanCode(0x2F),
    K_b : XTScanCode(0x30),
    K_n : XTScanCode(0x31),
    K_m : XTScanCode(0x32),
    K_COMMA : XTScanCode(0x33),
    K_PERIOD : XTScanCode(0x34),
    K_SLASH : XTScanCode(0x35),
    K_RSHIFT : XTScanCode(0x36),
    K_KP_MULTIPLY : XTScanCode(0x37),
    K_KP1 : XTScanCode(0x4F),
    K_KP2 : XTScanCode(0x50),
    K_KP3 : XTScanCode(0x51),
    # K_KP_PLUS already on third row.
    
    # Fifth row.
    K_F9 : XTScanCode(0x43),
    K_F10 : XTScanCode(0x44),
    K_LALT : XTScanCode(0x38),
    K_SPACE : XTScanCode(0x39),
    K_CAPSLOCK : XTScanCode(0x3A),
    K_KP0 : XTScanCode(0x52),
    K_KP_PERIOD : XTScanCode(0x53),
    # K_KP_PLUS already on third row.
    
    # pylint: enable=undefined-variable
}

assert len(PYGAME_KEY_TO_XT_SCANCODES) == 83

BLACK = (0x00, 0x00, 0x00)
GREEN = (0x00, 0xC0, 0x00)

# Functions

# Classes
class XTHardware(object):
    def __init__(self):
        pass
        
    def handle_keydown(self, event):
        if event.key == K_BACKSLASH and event.mod | KMOD_CTRL:
            print "ITS TIME TO GO"
            sys.exit()
            
        scancodes = PYGAME_KEY_TO_XT_SCANCODES.get(event.key, None)
        if scancodes is not None:
            print scancodes.make_codes
        else:
            print event
        
    def handle_keyup(self, event):
        scancodes = PYGAME_KEY_TO_XT_SCANCODES.get(event.key, None)
        if scancodes is not None:
            print scancodes.break_codes
        else:
            print event
            
# Main application
def main():
    print "PyXT UI"
    pygame.init()
    
    size = width, height = 720, 350
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("PyXT")
    screen.fill(BLACK)
    
    hw = XTHardware()
    cg = CharacterGeneratorBIOS(sys.argv[1])
    print "LOADING FONT..."
    
    print "GO"
    cursor = [0, 0]
    while True:
        for event in pygame.event.get():
            # print event
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                hw.handle_keydown(event)
                
                try:
                    char = ord(event.unicode.encode("ascii"))
                except Exception:
                    continue
                    
                cg.blit_character(screen, cursor, char)
                pygame.display.flip()
                cursor[0] += cg.char_width
                if cursor[0] > 720:
                    cursor[0] = 0
                    cursor[1] += cg.char_height
                    
            elif event.type == pygame.KEYUP:
                hw.handle_keyup(event)
                
if __name__ == "__main__":
    main()
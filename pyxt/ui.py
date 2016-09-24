#!/usr/bin/env python

"""
pyxt.ui - Pygame wrapper for PyXT.
"""

# Standard library imports
import sys
from collections import namedtuple

# PyGame Imports
import pygame
from pygame.locals import *

# Pyglet Imports
import pyglet
from pyglet.window import key

# PyXT imports
from pyxt.interface import KeyboardController
from pyxt.mda import MonochromeDisplayAdapter, CharacterGeneratorMDA_CGA_ROM

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants
UPDATE_DISPLAY = USEREVENT + 0

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

PYGLET_KEY_TO_XT_SCANCODES = {
    # First row, left to right across the keyboard.
    key.F1 : XTScanCode(0x3B),
    key.F2 : XTScanCode(0x3C),
    key.ESCAPE : XTScanCode(0x01),
    key._1 : XTScanCode(0x02),
    key._2 : XTScanCode(0x03),
    key._3 : XTScanCode(0x04),
    key._4 : XTScanCode(0x05),
    key._5 : XTScanCode(0x06),
    key._6 : XTScanCode(0x07),
    key._7 : XTScanCode(0x08),
    key._8 : XTScanCode(0x09),
    key._9 : XTScanCode(0x0A),
    key._0 : XTScanCode(0x0B),
    key.MINUS : XTScanCode(0x0C),
    key.EQUAL : XTScanCode(0x0D),
    key.BACKSPACE : XTScanCode(0x0E),
    key.NUMLOCK : XTScanCode(0x45),
    key.SCROLLLOCK : XTScanCode(0x46),
    
    # Second row.
    key.F3 : XTScanCode(0x3D),
    key.F4 : XTScanCode(0x3E),
    key.TAB : XTScanCode(0x0F),
    key.Q : XTScanCode(0x10),
    key.W : XTScanCode(0x11),
    key.E : XTScanCode(0x12),
    key.R : XTScanCode(0x13),
    key.T : XTScanCode(0x14),
    key.Y : XTScanCode(0x15),
    key.U : XTScanCode(0x16),
    key.I : XTScanCode(0x17),
    key.O : XTScanCode(0x18),
    key.P : XTScanCode(0x19),
    key.BRACKETLEFT : XTScanCode(0x1A),
    key.BRACKETRIGHT : XTScanCode(0x1B),
    key.RETURN : XTScanCode(0x1C),
    key.NUM_7 : XTScanCode(0x47),
    key.NUM_8 : XTScanCode(0x48),
    key.NUM_9 : XTScanCode(0x49),
    key.NUM_SUBTRACT : XTScanCode(0x4A),
    
    # Third row.
    key.F5 : XTScanCode(0x3F),
    key.F6 : XTScanCode(0x40),
    key.LCTRL : XTScanCode(0x1D),
    key.A : XTScanCode(0x1E),
    key.S : XTScanCode(0x1F),
    key.D : XTScanCode(0x20),
    key.F : XTScanCode(0x21),
    key.G : XTScanCode(0x22),
    key.H : XTScanCode(0x23),
    key.J : XTScanCode(0x24),
    key.K : XTScanCode(0x25),
    key.L : XTScanCode(0x26),
    key.SEMICOLON : XTScanCode(0x27),
    key.DOUBLEQUOTE : XTScanCode(0x28),
    key.QUOTELEFT : XTScanCode(0x29),
    # key.RETURN already on second row.
    key.NUM_4 : XTScanCode(0x4B),
    key.NUM_5 : XTScanCode(0x4C),
    key.NUM_6 : XTScanCode(0x4D),
    key.NUM_ADD : XTScanCode(0x4E),
    
    # Fourth row.
    key.F7 : XTScanCode(0x41),
    key.F8 : XTScanCode(0x42),
    key.LSHIFT : XTScanCode(0x2A),
    key.BACKSLASH : XTScanCode(0x2B),
    key.Z : XTScanCode(0x2C),
    key.X : XTScanCode(0x2D),
    key.C : XTScanCode(0x2E),
    key.V : XTScanCode(0x2F),
    key.B : XTScanCode(0x30),
    key.N : XTScanCode(0x31),
    key.M : XTScanCode(0x32),
    key.COMMA : XTScanCode(0x33),
    key.PERIOD : XTScanCode(0x34),
    key.SLASH : XTScanCode(0x35),
    key.RSHIFT : XTScanCode(0x36),
    key.NUM_MULTIPLY : XTScanCode(0x37),
    key.NUM_1 : XTScanCode(0x4F),
    key.NUM_2 : XTScanCode(0x50),
    key.NUM_3 : XTScanCode(0x51),
    # key.NUM__PLUS already on third row.
    
    # Fifth row.
    key.F9 : XTScanCode(0x43),
    key.F10 : XTScanCode(0x44),
    key.LALT : XTScanCode(0x38),
    key.SPACE : XTScanCode(0x39),
    key.CAPSLOCK : XTScanCode(0x3A),
    key.NUM_0 : XTScanCode(0x52),
    key.NUM_DECIMAL : XTScanCode(0x53),
    # key.NUM__PLUS already on third row.
}

assert len(PYGLET_KEY_TO_XT_SCANCODES) == 83

# Functions

# Classes
class PygameManager(object):
    """ Manages interactions with the Pygame UI for PyXT. """
    def __init__(self, keyboard, display):
        self.keyboard = keyboard
        self.display = display
        self.display.reset()
        pygame.time.set_timer(UPDATE_DISPLAY, 20)
        
    def poll(self):
        """ Run one iteration of the Pygame machine. """
        for event in pygame.event.get():
            if event.type == QUIT:
                log.critical("Pygame QUIT detected, powering down...")
                sys.exit()
                
            elif event.type == KEYDOWN:
                scancode = PYGAME_KEY_TO_XT_SCANCODES.get(event.key, None)
                if scancode:
                    self.keyboard.key_pressed(scancode.make_codes)
                    
            elif event.type == KEYUP:
                scancode = PYGAME_KEY_TO_XT_SCANCODES.get(event.key, None)
                if scancode:
                    self.keyboard.key_pressed(scancode.break_codes)
                    
            elif event.type == UPDATE_DISPLAY:
                self.display.draw()
                
class PygletManager(object):
    def __init__(self, keyboard, display):
        self.keyboard = keyboard
        self.display = display
        self.display.reset()
        self.display.screen.push_handlers(on_key_press = self.on_key_press)
        self.display.screen.push_handlers(on_key_release = self.on_key_release)
        self.display.screen.push_handlers(on_close = self.on_close)
        pyglet.clock.schedule_interval(self.draw, 0.02)
        self.count = 0
        
    def on_key_press(self, symbol, modifiers):
        scancode = PYGLET_KEY_TO_XT_SCANCODES.get(symbol, None)
        if scancode:
            self.keyboard.key_pressed(scancode.make_codes)
        
    def on_key_release(self, symbol, modifiers):
        scancode = PYGLET_KEY_TO_XT_SCANCODES.get(symbol, None)
        if scancode:
            self.keyboard.key_pressed(scancode.break_codes)
        
    def on_close(self):
        log.critical("Pyglet on_close detected, powering down...")
        sys.exit()
        
    def poll(self):
        """ Run one iteration of the Pyglet machine. """
        self.count += 1
        
        if self.count % 10 == 0:
            pyglet.clock.tick()
            
            for window in pyglet.app.windows:
                window.switch_to()
                window.dispatch_events()
                
    def draw(self, value):
        self.display.draw()
        
# Main application
def main():
    """ Test application for this module. """
    log.info("PyXT UI test application.")
    
    class DemoKeyboard(KeyboardController):
        """ Keyboard controller that prints the scancodes to the display. """
        def __init__(self, mda_card):
            self.x = 0
            self.y = 0
            self.mda_card = mda_card
            
        def key_pressed(self, scancode):
            addr = int((self.y * 160) + (self.x * 2))
            self.mda_card.mem_write_byte(addr, scancode[0])
            self.x += 1
            if self.x >= 80:
                self.x = 0
                self.y = (self.y + 1) % 25
                
    char_generator = CharacterGeneratorMDA_CGA_ROM(sys.argv[1])
    mda_card = MonochromeDisplayAdapter(char_generator)
    
    keyboard = DemoKeyboard(mda_card)
    
    manager = PygletManager(keyboard, mda_card)
    while True:
        manager.poll()
        
if __name__ == "__main__":
    main()
    
"""
pyxt.speaker - High-level emulation of the PC speaker using Pygame.

https://en.wikipedia.org/wiki/PC_speaker
"""

# Standard library imports
import sys
import array

# Six imports
from six.moves import range # pylint: disable=redefined-builtin

# PyXT imports

# Pygame imports
import pygame

# Logging setup
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Constants
SAMPLE_RATE = 44100
SIZE = -16
CHANNELS = 1
MIN_SHORT = -32768
MAX_SHORT = 32767
BUS_FREQUENCY = 1193181.8181

# Module-level init for Pygame mixer, must be called before anything else.+
pygame.mixer.pre_init(SAMPLE_RATE, SIZE, CHANNELS)

# Classes
class PCSpeaker(object):
    """ Class for generating PC-speaker style sounds with Pygame. """
    def __init__(self):
        self.data = array.array("h", (0,) * SAMPLE_RATE)
        self.frequency = 0
        self.needs_replay = False
        self.sound = None
        
    def set_tone(self, frequency):
        """ Generate a square wave for a given frequency. """
        # Don't divide by zero or go thru this again for the same frequency.
        if frequency > 0 and frequency != self.frequency:
            
            period = float(SAMPLE_RATE) / (frequency * 2)
            if int(period) == 0:
                return
            for index in range(SAMPLE_RATE):
                self.data[index] = MIN_SHORT if (index // int(period)) & 0x1 else MAX_SHORT
                
            self.frequency = frequency
            self.needs_replay = True
            
            if self.sound is not None:
                self.play()
                
    def set_tone_from_counter(self, count):
        """ Sets the tone from the 8253 counter value. """
        freq = int(round(BUS_FREQUENCY / count))
        self.set_tone(freq)
                
    def play(self):
        """ Plays the loaded sound until stopped. """
        if self.needs_replay:
            self.needs_replay = False
            self.stop()
                
            self.sound = pygame.mixer.Sound(buffer = self.data)
            self.sound.play(loops = -1)
        
    def stop(self):
        """ Stop a playing sound. """
        if self.sound is not None:
            self.sound.stop()
            self.sound = None
            self.needs_replay = True
            
# TODO: Find a clean way to pass this into the PPI and PIT objects to avoid the global.
GLOBAL_SPEAKER = PCSpeaker()
            
def main():
    """ Test application. """
    pygame.init()
    
    tone = 440
    
    spk = PCSpeaker()
    spk.set_tone(tone)
    spk.play()
    
    pygame.display.set_mode((640, 480))
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.unicode == u"+":
                    tone += 100
                    print(tone)
                    spk.set_tone(tone)
                    spk.play()
                    
                elif event.unicode == u"-":
                    tone -= 100
                    print(tone)
                    spk.set_tone(tone)
                    spk.play()
                    
            elif event.type == pygame.QUIT:
                sys.exit()
    
if __name__ == "__main__":
    main()
    
        
    
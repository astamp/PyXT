"""
pyxt.interfaces - Interfaces for different device types used by the UI classes.
"""

# Classes
class DisplayAdapter(object):
    """ Interface for a PyGame display adapter. """
    
    def get_resolution(self):
        """ Returns a tuple (width, height) of the display size. """
        raise NotImplementedError
        
class KeyboardController(object):
    """ Interface for a PyGame keyboard controller. """
    
    def key_pressed(self, scancodes):
        """ Function called when one or more scancodes are ready for the controller. """
        raise NotImplementedError
        
    def self_test_complete(self):
        """ Function called when the keyboard controller self-test is complete. """
        raise NotImplementedError
        
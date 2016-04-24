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
    
    def key_pressed(self, scancode):
        """ Function called when a scancode is ready for the controller. """
        raise NotImplementedError
        
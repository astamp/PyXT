"""
pyxt.tests.utils - Helpers for writing unit tests.
"""

import os
import inspect

from pyxt.bus import SystemBus

def get_test_file(suite, filename):
    """ Get the path to a test file for a given suite. """
    return os.path.join(
        os.path.dirname(inspect.getfile(suite.__class__)),
        "files",
        filename,
    )

class InterruptControllerSpy(object):
    """ Stubs out the interrupt controller for testing. """
    def __init__(self):
        self.irq_log = []
        
    def interrupt_request(self, irq):
        self.irq_log.append(irq)
        
    def interrupt_pending(self):
        return False
        
class SystemBusTestable(SystemBus):
    """ System bus object for unit testing. """
    def __init__(self):
        super(SystemBusTestable, self).__init__(InterruptControllerSpy(), None)
        
    def get_irq_log(self):
        """ Return the list if IRQs fired. """
        return self.pic.irq_log
        
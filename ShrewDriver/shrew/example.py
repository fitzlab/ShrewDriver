from __future__ import division
"""

This is an example shrew file with some handy test functions and

Each function in the shrew file is a task. The task is run when started by the UI.
While typically you would use a training task (go/nogo etc.), really any function can be used.
For example, in anesthetized imaging, you may want to simply show a sequence of stimuli, without any behavior feedback.
Or, you may want to write a small task that tests out some part of the system.

All the task functions take a single argument, which is a reference to the main UI.
That way, they can see any parameters / options specified there.

Each class in the shrew file is a configuration.
The configuration determines which hardware devices will be used.
For example, when training in the ARC, we use the Nexus 10 tablets to display the stimulus,
but when training in the imaging room, the stimulus is displayed on a computer monitor via PsychoPy.

"""

import sys
sys.path.append('..')

from shrew.shrew import Shrew

# --- Task functions --- #
def screen_test(mainUI):
    """

    """
    print "screen_test"
    animal = mainUI.selectedAnimal  # type: Shrew
    config = mainUI.selectedConfig  # type: object

    print animal.name
    print config.__dict__


def anesthetized(mainUI):
    """

    """
    print "things"

    animal = mainUI.selectedAnimal  # type: Shrew
    config = mainUI.selectedConfig  # type: object

    print animal.name
    print config.__dict__
    while not mainUI.stopTask:
        pass

    print "Thread complete!"

# --- Configuration classes --- #
class NexusTest:
    """
    For testing of sending stimuli to the screen (Nexus 10)
    """
    def __init__(self):
        self.stimDevice = "COM12"

class PsychoPy:
    """
    For testing of sending stimuli to the screen (PsychoPy)
    """
    def __init__(self):
        self.stimDevice = "PsychoPy"

class ARC:
    """
    Configuration typically used in the ARC:
    A webcam plus three serial ports for sensors/stim/syringe pump.
    """

    def __init__(self):
        self.sensorPort = "COM10"
        self.syringePort = "COM11"
        self.stimDevice = "COM12"
        self.cameraID = 2

class AnesthetizedImaging:
    """
    For anesthetized imaging, we will just be putting things on the screen.
    We'll need the DAQ as well, to notify Spike2 what our stimuli were.
    """

    def __init__(self):
        self.stimDevice = "PsychoPy"
        self.useDaq = True

class AwakeBehavingImaging:
    """

    """

    def __init__(self):
        self.sensorPort = "COM90"
        self.syringePort = "COM91"
        self.stimDevice = "PsychoPy"
        self.cameraID = 2

        self.useDaq = True
        self.interactUI = True  # Enable UI for manually giving rewards, controlling screen, etc.
        self.sensorUI = True  # Show detailed readouts for tap and lick sensors

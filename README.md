ShrewDriver
===========

Automated training system for training multiple animals to discriminate visual stimuli. 

Using it, one experimenter can train many animals simultaneously:

Core Python code is in the ShrewDriver directory. "shrewdriver.py" runs training. 

"shrew_graphs.py" is a tool for analysis and display of historical training data. Details of invididual sessions as well as overall performance history can be viewed:

![](https://github.com/fitzlab/ShrewDriver/blob/master/Documentation/shrew_graphs.png)

PyQt is used for UI. Plotting is done using the excellent [pyqtgraph library](https://github.com/pyqtgraph/pyqtgraph).

Visual stimuli for monitors using the PsychoPy library. ShrewDriver can also display to Nexus 10 tablets; code for the Nexus 10 display app is in the Stimbot directory.

Firmware for the electronic components (sensors, syringe pump, and air puff) is in the Arduino directory.

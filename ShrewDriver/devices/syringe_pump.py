from __future__ import division
import sys
sys.path.append("..")


from serial_port import SerialPort

class SyringePump(SerialPort):
    
    def __init__(self, serialPortName):
        super(SyringePump, self).__init__(serialPortName)
        self.total_mL = 0
    
    def bolus(self, mL):
        self.write(str(mL*1000) + "\n")
        self.total_mL += mL

        #self.serialPort = SerialPort(serialPortName)
        #self.serialPort.startReadThread()        
        
        #self.dispensed_mL = 0
    
    #def bolus(self, amount):
        #pass
    
    
from serial_port import SerialPort
import time

# handles communications with the display tablet
# consider that this will eventually be a PsychoPy communication mechanism as well!

class Stimbot(SerialPort):
    
    def __init__(self, serialPortName):
        SerialPort.__init__(self, serialPortName)
        Renderer.__init__(self)
        
        #turn screen on, if needed
        time.sleep(0.1) 
        self.write('screenon')        
    
    def setUpCommands(self,commandStrings):
        #set up stimbot commands for later use
        for (i,commandString) in enumerate(commandStrings):
            time.sleep(0.1) #wait a bit between long commands to make sure serial sends everything
            saveCommand = 'save' + str(i) + ' ' + commandString
            self.write(saveCommand)    

if __name__ == '__main__':
    stimbot = Stimbot('COM92')
    
    stimbot.setUpCommands(["sx0 sy0", "ac pab sx50 sy50", "as paw sx50 sy50"])

    stimbot.setScreenDistance(100)

    for n in range(0,10):
        for i in range(0,3):
            print "Doing command " + str(i)
            stimbot.write(str(i))
            time.sleep(1)

    print "Done!"
    
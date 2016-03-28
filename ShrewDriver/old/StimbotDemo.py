from devices.SerialPort import SerialPort
import time, random

# Connects to a tablet running Stimbot at sends commands that show off features
# Edit the main function at the bottom of the file to run.

def stimbotDemo(portName):
    serial = SerialPort(portName)
    
    commandTime = 4
    
    serial.write('screenon\n')
    serial.write('screendist800\n')
    
    while True:
        #sinusoidal Gabor
        serial.write('ag sin0 tf1 jf0 ja0 sf0.5 sx10 sy10 px0 py0\n')
        time.sleep(commandTime)
        
        #Temporal + spatial frequency, square wave
        serial.write('sqr45 tf3 sf3\n')
        time.sleep(commandTime)
        
        #size change
        serial.write('ac sqr90 sx6 sy4 tf1.5 sf0.5\n')
        time.sleep(commandTime)
        
        #position change and jitter
        serial.write('ag sqr135 jf5 ja0.2 tf0 px-4 py0 sx6 sy6\n')
        time.sleep(commandTime)
        
        #phase demo
        serial.write('as sin180 px0 py0 sx8 sy6 jf0 ja0 ph0\n')
        time.sleep(commandTime/4)
        
        serial.write('ph0.5\n')
        time.sleep(commandTime/4)
        
        serial.write('ph0.75\n')
        time.sleep(commandTime/4)
        
        serial.write('ph0.25\n')
        time.sleep(commandTime/4)
        
        #jitter + drift at the same time
        serial.write('ac sin225 sx5 sy5 tf1.5 jf5 ja0.5 ph0\n')
        time.sleep(commandTime)
        
        #various color patches
        serial.write('ac pab jf0 ja0 sx3 sy3 px-4 py0\n')
        time.sleep(commandTime/2)
        
        serial.write('ag par sx5 sy5  px4 py0\n')
        time.sleep(commandTime/2)
        
        serial.write('as pay sx4 sy4 px0 py3\n')
        time.sleep(commandTime/2)
        

def saveCommandsDemo(portName):
    serial = SerialPort(portName)
    
    serial.write('screenon\n')
    serial.write('screendist800\n')
    
    #save a set of commands
    #it's important to wait a short time between commands
    cmdWait = 0.050
    serial.write('save0 ac paw px0 py0 sx3 sy3\n')
    time.sleep(cmdWait)
    serial.write('save1 as pam px0 py0 sx2 sy2\n')
    time.sleep(cmdWait)
    serial.write('save2 ag sqr22.5 px0 py0 sx8 sy8 ja0 jf0 tf2\n')
    time.sleep(cmdWait)
    serial.write('save3 ac sin0.0 px-4 py0 sx5 sy5 ja0.3 jf3 tf0\n')
    time.sleep(cmdWait)
    serial.write('save4 as sin89.5 px4 py0 sx5 sy5 ja0 jf0 tf1\n')
    time.sleep(cmdWait)
    
    #randomly pick commands and run them
    while True:
        stimNumber = random.randint(0,4)
        serial.write(str(stimNumber) + "\n")
        time.sleep(2)
    
def latencyTest(portName):
    serial = SerialPort(portName)
    
    serial.write('screenon\n')
    serial.write('screendist800\n')
    
    #save a set of commands
    #it's important to wait a short time between commands
    cmdWait = 0.050
    serial.write('save0 ac paw px0 py0 sx3 sy3\n')
    time.sleep(cmdWait)
    serial.write('save1 as pam px0 py0 sx2 sy2\n')
    time.sleep(cmdWait)
    serial.write('save2 ag sqr22.5 px0 py0 sx8 sy8 ja0 jf0 tf2\n')
    time.sleep(cmdWait)
    serial.write('save3 ac sin0.0 px-4 py0 sx5 sy5 ja0.3 jf3 tf0\n')
    time.sleep(cmdWait)
    serial.write('save4 as sin89.5 px4 py0 sx5 sy5 ja0 jf0 tf1\n')
    time.sleep(cmdWait)
    
    #run commands fast
    for i in xrange(0,10000):
        stimNumber = i % 5
        serial.write(str(stimNumber) + " sqr45 ph0.05" + "\n")
        time.sleep(0.05) #looks like we can run a command every 25ms
    

def screenDistCheck(portName):
    serial = SerialPort(portName)
    serial.write('ac\n')
    
    while True:
        #both of these should produce circles, of very close to the same size.
        time.sleep(1)
        serial.write('pab screendist100 sx44 sy44\n')
        time.sleep(1)
        serial.write('paw screendist1000 sx5 sy5\n')
        

def testStimsForTraining(portName):
    serial = SerialPort(portName)
    serial.write('\n')

if __name__ == '__main__':
    portName = 'COM34' #Set this to the serial port that connects to Stimbot
    
    #Uncomment a demo below to run it!
    
    #stimbotDemo(portName))
    #saveCommandsDemo(portName)
    screenDistCheck(portName)
    #latencyTest(portName)
    
import serial, time, re, threading, sys, traceback

class SerialPort():
    # This class talks to an Arduino and reads the raw data from it, adding timestamps.
    # This data is read by both the training program and the live plotting display. 
    # SerialPort accepts write commands from the training program to command the stimulus tablet.
    
    def __init__(self, serialPortName):
        #serial port setup
        self.serialPortName = int(serialPortName[3:])-1
        self.baudRate = 57600
        print "Opening serial port [" + serialPortName + "] at " + str(self.baudRate) 
        self.ser = serial.Serial(self.serialPortName, self.baudRate, timeout=5)
        self.updates = []
        self.threadLock = threading.Lock()
        
        self.startTimeMillis = time.time()*1000
        
        self.stopFlag = False
        self.SLEEP_TIME = 0.0001 #prevents polling thread from eating up all the CPU
        
    def getUpdates(self):
        #returns all of the raw text received since the last poll.
        updatesToReturn = self.updates
        with self.threadLock:
            self.updates = []
        return updatesToReturn
    
    def readSerial(self):
        bytes = ''
        while bytes == '' and not self.stopFlag:
            bytes = self.ser.readline()
        return bytes
    
    def readData(self):
        while not self.stopFlag:
            time.sleep(self.SLEEP_TIME)
            data = self.readSerial()
            timeStr = str(time.time())
            byteStr = str(data).rstrip() + ' ' + timeStr
            if byteStr != '' and byteStr != '\n': 
                with self.threadLock:
                    self.updates.append(byteStr)
    
    def close(self):
        """For closing serial at end of task"""
        self.stopFlag = True
        time.sleep(0.1)
        self.ser.close()
    
    def reopen(self):
        """In case of failure, reopen serial. Read/write lock is acquired while reopening."""
        print "Reopening serial after write failure..."
        with self.threadLock:
            self.ser.close()
            self.ser = serial.Serial(self.serialPortName, self.baudRate, timeout=5)
            time.sleep(2)
        print "Opened."
        

    def write(self, command):
        try:
            self.ser.write(command)
        except Exception as e:
            print traceback.format_exception(*sys.exc_info())
            self.reopen()

    def startReadThread(self):
        self.stopFlag = False
        thread = threading.Thread(target=self.readData)
        thread.daemon = True
        thread.start()
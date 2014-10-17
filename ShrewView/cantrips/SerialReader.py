import serial, time, re, threading

class SerialReader():
    # This class talks to an Arduino and reads the raw data from it, adding timestamps.
    # It updates the sensor data variables, triggering updates to the live plot.
    
    def __init__(self, serialPortName):
        #serial port setup
        self.serialPortName = serialPortName
        
        self.ser = serial.Serial(self.serialPortName, 9600, timeout=5)
        self.updates = []
        self.threadLock = threading.Lock()
        
        self.startTimeMillis = time.time()*1000
        
        self.SLEEP_TIME = 0.0001 #prevents polling thread from eating up all the CPU
        
    def getUpdates(self):
        #returns all of the raw text received since the last poll.
        updatesToReturn = self.updates
        with self.threadLock:
            self.updates = []
        return updatesToReturn
        
    def readSerial(self):
        bytes = ''
        while bytes == '':
            bytes = self.ser.readline()
        return bytes
    
    def readData(self):
        while True:
            time.sleep(self.SLEEP_TIME)
            data = self.readSerial()
            timeStr = str(long(time.time()*1000 - self.startTimeMillis))
            byteStr = str(data).rstrip() + ' ' + timeStr
            if byteStr != '' and byteStr != '\n': 
                with self.threadLock:
                    self.updates.append(byteStr)
                    
    def startReadThread(self):
        thread = threading.Thread(target=self.readData)
        thread.daemon = True
        thread.start()
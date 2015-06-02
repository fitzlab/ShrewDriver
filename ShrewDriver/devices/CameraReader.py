from __future__ import division
import cv2, time, threading

#Captures and saves webcam video
#Does not capture audio!

class CameraReader():
    
    def __init__(self, cameraID, vidPath, animalName):
        self.stopFlag = False
        self.frameRate = 15 #frames per second
        self.windowName = animalName + ' - Camera (' + str(cameraID) + ")"
        
        #set up frame acquisition, display, and disk writing
        self.cap = cv2.VideoCapture(cameraID)
        self.readFrame()
        rows,cols,channels = self.frame.shape
        self.video  = cv2.VideoWriter(vidPath, cv2.cv.CV_FOURCC('X','V','I','D'), self.frameRate, (cols,rows));
    
    def readFrame(self):
        ret, self.frame = self.cap.read()
        
    def captureFrame(self):
        self.readFrame()
        rows,cols,channels = self.frame.shape
        if rows == 0 or cols == 0:
            #Once in a while, a bad frame comes off the camera. Skip it.
            return
        self.frame = cv2.flip(self.frame, -1) #rotate frame 180
        self.video.write(self.frame)
        cv2.imshow(self.windowName, self.frame); 
        cv2.waitKey(1) #pauses 1ms, allows frame to display

    def stopCapture(self):
        # When everything done, release the capture
        self.video.release()
        self.cap.release()
        cv2.destroyAllWindows()
    
    def acquire(self):
        #thread function, loops capture until stopped
        #blocking happens automatically at self.cap.read() so this won't consume
        #much CPU. No need for a sleep() call.
        while True:
            self.captureFrame()
            if self.stopFlag:
                self.stopCapture()
                break
        
    def startReadThread(self):
        self.stopFlag = False
        thread = threading.Thread(target=self.acquire)
        thread.daemon = True
        thread.start()
    
if __name__ == '__main__':
    #set up CameraReader object
    cameraID = 0
    vidPath = '../../shrewData/video' + str(cameraID) + '.avi'
    cr = CameraReader(cameraID, vidPath)
    
    #start it running
    cr.startReadThread()
    
    #keep busy while it runs
    startTime = time.time()
    while time.time() - startTime < 10:
        time.sleep(0.001)
        pass
    
    #stop it, and wait for it to shut down nicely
    cr.stopFlag = True
    print "Saving video to " + vidPath
    time.sleep(1)
    print "done!"


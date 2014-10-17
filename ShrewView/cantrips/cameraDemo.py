import numpy as np
import cv2
from scipy.interpolate import griddata

cap = cv2.VideoCapture(0)

img = np.zeros((480,640,3), np.uint8)
cv2.line(img,(0,0),(450,450),(255,0,0),5)

ret, prevFrame = cap.read()
rows,cols,channels = prevFrame.shape

cv2.namedWindow("Defenestraight to my heart")

detector = cv2.FastFeatureDetector(15)

while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()
    keypoints = detector.detect(frame)
    prevKeypoints = detector.detect(prevFrame)
    
    outImg = cv2.drawKeypoints(frame, keypoints)
    
    cv2.imshow("Defenestraight to my heart", outImg); 
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
    prevFrame = frame

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
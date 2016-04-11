from __future__ import division
import sys
sys.path.append("..")

import cv2

from PyQt4.QtCore import QPoint, QTimer
from PyQt4.QtGui import QApplication, QImage, QPainter, QWidget


class IplQImage(QImage):
    """
    http://matthewshotton.wordpress.com/2011/03/31/python-opencv2-iplimage-to-pyqt-qimage/
    A class for converting iplimages to qimages
    """

    def __init__(self,iplimage):
        alpha = cv2.CreateMat(iplimage.height,iplimage.width, cv2.cv2_8UC1)
        cv2.Rectangle(alpha, (0, 0), (iplimage.width,iplimage.height), cv2.ScalarAll(255) ,-1)
        rgba = cv2.CreateMat(iplimage.height, iplimage.width, cv2.cv2_8UC4)
        cv2.Set(rgba, (1, 2, 3, 4))
        cv2.MixChannels([iplimage, alpha],[rgba], [
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3)  
        ])
        self.__imagedata = rgba.tostring()
        super(IplQImage,self).__init__(self.__imagedata, iplimage.width, iplimage.height, QImage.Format_RGB32)


class MovieWidget(QWidget):
    """ A class for rendering video coming from Opencv2 """

    def __init__(self, parent=None):
        QWidget.__init__(self)
        self._frame = None
        self._image = None
        
        #capture setup
        self._capture = cv2.VideoCapture(0)        

        # Paint every 50 ms
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.queryFrame)
        self._timer.start(50)

    def _build_image(self):
        if not self._frame:
            self._image = None
        else:
            self._image = IplQImage(self._frame)

    def paintEvent(self, event):
        if self._image is not None:
            painter = QPainter(self)
            painter.drawImage(QPoint(0, 0), self._image)

    def queryFrame(self):
        self._frame = self._capture.read()
        self._build_image()
        self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    widget = VideoWidget()
    widget.setWindowTitle('PyQt - Opencv2 Test')
    widget.show()

    sys.exit(app.exec_())
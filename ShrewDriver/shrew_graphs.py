from __future__ import division
import sys
from PyQt4 import QtCore, QtGui, uic

from ui import graph_ui

if __name__ == '__main__':
    print "Loading shrew data..."
    app = QtGui.QApplication(sys.argv)
    graphUI = graph_ui.GraphUI(None)
    graphUI.show()
    app.exec_()

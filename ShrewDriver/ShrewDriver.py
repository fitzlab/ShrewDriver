import sys
from PyQt4 import QtCore, QtGui, uic

from ui import main_ui

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainUI = main_ui.MainUI(None)
    mainUI.show()
    app.exec_()

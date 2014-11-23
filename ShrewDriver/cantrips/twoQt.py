import sys
from pyqtgraph.Qt import QtGui, QtCore

def main():
    app = QtGui.QApplication(sys.argv)
    ex = QtGui.QWidget()
    ex.show()
    ex2 = QtGui.QWidget()
    ex2.show()
    QtGui.QApplication.instance().exec_()
    #sys.exit(app.exec())
   
if __name__ == '__main__':
    main()
    print 'done'
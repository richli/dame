__author__ = "Richard Lindsley"

import sys, os

import sip
sip.setapi('QDate', 2)
sip.setapi('QDateTime', 2)
sip.setapi('QString', 2)
sip.setapi('QTextStream', 2)
sip.setapi('QTime', 2)
sip.setapi('QUrl', 2)
sip.setapi('QVariant', 2)
from PyQt4 import QtCore,QtGui

from .ui.mainwindow import MainWindow
from loadsir import loadsir

#class Dame(QtGui.QApplication):

def main():
    qt_app = QtGui.QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    qt_app.exec_()

if __name__ == "__main__":
    main()

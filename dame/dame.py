__author__ = "Richard Lindsley"

import sys

import sip
sip.setapi('QDate', 2)
sip.setapi('QDateTime', 2)
sip.setapi('QString', 2)
sip.setapi('QTextStream', 2)
sip.setapi('QTime', 2)
sip.setapi('QUrl', 2)
sip.setapi('QVariant', 2)
from PyQt4 import Qt

def main():
    qt_app = Qt.QApplication(sys.argv)
    label = Qt.QLabel("Hello, world")
    label.show()
    qt_app.exec_()

if __name__ == "__main__":
    main()

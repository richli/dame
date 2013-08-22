__author__ = "Richard Lindsley"

import sys

#import sip
#sip.setapi('QDate', 2)
#sip.setapi('QDateTime', 2)
#sip.setapi('QString', 2)
#sip.setapi('QTextStream', 2)
#sip.setapi('QTime', 2)
#sip.setapi('QUrl', 2)
#sip.setapi('QVariant', 2)
#from PyQt4 import Qt

from PySide.QtCore import *
from PySide.QtGui import *


def main():
    qt_app = QApplication(sys.argv)
    label = QLabel("Hello, world")
    label.show()
    qt_app.exec_()

if __name__ == "__main__":
    main()

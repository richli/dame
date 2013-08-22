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
from main_window import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

def main():
    qt_app = QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    qt_app.exec_()

if __name__ == "__main__":
    main()

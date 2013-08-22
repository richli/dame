__author__ = "Richard Lindsley"

import sys, os

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

from loadsir import loadsir

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        # Menu handlers
        self.actionAbout.triggered.connect(self.menu_about)
        self.actionOpen.triggered.connect(self.menu_open)
        self.actionClose.triggered.connect(self.menu_close)

        # Status bar
        self.statusbar.showMessage("No file loaded")

    def menu_about(self):
        """ Display about popup """
        QMessageBox.about(self, "About", 
                "Dame\nCopyright 2013 Richard Lindsley\nDame is a SIR file viewer")
        
    def menu_open(self):
        """ Display open file dialog """
        filename, file_filter = QFileDialog.getOpenFileName(self, 
                "Open SIR file", 
                os.getenv("HOME", os.getcwd()), 
                "SIR files (*.sir *.ave);;Any file (*)"
                )
        if filename != '':
            pass # TODO: Open the file

    def menu_close(self):
        """ Close file """
        print("close clicked")

def main():
    qt_app = QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    qt_app.exec_()

if __name__ == "__main__":
    main()

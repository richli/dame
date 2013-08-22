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

        # Add icons to menu items (can't seem to do it in Qt Designer)
        # http://stackoverflow.com/questions/11643221/are-there-default-icons-in-pyqt-pyside
        QIcon.setThemeName("gnome") # TODO: temporary
        self.actionQuit.setIcon(QIcon.fromTheme("application-exit"))
        self.actionOpen.setIcon(QIcon.fromTheme("document-open"))
        self.actionAbout.setIcon(QIcon.fromTheme("help-about"))
        self.actionClose.setIcon(QIcon.fromTheme("window-close"))

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
            self.load_sir(filename)

    def menu_close(self):
        """ Close file """
        print("close clicked")

    def load_sir(self, fname):
        """ Loads the SIR file and updates display """
        self.sirdata = loadsir(fname)
        self.update_image()

    def update_image(self):
        """ Reload the image """
        nsx = int(self.sirdata[1][0].astype('int'))
        nsy = int(self.sirdata[1][1].astype('int'))
        image = QImage(nsx, nsy, QImage.Format_ARGB32)
        for x in xrange(nsx):
            for y in xrange(nsy):
                pix_val = qRgba(1, 2, 3, 255)
                image.setPixel(x, y, pix_val)
        pixmap = QPixmap.fromImage(image)
        #self.main_im.pixmap = pixmap
        self.main_im.setText("Loaded")
        # TODO: Finish here

def main():
    qt_app = QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    qt_app.exec_()

if __name__ == "__main__":
    main()

import os
from textwrap import dedent

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QImage, QLabel, QMessageBox, QScrollArea, QAction, QIcon, QPixmap

from dame import version_string

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("dame")
        # TODO: Set window icon
        self.create_actions()
        self.create_statusbar()
        self.create_menus()

        self.imageLabel = QLabel()
        #self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        self.imageLabel.setSizePolicy(QtGui.QSizePolicy.Ignored,
                QtGui.QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)

        self.setCentralWidget(self.scrollArea)

    def create_statusbar(self):
        self.statusBar().showMessage("Ready")
        self.pixinfo_label = QLabel()
        self.pixinfo_label.setVisible(False)

        self.statusBar().addPermanentWidget(self.pixinfo_label)

    def create_actions(self):
        self.about_action = QAction("&About", self)
        self.about_action.setStatusTip("About dame")
        self.about_action.setMenuRole(QAction.AboutRole)
        self.about_action.triggered.connect(self.show_about)

        self.open_action = QAction("&Open", self)
        self.open_action.setStatusTip("Open a SIR file")
        self.open_action.setShortcut(QtGui.QKeySequence.Open)
        self.open_action.triggered.connect(self.open_file)

        self.close_action = QAction("&Close", self)
        self.close_action.setStatusTip("Close current SIR file")
        self.close_action.setShortcut(QtGui.QKeySequence.Close)
        self.close_action.triggered.connect(self.close_file)

        self.exit_action = QAction("E&xit", self)
        self.about_action.setMenuRole(QAction.QuitRole)
        self.exit_action.setStatusTip("Exit dame")
        self.exit_action.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        self.exit_action.triggered.connect(self.close)

        # http://stackoverflow.com/questions/11643221/are-there-default-icons-in-pyqt-pyside
        # TODO: Add icons in a better way. See how Picard does it.
        QIcon.setThemeName("gnome") # TODO: temporary
        self.open_action.setIcon(QIcon.fromTheme("document-open"))
        self.close_action.setIcon(QIcon.fromTheme("window-close"))
        self.exit_action.setIcon(QIcon.fromTheme("application-exit"))
        self.about_action.setIcon(QIcon.fromTheme("help-about"))

    def create_menus(self):
        menu = self.menuBar().addMenu("&File")
        menu.addAction(self.open_action)
        menu.addAction(self.close_action)
        menu.addSeparator()
        menu.addAction(self.exit_action)
        menu = self.menuBar().addMenu("&Help")
        menu.addAction(self.about_action)

    def open_file(self):
        """ Display open file dialog """
        filename, file_filter = QtGui.QFileDialog.getOpenFileName(self, 
                "Open SIR file", 
                QtCore.QDir.homePath(), 
                "SIR files (*.sir *.ave);;Any file (*)"
                )
        if filename:
            print("Loading {}".format(filename))
            self.sirdata = loadsir(filename)
            # TODO
            #self.update_image()

    def close_file(self):
        """ Close file """
        print("Close file clicked")

    def show_about(self):
        """ Display about popup """
        about_text= """
                Dame {}
                Copyright 2013 Richard Lindsley
                Dame is a SIR file viewer""".format(version_string)
        QMessageBox.about(self, "About", dedent(about_text))

    #def update_image(self):
    #    """ Reload the image """
    #    nsx = int(self.sirdata[1][0].astype('int'))
    #    nsy = int(self.sirdata[1][1].astype('int'))
    #    image = QImage(nsx, nsy, QImage.Format_ARGB32)
    #    for x in xrange(nsx):
    #        for y in xrange(nsy):
    #            pix_val = qRgba(1, 2, 3, 255)
    #            image.setPixel(x, y, pix_val)
    #    pixmap = QPixmap.fromImage(image)
        #self.main_im.pixmap = pixmap
        #self.main_im.setText("Loaded")
        # TODO: Finish here
    

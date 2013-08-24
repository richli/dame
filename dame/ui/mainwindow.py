from __future__ import division

import os
from textwrap import dedent

import numpy as np
import numpy.ma as ma
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QImage, QLabel, QMessageBox, QScrollArea, QAction, QIcon, QPixmap, QCursor

from dame import version_string
from dame.loadsir import loadsir

#http://stackoverflow.com/questions/1736015/debugging-a-pyqt4-app
def debug_trace():
    '''Set a tracepoint in the Python debugger that works with Qt'''
    from PyQt4.QtCore import pyqtRemoveInputHook
    from pdb import set_trace
    pyqtRemoveInputHook()
    set_trace()


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi()
        self.panning = None # a flag if we're panning with the mouse currently
        self.scanning = None # a flag if we're scanning pixel values with the mouse

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
        self.imageLabel.adjustSize()
        self.imageLabel.setHidden(True)

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
        self.exit_action.setMenuRole(QAction.QuitRole)
        self.exit_action.setStatusTip("Exit dame")
        self.exit_action.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        self.exit_action.triggered.connect(self.close)

        self.prop_action = QAction("Image properties", self)
        self.prop_action.setStatusTip("Display properties of the loaded SIR file")
        self.prop_action.setEnabled(False)
        # TODO: Implement
        #self.prop_action.triggered.connect(self.close)

        self.zoomer_action = QAction("Enable zoomer window", self)
        self.zoomer_action.setStatusTip("Show zoomer window for magnified viewing")
        self.zoomer_action.setCheckable(True)
        # TODO: Implement
        #self.zoomer_action.triggered.connect(self.close)

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
        menu = self.menuBar().addMenu("Image")
        menu.addAction(self.prop_action)
        menu = self.menuBar().addMenu("Zoomer")
        menu.addAction(self.zoomer_action)
        menu = self.menuBar().addMenu("&Help")
        menu.addAction(self.about_action)

    @QtCore.pyqtSlot()
    def open_file(self):
        """ Display open file dialog """
        filename = QtGui.QFileDialog.getOpenFileName(self, 
                "Open SIR file", 
                QtCore.QDir.homePath(), 
                "SIR files (*.sir *.ave);;Any file (*)"
                )
        if filename:
            self.load_sir(filename)

    def load_sir(self, filename):
        if os.access(filename, os.F_OK|os.R_OK):
            print("Loading {}".format(filename))
            self.sirdata = loadsir(filename)
            self.update_image()
        else:
            print("Can't open {}".format(filename))

    @QtCore.pyqtSlot()
    def close_file(self):
        """ Close file """
        self.sirdata = None
        self.imageLabel.setHidden(True)
        self.imageLabel.clear()
        self.imageLabel.adjustSize()
        self.imageLabel.setCursor(QCursor(QtCore.Qt.ArrowCursor))
        # TODO: update status bar

    @QtCore.pyqtSlot()
    def show_about(self):
        """ Display about popup """
        about_text= """
                Dame {}
                Copyright 2013 Richard Lindsley
                Dame is a SIR file viewer""".format(version_string)
        QMessageBox.about(self, "About", dedent(about_text))

    def update_image(self):
        """ Reload the image """
        # TODO: Sometime I could use the C SIR library instead of the Python
        # version
        nsx = int(self.sirdata[1][0].astype('int'))
        nsy = int(self.sirdata[1][1].astype('int'))
        vmin = self.sirdata[1][49]
        vmax = self.sirdata[1][50]
        anodata = self.sirdata[1][48]
        v_offset = vmax - vmin
        v_scale = 255 / (vmax - vmin)
        #image = QImage(nsx, nsy, QImage.Format_ARGB32)
        image = QImage(nsx, nsy, QImage.Format_RGB32)
        # Scale the SIR image to the range of 0,255
        sir_scale = ma.masked_less_equal(self.sirdata[0], anodata, copy=True)
        sir_scale += v_offset
        sir_scale *= v_scale
        sir_scale = sir_scale.filled(0) # all nodata values are set to 0
        for x in xrange(nsx):
            for y in xrange(nsy):
                #pix_val = QtGui.qRgba(1, 2, 3, 128)
                sir_val = sir_scale[y,x]
                sir_val = int(round(sir_val))
                # TODO: I could use a different colormap here
                pix_val = QtGui.qRgb(sir_val, sir_val, sir_val)
                image.setPixel(x, y, pix_val)
        pixmap = QPixmap.fromImage(image)
        self.imageLabel.setHidden(False)
        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.adjustSize()
        self.imageLabel.setCursor(QCursor(QtCore.Qt.CrossCursor))
        # TODO: Update status bar

    # Mouse events
    def mousePressEvent(self, mouse):
        if mouse.button() == QtCore.Qt.RightButton:
            self.panning = mouse.pos()
            self.imageLabel.setCursor(QCursor(QtCore.Qt.ClosedHandCursor))
        elif mouse.button() == QtCore.Qt.LeftButton:
            self.scanning = mouse.pos()
            # TODO: Implement scanning. I need to draw a box around the current
            # position that represents the zoomer window size/position

    def mouseMoveEvent(self, mouse):
        if self.panning:
            dx = self.panning.x() - mouse.pos().x()
            dy = self.panning.y() - mouse.pos().y()
            hbar = self.scrollArea.horizontalScrollBar()
            vbar = self.scrollArea.verticalScrollBar()
            hbar.setValue(hbar.value()+dx)
            vbar.setValue(vbar.value()+dy)
            self.panning = mouse.pos()
        elif self.scanning:
            print("scanning pixel at {}".format(mouse.pos()))
    
    def mouseReleaseEvent(self, mouse):
        print("mouse released")
        if mouse.button() == QtCore.Qt.RightButton and self.panning:
            self.panning = None
            self.imageLabel.setCursor(QCursor(QtCore.Qt.CrossCursor))
        if mouse.button() == QtCore.Qt.LeftButton and self.scanning:
            self.scanning = None

    # Keyboard events
    # TODO

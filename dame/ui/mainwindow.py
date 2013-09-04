from __future__ import division

import os
import logging
from textwrap import dedent

import numpy as np
import numpy.ma as ma
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QImage, QLabel, QMessageBox, QScrollArea, QAction, QIcon, QPixmap, QCursor

from dame import version_string
from dame.loadsir import loadsir
from dame.pix2latlon import pix2latlon

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
        self.sir_files = {} # TODO: Use this dict to hold all the SIR files and associated info

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
        self.status_coord_label = QLabel()
        self.status_coord_label.setVisible(True)

        self.statusBar().addWidget(self.pixinfo_label)
        self.statusBar().addWidget(self.status_coord_label)

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
            logging.info("Loading {}".format(filename))
            self.statusBar().showMessage("Loading")
            sirdata = loadsir(filename)
            self.sir_files[0] = {
                    'filename': filename, 
                    'data': sirdata[0],
                    'header': sirdata[1]}
            self.update_image()
            self.statusBar().showMessage("Loaded", 2000)
        else:
            logging.warning("Can't open {}".format(filename))
            # TODO: Alert the user via GUI

    @QtCore.pyqtSlot()
    def close_file(self):
        """ Close file """
        logging.info("Closing SIR file")
        del self.sir_files[0]
        self.imageLabel.setHidden(True)
        self.imageLabel.clear()
        self.imageLabel.adjustSize()
        self.imageLabel.setCursor(QCursor(QtCore.Qt.ArrowCursor))
        self.pixinfo_label.setVisible(False)
        self.status_coord_label.setVisible(False)
        self.statusBar().showMessage("SIR closed", 2000)

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
        logging.info("Updating imageLabel")
        # TODO: Use the C SIR library instead of the Python version
        header = self.sir_files[0]['header']
        sirdata = self.sir_files[0]['data']
        nsx = int(header[0].astype('int'))
        nsy = int(header[1].astype('int'))
        vmin = header[49]
        vmax = header[50]
        anodata = header[48]
        v_offset = vmax - vmin
        v_scale = 255 / (vmax - vmin)
        #image = QImage(nsx, nsy, QImage.Format_ARGB32)
        image = QImage(nsx, nsy, QImage.Format_RGB32)
        # Scale the SIR image to the range of 0,255
        sir_scale = ma.masked_less_equal(sirdata, anodata, copy=True)
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
        self.update_statusbar()
        self.sir_files[0]['pixmap'] = pixmap

    def draw_zoomer_rect(self):
        """ Draw the rect on the image where the zoomer window location is """
        pixmap = self.sir_files[0]['pixmap'].copy()
        loc = self.sir_files[0]['pix_loc']
        p = QtGui.QPainter()
        p.begin(pixmap)
        p.drawText(loc.x(), loc.y(), "Hi there") # TODO: Replace with the zoomer box
        p.end()
        self.imageLabel.setPixmap(pixmap)

    def update_statusbar(self):
        vmin = self.sir_files[0]['header'][49]
        vmax = self.sir_files[0]['header'][50]
        self.pixinfo_label.setVisible(True)
        self.pixinfo_label.setText("{}, min: {}, max: {}".format(
            self.sir_files[0]['filename'],
            vmin, vmax))
        self.status_coord_label.setVisible(False)

    def update_statusbar_pos(self, x, y):
        """ Update with position at image index x, y """
        self.statusBar().clearMessage()
        self.status_coord_label.setVisible(True)
        nsx = int(self.sir_files[0]['header'][0].astype('int'))
        nsy = int(self.sir_files[0]['header'][1].astype('int'))
        # NOTE: 0-based indexing!
        if x >= 0 and y >= 0 and x < nsx and y < nsy:
            lon, lat = pix2latlon(x, y, self.sir_files[0]['header'])
            stat_text = "x:{}, y:{}, lat:{:0.4f}, lon:{:0.4f}, value:{}".format(
                    x, y, lat, lon, self.sir_files[0]['data'][y, x])
            self.status_coord_label.setText(stat_text)

    # Mouse events
    def mousePressEvent(self, mouse):
        if mouse.button() == QtCore.Qt.RightButton:
            self.panning = mouse.pos()
            self.imageLabel.setCursor(QCursor(QtCore.Qt.ClosedHandCursor))
        elif mouse.button() == QtCore.Qt.LeftButton:
            self.scanning = mouse.pos()
            # Update status bar
            im_pos = self.imageLabel.mapFromGlobal(self.mapToGlobal(mouse.pos()))
            self.update_statusbar_pos(im_pos.x(), im_pos.y())
            # Draw zoomer rect
            self.sir_files[0]['pix_loc'] = im_pos
            self.draw_zoomer_rect()

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
            # Switch mouse position coord from QMainWindow to self.imagelabel (QLabel)
            im_pos = self.imageLabel.mapFromGlobal(self.mapToGlobal(mouse.pos()))
            self.update_statusbar_pos(im_pos.x(), im_pos.y())
            # Draw zoomer rect
            self.sir_files[0]['pix_loc'] = im_pos
            self.draw_zoomer_rect()
    
    def mouseReleaseEvent(self, mouse):
        if mouse.button() == QtCore.Qt.RightButton and self.panning:
            self.panning = None
            self.imageLabel.setCursor(QCursor(QtCore.Qt.CrossCursor))
        if mouse.button() == QtCore.Qt.LeftButton and self.scanning:
            self.scanning = None

    # Keyboard events
    # TODO

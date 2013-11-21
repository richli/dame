from __future__ import division

import os
import logging
from textwrap import dedent

import numpy as np
import numpy.ma as ma
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QImage, QLabel, QMessageBox, QScrollArea, QAction, QIcon, QPixmap, QCursor
from PyQt4.QtCore import Qt

from . import version_string
import libsir

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

    def setupUi(self):
        self.setWindowTitle("dame")
        # TODO: Set window icon
        self.create_actions()
        self.create_statusbar()

        self.mainview = MainViewer(parent=self)

        ## Connect an action now that mainview is set
        #self.mode_group.triggered.connect(self.mainview.toggleComparison)

        # TODO: This is the start of using tabbed windows
        #self.mdiArea = QtGui.QMdiArea(parent=self)
        #first = self.mdiArea.addSubWindow(self.scrollArea)
        #self.mdiArea.setViewMode(QtGui.QMdiArea.TabbedView)
        #self.mdiArea.setTabsMovable(True)
        #self.setCentralWidget(self.mdiArea)
        #first.setWindowTitle("foo")

        self.setCentralWidget(self.mainview)

        # Create popup windows (for zoomer and panner)
        self.zoom_win = QtGui.QWidget(self, Qt.Window | Qt.Tool)
        self.zoom_win.setSizePolicy(QtGui.QSizePolicy.Fixed,
                QtGui.QSizePolicy.Fixed)
        self.zoom_win_im = QLabel()
        self.zoom_win_im.setSizePolicy(QtGui.QSizePolicy.Ignored,
                QtGui.QSizePolicy.Ignored)
        #self.zoom_win.resize(150,150)
        #self.zoom_win.show()
        zoomer_layout = QtGui.QGridLayout()
        zoomer_layout.setContentsMargins(0,0,0,0)
        zoomer_layout.addWidget(self.zoom_win_im)
        self.zoom_win.setLayout(zoomer_layout)

        #TODO: panner

        # Create note dock widget
        self.note_widget = QtGui.QDockWidget("Notes", parent=self)
        self.note_text = QtGui.QTextEdit(parent=self.note_widget)
        self.note_widget.setWidget(self.note_text)
        self.note_widget.setFeatures(
                QtGui.QDockWidget.DockWidgetClosable | 
                QtGui.QDockWidget.DockWidgetMovable | 
                QtGui.QDockWidget.DockWidgetFloatable | 
                QtGui.QDockWidget.DockWidgetVerticalTitleBar)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.note_widget)
        self.note_widget.close()
        self.note_action = self.note_widget.toggleViewAction()
        self.note_action.setText("Display notes")
        self.note_action.setStatusTip("Show notes about the SIR image")

        # Create the menus
        self.create_menus()

    def create_statusbar(self):
        self.statusBar().showMessage("Ready")

        # The individual info
        self.status_sing_pixinfo = QLabel()
        self.status_sing_coord = QLabel()
        self.status_left_pixinfo = QLabel()
        self.status_right_pixinfo = QLabel()
        self.status_comp_coord = QLabel()

        # The groups
        self.status_sing_layout = QtGui.QHBoxLayout()
        self.status_sing_layout.addWidget(self.status_sing_coord, 0, Qt.AlignRight)
        self.status_sing_layout.addWidget(self.status_sing_pixinfo, 1, Qt.AlignRight)
        self.status_comp_layout = QtGui.QHBoxLayout()
        self.status_comp_layout.addWidget(self.status_left_pixinfo, 0)
        self.status_comp_layout.addWidget(self.status_comp_coord, 1)
        self.status_comp_layout.addWidget(self.status_right_pixinfo, 0)

        self.status_sing_layout.setContentsMargins(0,0,0,0)
        self.status_comp_layout.setContentsMargins(0,0,0,0)

        self.status_sing = QtGui.QWidget()
        self.status_sing.setLayout(self.status_sing_layout)
        self.status_comp = QtGui.QWidget()
        self.status_comp.setLayout(self.status_comp_layout)

        # The stacked widget (to alternate between single and comparison modes)
        self.status_stacked = QtGui.QStackedWidget()
        self.status_stacked.addWidget(self.status_sing)
        self.status_stacked.addWidget(self.status_comp)
        self.status_stacked.setCurrentIndex(0)

        self.statusBar().addWidget(self.status_stacked)

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

        self.prop_action = QAction("SIR header", self)
        self.prop_action.setStatusTip("Display SIR header information")
        self.prop_action.triggered.connect(self.print_header)

        self.range_action = QAction("Image range", self)
        self.range_action.setStatusTip("Set image display range")
        self.range_action.triggered.connect(self.show_range)

        self.zoomer_action = QAction("Enable zoomer window", self)
        self.zoomer_action.setStatusTip("Show zoomer window for magnified viewing")
        self.zoomer_action.setCheckable(True)
        self.zoomer_action.triggered.connect(self.update_zoomer_opts)

        self.zoom_factor_label_action = QAction("Zoom factor", self)
        self.zoom_factor_label_action.setEnabled(False)

        self.zoom_factor_1_action = QAction("2x zoom", self)
        self.zoom_factor_2_action = QAction("4x zoom", self)
        self.zoom_factor_3_action = QAction("8x zoom", self)
        self.zoom_factor_4_action = QAction("16x zoom", self)
        self.zoom_factor_1_action.setStatusTip("Magnify zoom region by 2x")
        self.zoom_factor_2_action.setStatusTip("Magnify zoom region by 4x")
        self.zoom_factor_3_action.setStatusTip("Magnify zoom region by 8x")
        self.zoom_factor_4_action.setStatusTip("Magnify zoom region by 16x")
        self.zoom_factor_1_action.setCheckable(True)
        self.zoom_factor_2_action.setCheckable(True)
        self.zoom_factor_3_action.setCheckable(True)
        self.zoom_factor_4_action.setCheckable(True)

        self.zoom_size_label_action = QAction("Zoom region size", self)
        self.zoom_size_label_action.setEnabled(False)

        self.zoom_size_1_action = QAction("9x9 window", self)
        self.zoom_size_2_action = QAction("17x17 window", self)
        self.zoom_size_3_action = QAction("29x29 window", self)
        self.zoom_size_4_action = QAction("45x45 window", self)
        self.zoom_size_1_action.setStatusTip("Set zoom region to 9x9 pixels")
        self.zoom_size_2_action.setStatusTip("Set zoom region to 17x17 pixels")
        self.zoom_size_3_action.setStatusTip("Set zoom region to 29x29 pixels")
        self.zoom_size_4_action.setStatusTip("Set zoom region to 45x45 pixels")
        self.zoom_size_1_action.setCheckable(True)
        self.zoom_size_2_action.setCheckable(True)
        self.zoom_size_3_action.setCheckable(True)
        self.zoom_size_4_action.setCheckable(True)

        # Group zoomer actions and connect slots
        self.zoom_factor_group = QtGui.QActionGroup(self)
        self.zoom_factor_group.addAction(self.zoom_factor_1_action)
        self.zoom_factor_group.addAction(self.zoom_factor_2_action)
        self.zoom_factor_group.addAction(self.zoom_factor_3_action)
        self.zoom_factor_group.addAction(self.zoom_factor_4_action)
        self.zoom_factor_group.triggered.connect(self.update_zoomer_opts)

        self.zoom_size_group = QtGui.QActionGroup(self)
        self.zoom_size_group.addAction(self.zoom_size_1_action)
        self.zoom_size_group.addAction(self.zoom_size_2_action)
        self.zoom_size_group.addAction(self.zoom_size_3_action)
        self.zoom_size_group.addAction(self.zoom_size_4_action)
        self.zoom_size_group.triggered.connect(self.update_zoomer_opts)

        ## Mode actions
        #self.mode_group = QtGui.QActionGroup(self)
        #self.mode_single_action = QAction("Single image", self.mode_group)
        #self.mode_dual_action = QAction("Two images", self.mode_group)
        #self.mode_single_action.setCheckable(True)
        #self.mode_dual_action.setCheckable(True)
        #self.mode_single_action.setStatusTip("Display a single image")
        #self.mode_dual_action.setStatusTip("Display two images for comparison")
        #self.mode_single_action.setChecked(True)
        ##self.mode_group.triggered.connect(self.mainview.toggleComparison) # Moved later

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
        #menu.addAction(self.mode_single_action)
        #menu.addAction(self.mode_dual_action)
        #menu.addSeparator()
        menu.addAction(self.exit_action)
        menu = self.menuBar().addMenu("Image")
        menu.addAction(self.prop_action)
        menu.addAction(self.range_action)
        menu.addAction(self.note_action)
        #submenu = menu.addMenu("Mode")
        #submenu.addAction(self.mode_single_action)
        #submenu.addAction(self.mode_split_action)
        #submenu.addAction(self.mode_fade_action)
        menu = self.menuBar().addMenu("Zoomer")
        menu.addAction(self.zoomer_action)
        menu.addSeparator()
        menu.addAction(self.zoom_factor_label_action)
        menu.addAction(self.zoom_factor_1_action)
        menu.addAction(self.zoom_factor_2_action)
        menu.addAction(self.zoom_factor_3_action)
        menu.addAction(self.zoom_factor_4_action)
        menu.addSeparator()
        menu.addAction(self.zoom_size_label_action)
        menu.addAction(self.zoom_size_1_action)
        menu.addAction(self.zoom_size_2_action)
        menu.addAction(self.zoom_size_3_action)
        menu.addAction(self.zoom_size_4_action)
        menu = self.menuBar().addMenu("&Help")
        menu.addAction(self.about_action)

        # Deactivate menus by default
        self.range_action.setEnabled(False)
        self.prop_action.setEnabled(False)
        self.close_action.setEnabled(False)

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
            self.statusBar().showMessage("Loading")
            self.mainview.load_sir(filename)
            self.statusBar().showMessage("Loaded", 2000)

            # Activate menus
            self.range_action.setEnabled(True)
            self.prop_action.setEnabled(True)
            self.close_action.setEnabled(True)
        else:
            logging.warning("Can't open {}".format(filename))
            # TODO: Alert the user via GUI

    @QtCore.pyqtSlot()
    def close_file(self):
        """ Close file """
        logging.info("Closing SIR file")
        self.mainview.close_file()
        self.statusBar().showMessage("SIR closed", 2000)

        # That was the last file, so disable stuff
        if len(self.mainview.sir_files) == 0:
            self.status_stacked.setVisible(False)
            self.zoom_win.hide()

            # Deactivate menus
            self.range_action.setEnabled(False)
            self.prop_action.setEnabled(False)
            self.close_action.setEnabled(False)

    @QtCore.pyqtSlot()
    def show_about(self):
        """ Display about popup """
        about_text= """
                Dame {}
                Copyright 2013 Richard Lindsley
                Dame is a SIR file viewer""".format(version_string)
        QMessageBox.about(self, "About", dedent(about_text))

    @QtCore.pyqtSlot()
    def show_range(self):
        """ Display image range popup """
        win = RangeWindow()
        win.min_text.setText(str(self.mainview.sir_files[self.mainview.cur_tab]['vmin']))
        win.max_text.setText(str(self.mainview.sir_files[self.mainview.cur_tab]['vmax']))
        if win.exec_() == QtGui.QDialog.Accepted:
            win_range = win.getRange()
            self.mainview.sir_files[self.mainview.cur_tab]['vmin'] = win_range[0]
            self.mainview.sir_files[self.mainview.cur_tab]['vmax'] = win_range[1]
            self.mainview.update_image(self.mainview.cur_tab)
            self.mainview.update_view()

    @QtCore.pyqtSlot()
    def print_header(self):
        """ Display SIR header info """
        sir_head = libsir.print_sir_head(self.mainview.sir_files[self.mainview.cur_tab]['header'])
        # TODO: Maybe make this a modeless dialog instead of modal? Use a dock
        # widget?
        box = QMessageBox()
        box.setText(dedent(sir_head))
        box.setIcon(QMessageBox.Information)
        box.exec_()

    def update_zoomer(self):
        """ Update the zoomer, both the image as well as the popup """
        if 'pix_loc' not in self.mainview.sir_files[self.mainview.cur_tab]:
            return
        try:
            loc = self.mainview.sir_files[self.mainview.cur_tab]['pix_loc']
            rect_w = self.mainview.sir_files[self.mainview.cur_tab]['zoomer_size']
            winsize = rect_w * self.mainview.sir_files[self.mainview.cur_tab]['zoomer_factor']
            if self.mainview.cur_tab == "split":
                pixmaps = (self.mainview.sir_files['left']['pixmap'].copy(),
                        self.mainview.sir_files['right']['pixmap'].copy())
            else:
                pixmaps = \
                (self.mainview.sir_files[self.mainview.cur_tab]['pixmap'].copy(),)

            for pixmap_i, pixmap in enumerate(pixmaps):
                # Upper left corner
                if loc.x() < rect_w/2: 
                    rect_x = -0.5
                elif loc.x() > pixmap.width() - rect_w/2:
                    rect_x = pixmap.width() - rect_w - 0.5
                else:
                    rect_x = loc.x() - rect_w/2
                if loc.y() < rect_w/2: 
                    rect_y = -0.5
                elif loc.y() > pixmap.height() - rect_w/2:
                    rect_y = pixmap.height() - rect_w - 0.5
                else:
                    rect_y = loc.y() - rect_w/2

                rect_x += 1
                rect_y += 1

                # Draw the image with the zoomer region outlined
                p = QtGui.QPainter()
                p.begin(pixmap)
                p.setPen(QtGui.QColor("#FFFFFF")) # White stroke
                p.drawRect(rect_x, rect_y, rect_w, rect_w)
                p.end()
                if self.mainview.cur_tab in ("left", "right", "cross"):
                    self.mainview.single_image.image.setPixmap(pixmap)
                elif self.mainview.cur_tab in ("split", ):
                    if pixmap_i == 0:
                        self.mainview.left_image.image.setPixmap(pixmap)
                    elif pixmap_i == 1:
                        self.mainview.right_image.image.setPixmap(pixmap)
                    else:
                        logging.warning("pixmap_i is {}".format(pixmap_i))

            # Update the zoomer window
            if self.mainview.cur_tab == "split":
                pixmaps = (self.mainview.sir_files['left']['pixmap'],
                        self.mainview.sir_files['right']['pixmap'])
            else:
                pixmaps = \
                (self.mainview.sir_files[self.mainview.cur_tab]['pixmap'],)

            for pixmap_src in pixmaps:
                # extract the zoomer region
                pixmap = pixmap_src.copy(rect_x, rect_y, rect_w, rect_w)
                # scale it
                pixmap = pixmap.scaled(winsize, winsize,
                        Qt.KeepAspectRatioByExpanding)

                # Add crosshair to zoomer window; note that the crosshair
                # won't be centered if the region is at the edges
                p = QtGui.QPainter()
                p.begin(pixmap)
                # Highlight selected pixel
                #p.setPen(QtGui.QColor("#000000")) # Black stroke
                p.setPen(QtGui.QColor("#FFFFFF")) # White stroke
                zoom_fac = self.mainview.sir_files[self.mainview.cur_tab]['zoomer_factor']
                # Top left of magnified pixel
                mag_pix = (zoom_fac * (loc.x() - rect_x + 1) - zoom_fac/2, 
                        zoom_fac * (loc.y() - rect_y + 1) - zoom_fac/2)
                # Center of magnified pixel
                mag_pix_cen = (zoom_fac * (loc.x() - rect_x + 1), 
                        zoom_fac * (loc.y() - rect_y + 1))
                p.drawRect(mag_pix[0], mag_pix[1], zoom_fac, zoom_fac)
                # Draw crosshairs
                p.setPen(QtGui.QColor("#FFFFFF")) # White stroke
                p.drawLine(mag_pix_cen[0],0,mag_pix_cen[0],mag_pix[1]-1) # vertical line, top
                p.drawLine(mag_pix_cen[0],mag_pix[1]+zoom_fac, mag_pix_cen[0],winsize-0) # vertical line, bottom
                p.drawLine(0,mag_pix_cen[1],mag_pix[0]-1,mag_pix_cen[1]) # horizontal line, left
                p.drawLine(mag_pix[0]+zoom_fac,mag_pix_cen[1],winsize-0,mag_pix_cen[1]) # horizontal line, right
                p.end()

                self.zoom_win_im.setHidden(False)
                self.zoom_win_im.setPixmap(pixmap)
                self.zoom_win_im.adjustSize()

        except KeyError as err:
            logging.warning("Can't find {}".format(err))

    def update_statusbar(self):
        if self.mainview.cur_tab in ("left", "right"):
            vmin = self.mainview.sir_files[self.mainview.cur_tab]['vmin']
            vmax = self.mainview.sir_files[self.mainview.cur_tab]['vmax']
            self.status_stacked.setVisible(True)
            self.status_stacked.setCurrentIndex(0)
            self.status_sing_pixinfo.setText("min: {}, max: {}".format(vmin, vmax))
            self.status_sing_coord.setVisible(False)
        elif self.mainview.cur_tab in ("split", "fade"):
            vmin_l = self.mainview.sir_files['left']['vmin']
            vmax_l = self.mainview.sir_files['left']['vmax']
            vmin_r = self.mainview.sir_files['right']['vmin']
            vmax_r = self.mainview.sir_files['right']['vmax']
            self.status_stacked.setVisible(True)
            self.status_stacked.setCurrentIndex(1)
            self.status_left_pixinfo.setText("min: {} max: {}".format(vmin_l, vmax_l))
            self.status_right_pixinfo.setText("min: {} max: {}".format(vmin_r, vmax_r))
            self.status_comp_coord.setVisible(False)

    def update_statusbar_pos(self, x_im, y_im):
        """ Update with position at image index x, y """
        self.statusBar().clearMessage()
        nsx = self.mainview.sir_files[self.mainview.cur_tab]['header'].nsx
        nsy = self.mainview.sir_files[self.mainview.cur_tab]['header'].nsy
        # Convert from 0-based to 1-based indexing
        # (I've double-checked the values returned here using sir_util2a)
        y = nsy - y_im # Convert image y coord to SIR y coord
        x = x_im + 1
        if x > 0 and y > 0 and x <= nsx and y <= nsy:
            # Note that sir_data is 0-based indexing, but pix2latlon is 1-based
            lon, lat = libsir.pix2latlon(x, y,
                    self.mainview.sir_files[self.mainview.cur_tab]['header'])
            if self.mainview.cur_tab in ("left", "right"):
                self.status_sing_coord.setVisible(True)
                stat_text = "x = {}, y = {}   lat = {:0.4f}, lon = {:0.4f} value = {:0.4f}".format(
                        x, y, lat, lon,
                        self.mainview.sir_files[self.mainview.cur_tab]['data'][y_im, x_im])
                self.status_sing_coord.setText(stat_text)
            elif self.mainview.cur_tab in ("split","fade"):
                self.status_comp_coord.setVisible(True)
                stat_text = "x = {}, y = {}   lat = {:0.4f}, lon = {:0.4f} left value = {:0.4f} right value = {:0.4f}".format(
                        x, y, lat, lon,
                        self.mainview.sir_files['left']['data'][y_im, x_im],
                        self.mainview.sir_files['right']['data'][y_im, x_im])
                self.status_comp_coord.setText(stat_text)

    def sizeHint(self):
        """ Override the suggested size """
        return QtCore.QSize(1000,800)

    # Menu events
    @QtCore.pyqtSlot()
    def update_zoomer_opts(self, draw_win=True):
        """ Given a menu change, this sets zoomer options and updates """
        file_dict = self.mainview.sir_files[self.mainview.cur_tab]
        # Is zoomer enabled?
        file_dict['zoomer_on'] = self.zoomer_action.isChecked()

        # Find the zoom factor
        zfactor = self.zoom_factor_group.checkedAction()
        if zfactor is self.zoom_factor_1_action:
            file_dict['zoomer_factor'] = 2
        elif zfactor is self.zoom_factor_2_action:
            file_dict['zoomer_factor'] = 4
        elif zfactor is self.zoom_factor_3_action:
            file_dict['zoomer_factor'] = 8
        elif zfactor is self.zoom_factor_4_action:
            file_dict['zoomer_factor'] = 16

        # Find the zoom size
        zsize = self.zoom_size_group.checkedAction()
        if zsize is self.zoom_size_1_action:
            file_dict['zoomer_size'] = 9
        elif zsize is self.zoom_size_2_action:
            file_dict['zoomer_size'] = 17
        elif zsize is self.zoom_size_3_action:
            file_dict['zoomer_size'] = 29
        elif zsize is self.zoom_size_4_action:
            file_dict['zoomer_size'] = 45

        if draw_win:
            # Compute zoomer window size and show/hide it
            winsize = file_dict['zoomer_size'] * file_dict['zoomer_factor']
            self.zoom_win.resize(winsize, winsize)
            self.zoom_win.setFixedSize(winsize, winsize)
            if file_dict['zoomer_on']:
                self.zoom_win.show()
            else:
                self.zoom_win.hide()

            # Update zoomer
            self.update_zoomer()

    # Keyboard events
    def keyPressEvent(self, key):
        if len(self.mainview.sir_files) == 0:
            key.ignore()
            return

        if 'pix_loc' not in self.mainview.sir_files[self.mainview.cur_tab]:
            # Don't do anything if we don't have a coord yet
            key.ignore()
            return

        # Increment im_pos if valid key
        # Note that im_pos is 0-based, so 
        # it ranges from 0 to nsx-1/nsy-1 inclusive
        im_pos = self.mainview.sir_files[self.mainview.cur_tab]['pix_loc']
        nsx = self.mainview.sir_files[self.mainview.cur_tab]['header'].nsx
        nsy = self.mainview.sir_files[self.mainview.cur_tab]['header'].nsy
        delta = 5 if key.modifiers() == Qt.ShiftModifier else 1
        if key.key() == Qt.Key_J:
            # Down
            if im_pos.y() + delta < nsy:
                im_pos.setY(im_pos.y() + delta)
        elif key.key() == Qt.Key_K:
            # Up
            if im_pos.y() - delta >= 0:
                im_pos.setY(im_pos.y() - delta)
        elif key.key() == Qt.Key_H:
            # Left
            if im_pos.x() - delta >= 0:
                im_pos.setX(im_pos.x() - delta)
        elif key.key() == Qt.Key_L:
            # Right
            if im_pos.x() + delta < nsx:
                im_pos.setX(im_pos.x() + delta)
        else:
            key.ignore()
            return

        # Update stuff with our new position
        self.mainview.sir_files[self.mainview.cur_tab]['pix_loc'] = im_pos
        self.update_zoomer()
        self.update_statusbar_pos(im_pos.x(), im_pos.y())

class RangeWindow(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        min_label = QtGui.QLabel("min")
        max_label = QtGui.QLabel("max")
        min_text = QtGui.QLineEdit()
        max_text = QtGui.QLineEdit()
        min_text.setValidator(QtGui.QDoubleValidator())
        max_text.setValidator(QtGui.QDoubleValidator())

        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                QtGui.QDialogButtonBox.Cancel, Qt.Horizontal, parent=self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        vbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(min_label)
        hbox.addWidget(min_text)
        hbox.addWidget(max_label)
        hbox.addWidget(max_text)

        vbox.addLayout(hbox)
        vbox.addWidget(buttons)
        self.setLayout(vbox)
        self.setWindowTitle("Display range")

        min_text.setFocus()

        # Allow outside access to these
        self.min_text = min_text
        self.max_text = max_text

    def getRange(self):
        return (float(self.min_text.text()), float(self.max_text.text()))

class MainViewer(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        # Setup main image labels and their scrollers
        self.single_image = ImageView(parent=self, mainwindow=parent)
        self.left_image = ImageView(parent=self, mainwindow=parent)
        self.right_image = ImageView(parent=self, mainwindow=parent)

        # Variables to store
        self.parent = parent
        self.panning = None # a flag if we're panning with the mouse currently
        self.scanning = None # a flag if we're scanning pixel values with the mouse
        self.scanning_side = None # For split screen, which side did we start on
        self.cur_tab = None # Which tab name we're currently on
        self.sir_files = {} # Holds SIR files and associated info for each tab

        # Set context menu
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.addAction(self.parent.range_action)
        self.addAction(self.parent.open_action)
        self.addAction(self.parent.close_action)

        # Create tabbar for comparison views
        self.tabbar = QtGui.QTabBar()
        self.tabbar.setExpanding(True)
        self.tabbar.setMovable(False)
        self.tabbar.setTabsClosable(False)
        self.tabbar.currentChanged.connect(self.tabSelect)

        # Splitter widget
        self.splitView = QtGui.QSplitter(parent=self)
        self.splitView.addWidget(self.left_image)
        self.splitView.addWidget(self.right_image)

        # Stacked widget
        self.stacked_widget = QtGui.QStackedWidget(parent=self)
        self.stacked_widget.addWidget(self.single_image)
        self.stacked_widget.addWidget(self.splitView)

        # Layout
        vbox = QtGui.QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.addWidget(self.tabbar)
        vbox.addWidget(self.stacked_widget)
        self.setLayout(vbox)

    def load_sir(self, filename):
        file_index = 'left'
        # Do we already have a file loaded?
        if file_index in self.sir_files:
            msg = QtGui.QMessageBox(parent=self)
            msg.setText(
                    "{} is already loaded. Load {} in comparison view?".format(
                        self.sir_files[file_index]['filename'], filename))
            msg.setStandardButtons(QtGui.QMessageBox.Yes |
                    QtGui.QMessageBox.No)
            msg.setDefaultButton(QtGui.QMessageBox.Yes)
            msg.setIcon(QtGui.QMessageBox.Question)
            msg_ret = msg.exec_()
            if msg_ret == QtGui.QMessageBox.No:
                del self.sir_files[file_index]
            elif msg_ret == QtGui.QMessageBox.Yes:
                file_index = 'right'

        logging.info("Loading {}".format(filename))
        sir_head, sir_data = libsir.get_sir(filename)
        self.sir_files[file_index] = {
                'filename': filename, 
                'data': sir_data,
                'header': sir_head}

        # Make sure the comparison image is compatible
        if file_index == 'right':
            # Assume the header (or the parts we use, at least) is the same
            # between the files
            self.sir_files['split'] = {'header': sir_head} 
            self.sir_files['fade'] = {}
            old_head = self.sir_files['left']['header']
            if old_head.nsx != sir_head.nsx or \
               old_head.nsy != sir_head.nsy or \
               old_head.iopt != sir_head.iopt or \
               old_head.xdeg != sir_head.xdeg or \
               old_head.ydeg != sir_head.ydeg or \
               old_head.ascale != sir_head.ascale or \
               old_head.bscale != sir_head.bscale or \
               old_head.a0 != sir_head.a0 or \
               old_head.b0 != sir_head.b0:
                   logging.error("New SIR isn't compatible with old SIR for comparison purposes")

        self.cur_tab = file_index
        # Set zoomer options
        self.parent.zoom_factor_2_action.setChecked(True)
        self.parent.zoom_size_2_action.setChecked(True)
        self.parent.update_zoomer_opts(draw_win=False)

        # Update stuff
        self.update_image(file_index)
        self.update_view()
        self.toggleComparison()

        if file_index == 'left':
            self.parent.setWindowTitle("dame - {}".format(filename))

    # Tab management
    def toggleComparison(self):
        # Single mode
        if len(self.sir_files) < 2:
            logging.info("toggleComparison: single mode")
            self.tabbar.setCurrentIndex(0) # So the active tab doesn't change when I remove tabs below
            # Remove tabs
            while self.tabbar.count() > 0:
                self.tabbar.removeTab(0)
        # Comparison mode
        else:
            logging.info("toggleComparison: comparison mode")
            self.setWindowTitle("dame")
            self.tabbar.addTab(self.sir_files['left']['filename'])
            self.tabbar.addTab("Split view")
            self.tabbar.addTab("Crossfade view")
            self.tabbar.addTab(self.sir_files['right']['filename'])
            self.tabbar.setTabEnabled(2, False) # TODO: Temp until crossfade is ready

    def tabSelect(self, index):
        """ Update stuff based on what tab was selected """
        logging.info("Selected tab {}".format(index))
        if index == 0:
            self.cur_tab = 'left'
        elif index == 1:
            self.cur_tab = 'split'
        elif index == 2:
            self.cur_tab = 'fade'
        elif index == 3:
            self.cur_tab = 'right'

        # index of -1 means the tabbar is empty
        if index in (-1,0,3):
            self.parent.open_action.setEnabled(True)
            self.parent.close_action.setEnabled(True)
            self.parent.prop_action.setEnabled(True)
            self.parent.range_action.setEnabled(True)
        else:
            self.parent.open_action.setEnabled(False)
            self.parent.close_action.setEnabled(False)
            self.parent.prop_action.setEnabled(False)
            self.parent.range_action.setEnabled(False)

        self.update_view()

    def update_image(self, tabname):
        """ Refresh the image in the tab 

        tabname can be: "left", "right", "split", "fade"

        """
        if tabname in ("left", "right"):
            logging.info("Refreshing image {}".format(tabname))
            header = self.sir_files[tabname]['header']
            sirdata = self.sir_files[tabname]['data']
            nsx = header.nsx
            nsy = header.nsy
            vmin = self.sir_files[tabname].setdefault('vmin', header.v_min)
            vmax = self.sir_files[tabname].setdefault('vmax', header.v_max)
            anodata = header.anodata
            v_offset = -vmin
            v_scale = 255 / (vmax - vmin)

            # Scale the SIR image to the range of 0,255
            sir_scale = ma.masked_less_equal(sirdata, anodata, copy=True)
            sir_scale += v_offset
            sir_scale *= v_scale
            sir_scale = sir_scale.filled(0) # all nodata values are set to 0
            # Clip to 0,255
            sir_scale[sir_scale < 0] = 0
            sir_scale[sir_scale > 255] = 255
            # Ensure uint8 data and C contiguous data
            sir_scale = np.require(sir_scale, np.uint8, 'C') 

            # Construct image from sir_scale
            # http://www.swharden.com/blog/2013-06-03-realtime-image-pixelmap-from-numpy-array-data-in-qt/
            # Note that I use the bytesPerLine option here. Without it, the data
            # must be 32-bit aligned (4 bytes). This means with uint8 data that
            # the image width must be a multiple of 4. This does not apply to
            # all SIR images, so I set bytesPerLine to be 
            # nsx (items) * 1 (bytes/item)
            image = QImage(sir_scale.data, nsx, nsy, nsx, QImage.Format_Indexed8)
            #ctab = []
            #for i in xrange(256):
            #    ctab.append(QtGui.qRgb(i,i,i))
            #image.setColorTable(ctab)

            # Save pixmap
            pixmap = QPixmap.fromImage(image)
            self.sir_files[tabname]['pixmap'] = pixmap
        else:
            logging.warning("Can't use update_image for {}".format(tabname))

    def update_view(self):
        if self.cur_tab in ("left", "right", "fade"):
            self.stacked_widget.setCurrentIndex(0)
        elif self.cur_tab == "split":
            self.stacked_widget.setCurrentIndex(1)

        # Single view mode
        if self.cur_tab in ("left", "right"):
            logging.info("Updating view, single view")

            pixmap = self.sir_files[self.cur_tab]['pixmap']
            self.single_image.update_image(pixmap)

            self.parent.update_statusbar()
            self.parent.update_zoomer_opts()

            # Update statusbar
            if 'pix_loc' in self.sir_files[self.cur_tab]:
                im_pos = self.sir_files[self.cur_tab]['pix_loc']
                self.parent.update_statusbar_pos(im_pos.x(), im_pos.y())

        # Split view
        elif self.cur_tab == "split":
            logging.info("Updating view, split view")

            pixmap = self.sir_files['left']['pixmap']
            self.left_image.update_image(pixmap)
            pixmap = self.sir_files['right']['pixmap']
            self.right_image.update_image(pixmap)

            self.parent.update_statusbar()
            self.parent.update_zoomer_opts()

            # Update statusbar
            if 'pix_loc' in self.sir_files[self.cur_tab]:
                im_pos = self.sir_files[self.cur_tab]['pix_loc']
                self.parent.update_statusbar_pos(im_pos.x(), im_pos.y())

        elif self.cur_tab == "fade":
            logging.info("Updating view, fade view")
            # TODO

    def close_file(self):
        if len(self.sir_files) == 1:
            logging.info("Closing a single file")
            del self.sir_files['left']
            self.single_image.image.setHidden(True)
            self.single_image.image.clear()
            self.single_image.image.adjustSize()
            self.single_image.image.setCursor(QCursor(Qt.ArrowCursor))
        else:
            logging.info("Closing a file in comparison mode")
            del self.sir_files['split']
            del self.sir_files['fade']
            del self.sir_files[self.cur_tab]
            # We closed the left image, so move the right image to left
            if self.cur_tab == 'left':
                self.sir_files['left'] = self.sir_files.pop('right')
                logging.info("Closed left file")
            self.cur_tab = 'left'
            self.update_view()

        self.toggleComparison()

    # Mouse events
    def mousePressEvent(self, mouse):
        if len(self.sir_files) > 0:
            if mouse.button() == Qt.MiddleButton:
                self.panning = mouse.pos()
                self.single_image.image.setCursor(QCursor(Qt.ClosedHandCursor))
                self.left_image.image.setCursor(QCursor(Qt.ClosedHandCursor))
                self.right_image.image.setCursor(QCursor(Qt.ClosedHandCursor))
            elif mouse.button() == Qt.LeftButton:
                self.scanning = mouse.pos()

                if self.cur_tab in ("left", "right", "fade"):
                    im_pos = self.single_image.image.mapFromGlobal(self.mapToGlobal(mouse.pos()))
                elif self.cur_tab in ("split",):
                    # Figure out which widget has the mouse
                    if self.left_image.image.underMouse():
                        self.scanning_side = 'left'
                        im_pos = self.left_image.image.mapFromGlobal(self.mapToGlobal(mouse.pos()))
                    elif self.right_image.image.underMouse():
                        self.scanning_side = 'right'
                        im_pos = self.right_image.image.mapFromGlobal(self.mapToGlobal(mouse.pos()))
                    else:
                        logging.error("neither image is under mouse?!")

                self.sir_files[self.cur_tab]['pix_loc'] = im_pos

                # Update status bar and zoomer
                self.parent.update_statusbar_pos(im_pos.x(), im_pos.y())
                self.parent.update_zoomer()

    def mouseMoveEvent(self, mouse):
        if len(self.sir_files) > 0:
            if self.panning:
                dx = self.panning.x() - mouse.pos().x()
                dy = self.panning.y() - mouse.pos().y()
                self.panning = mouse.pos()

                if self.cur_tab == 'split':
                    scrollers = (self.left_image, self.right_image)
                else:
                    scrollers = (self.single_image,)

                for scroller in scrollers:
                    hbar = scroller.horizontalScrollBar()
                    vbar = scroller.verticalScrollBar()
                    hbar.setValue(hbar.value()+dx)
                    vbar.setValue(vbar.value()+dy)

            elif self.scanning:
                # Switch mouse position coord from QMainWindow to self.imagelabel (QLabel)
                if self.cur_tab in ("left", "right", "fade"):
                    im_pos = self.single_image.image.mapFromGlobal(self.mapToGlobal(mouse.pos()))
                elif self.cur_tab in ("split",):
                    if self.scanning_side == 'left':
                        im_pos = self.left_image.image.mapFromGlobal(self.mapToGlobal(mouse.pos()))
                    elif self.scanning_side == 'right':
                        im_pos = self.right_image.image.mapFromGlobal(self.mapToGlobal(mouse.pos()))

                self.sir_files[self.cur_tab]['pix_loc'] = im_pos
                # Update statusbar and zoomer
                self.parent.update_statusbar_pos(im_pos.x(), im_pos.y())
                self.parent.update_zoomer()
        else:
            mouse.ignore()
    
    def mouseReleaseEvent(self, mouse):
        if self.cur_tab in self.sir_files:
            if mouse.button() == Qt.MiddleButton and self.panning:
                self.panning = None
                self.single_image.image.setCursor(QCursor(Qt.CrossCursor))
                self.left_image.image.setCursor(QCursor(Qt.CrossCursor))
                self.right_image.image.setCursor(QCursor(Qt.CrossCursor))
            if mouse.button() == Qt.LeftButton and self.scanning:
                self.scanning = None
                self.scanning_side = None
        else:
            mouse.ignore()

    def wheelEvent(self, wheel):
        """ Normally this doesn't need reimplementation, but it does for split view """
        if len(self.sir_files) > 0:
            ds = -wheel.delta() / 4

            if self.cur_tab == 'split': 
                scrollers = (self.left_image, self.right_image)
            else: 
                scrollers = (self.single_image,)

            for scroller in scrollers: 
                if wheel.orientation() == Qt.Horizontal:
                    hbar = scroller.horizontalScrollBar() 
                    hbar.setValue(hbar.value()+ds)
                elif wheel.orientation() == Qt.Vertical:
                    vbar = scroller.verticalScrollBar() 
                    vbar.setValue(vbar.value()+ds)


class ImageView(QtGui.QScrollArea):
    def __init__(self, parent=None, mainwindow=None):
        QtGui.QScrollArea.__init__(self, parent)

        # Define the image
        self.image = QLabel()
        self.image.setSizePolicy(QtGui.QSizePolicy.Ignored,
                QtGui.QSizePolicy.Ignored)
        self.image.setScaledContents(True)
        self.image.adjustSize()
        self.image.setHidden(True)

        self.setWidget(self.image)
        self.setBackgroundRole(QtGui.QPalette.Dark)

        # Variables to store
        self.parent = parent
        self.mainwindow = mainwindow
        self.panning = None
        self.scanning = None

    def update_image(self, pixmap):
        self.image.setHidden(False)
        self.image.setPixmap(pixmap)
        self.image.adjustSize()
        self.image.setCursor(QCursor(Qt.CrossCursor))
        self.image.update()

    def wheelEvent(self, wheel):
        # This passes the wheel event to MainViewer()
        wheel.ignore()


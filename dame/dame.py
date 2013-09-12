__author__ = "Richard Lindsley"

import sys, os
import argparse
import logging

import sip
sip.setapi('QDate', 2)
sip.setapi('QDateTime', 2)
sip.setapi('QString', 2)
sip.setapi('QTextStream', 2)
sip.setapi('QTime', 2)
sip.setapi('QUrl', 2)
sip.setapi('QVariant', 2)
from PyQt4 import QtCore,QtGui

from . import __version__
from .mainwindow import MainWindow

#class Dame(QtGui.QApplication):
#    def __init__(self, args):
#        QtGui.QApplication.__init__(self, args)
#        self._args = args

def main():
    parser = argparse.ArgumentParser(description="View SIR file(s)")
    parser.add_argument("sir_files", action="store", nargs='*',
            help='List of SIR files to open')
    parser.add_argument("-v", "--verbose", action="store_true",
            help='Log INFO messages to stdout')
    parser.add_argument("--debug", action="store_true",
            help='Log DEBUG messages to stdout')
    parser.add_argument('--version', action='version',
            version='%(prog)s version {}'.format(__version__))
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    qt_app = QtGui.QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    # TODO: Handle multiple files
    if len(args.sir_files) > 0:
        frame.load_sir(args.sir_files[0])
    qt_app.exec_()

if __name__ == "__main__":
    main()

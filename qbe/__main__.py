"""Entry point into the QBE application.

Instantiates the main window and executes it."""

import sys

from PySide2.QtWidgets import QApplication

from qbe.config import config
from qbe.explorer import MainWindow

qbe_app = QApplication(sys.argv)
qbe_app.setApplicationName(config['App name'])
main_window = MainWindow(qbe_app)
qbe_app.exec_()

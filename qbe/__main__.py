"""Entry point into the QBE application.

Instantiates the main window and executes it."""

# This import is deliberately placed at the top of __main__.py to guarantee
# that hagadias is able to import ElementTree before any other package does,
# enabling it to switch to the Python-mode XML parser to get line numbers.
from hagadias import gameroot

import sys

from PySide2.QtWidgets import QApplication

from qbe.config import config
from qbe.explorer import MainWindow

qbe_app = QApplication(sys.argv)
qbe_app.setApplicationName(config['App name'])
main_window = MainWindow(qbe_app)
qbe_app.exec_()

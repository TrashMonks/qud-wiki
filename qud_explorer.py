import sys

from PySide2.QtWidgets import QTreeView, QMainWindow, QApplication


class MainWindow(QMainWindow):
    """Main application window for Qud Blueprint Explorer."""
    def __init__(self, app: QApplication, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.app = app

app = QApplication(sys.argv)
app.setApplicationName("Qud Blueprint Explorer")
main_window = MainWindow(app)
app.exec_()
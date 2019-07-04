import sys

from PySide2.QtWidgets import QTreeView, QMainWindow, QApplication, QAbstractItemModel

from qud_explorer_window import Ui_MainWindow
from qud_wiki import object_root


class QudObjectModel(QAbstractItemModel):



class MainWindow(QMainWindow):
    """Main application window for Qud Blueprint Explorer."""
    def __init__(self, app: QApplication, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.app = app

app = QApplication(sys.argv)
app.setApplicationName("Qud Blueprint Explorer")
main_window = MainWindow(app)
tree_view = QTreeView(main_window)
main_window.show()


app.exec_()

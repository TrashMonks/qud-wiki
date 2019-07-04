import pprint
import sys

from PySide2.QtCore import QModelIndex
from PySide2.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide2.QtWidgets import QMainWindow, QApplication

from item import wikify_item, get_item_stats
from qud_explorer_window import Ui_MainWindow
from qud_object import QudObject
from qud_object_tree import qud_object_root


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main application window for Qud Blueprint Explorer."""
    def __init__(self, app: QApplication, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.app = app
        self.setupUi(self)
        icon = QIcon("spray_bottle.png")
        self.setWindowIcon(icon)
        self.qud_object_model = QStandardItemModel()
        # We only need to add Object to the model, since all other Objects are loaded as children:
        self.qud_object_model.appendRow(self.init_qud_object(self.qud_object_model, qud_object_root))
        self.treeView.setModel(self.qud_object_model)
        self.treeView.clicked[QModelIndex].connect(self.tree_item_clicked)

    def init_qud_object(self, model: QStandardItemModel, qud_object: QudObject):
        item = QStandardItem(qud_object.name)
        if not qud_object.is_leaf:
            for child in qud_object.children:
                item.appendRow(self.init_qud_object(model, child))
        if qud_object.is_specified('tag_BaseObject'):
            item.setSelectable(False)
        item.setData(qud_object)
        return item

    def tree_item_clicked(self, index):
        item = self.qud_object_model.itemFromIndex(index)
        qud_object = item.data()
        text = pprint.pformat(qud_object.attributes)
        self.plainTextEdit.setPlainText(text)


app = QApplication(sys.argv)
app.setApplicationName("Qud Blueprint Explorer")
main_window = MainWindow(app)
main_window.show()
app.exec_()

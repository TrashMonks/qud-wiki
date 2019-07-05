import pprint
import sys

from PySide2.QtCore import QModelIndex
from PySide2.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide2.QtWidgets import QMainWindow, QApplication, QTreeView

from item import wikify_item, get_item_stats
from qud_explorer_window import Ui_MainWindow
from qud_object import QudObject
from qud_object_tree import qud_object_root

# most interesting targets to have expanded in the tree to start
INITIAL_EXPANSION_TARGETS = ['Food', 'MeleeWeapon', 'MissileWeapon', 'Armor', 'Shield', 'Token',
                             'LightSource', 'Tool', 'Tonic', 'Trinket', 'Energy Cell',
                             'Security Card', ]


def recursive_expand(item: QStandardItem, treeview: QTreeView, model: QStandardItemModel):
    index = model.indexFromItem(item)
    treeview.expand(index)
    if item.parent() is not None:
        recursive_expand(item.parent(), treeview, model)


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main application window for Qud Blueprint Explorer.

    The UI layout is derived from qud_explorer_window.py, which is compiled from
    qud_explorer_window.ui (designed graphically in Qt Designer) by the UIC executable that comes
    with PySide2."""
    def __init__(self, app: QApplication, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.app = app
        self.setupUi(self)  # lay out the inherited UI as in the graphical designer
        icon = QIcon("spray_bottle.png")
        self.setWindowIcon(icon)
        self.qud_object_model = QStandardItemModel()
        self.qud_object_model.setHorizontalHeaderLabels(['Name', 'Display Name'])
        # We only need to add Object to the model, since all other Objects are loaded as children:
        self.items_to_expand = []  # filled out during recursion of the Qud object tree
        self.qud_object_model.appendRow(self.init_qud_object(self.qud_object_model, qud_object_root))
        self.treeView.setModel(self.qud_object_model)
        for item in self.items_to_expand:
            recursive_expand(item, self.treeView, self.qud_object_model)
        self.treeView.setIndentation(10)
        self.treeView.clicked[QModelIndex].connect(self.tree_item_clicked)
        self.show()

    def init_qud_object(self, model: QStandardItemModel, qud_object: QudObject):
        """Recursive function to translate hierarchy from the Qud object AnyTree model to the
        Qt StandardItemModel model."""
        item = QStandardItem(qud_object.name)
        if not qud_object.is_leaf:
            for child in qud_object.children:
                item.appendRow(self.init_qud_object(model, child))
        if qud_object.is_specified('tag_BaseObject'):
            item.setSelectable(False)
        item.setCheckable(True)
        item.setData(qud_object)
        if qud_object.name in INITIAL_EXPANSION_TARGETS:
            self.items_to_expand.append(item)
        return item

    def tree_item_clicked(self, index):
        """Registered in __init__ as the handler for tree clicks."""
        item = self.qud_object_model.itemFromIndex(index)
        qud_object = item.data()
        text = pprint.pformat(qud_object.attributes)
        self.plainTextEdit.setPlainText(text)


app = QApplication(sys.argv)
app.setApplicationName("Qud Blueprint Explorer")
main_window = MainWindow(app)
app.exec_()

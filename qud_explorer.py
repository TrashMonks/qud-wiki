import sys
import os

from PySide2.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide2.QtWidgets import QMainWindow, QApplication, QTreeView, QSizePolicy, QAbstractItemView, \
    QFileDialog, QLabel

import qud_object_tree
from config import config
from qud_explorer_window import Ui_MainWindow
from qud_object import QudObject


def recursive_expand(item: QStandardItem, treeview: QTreeView, model: QStandardItemModel):
    index = model.indexFromItem(item)
    treeview.expand(index)
    if item.parent() is not None:
        recursive_expand(item.parent(), treeview, model)


class QudTreeView(QTreeView):
    def __init__(self, selection_handler, *args, **kwargs):
        """selection_handler: a function in the parent window to pass selected indices to"""
        self.selection_handler = selection_handler
        super().__init__(*args, **kwargs)

    def selectionChanged(self, selected, deselected):
        """Custom override to handle all forms of selection (keyboard, mouse)"""
        indices = self.selectedIndexes()
        self.selection_handler(indices)
        super().selectionChanged(selected, deselected)


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main application window for Qud Blueprint Explorer.

    The UI layout is derived from qud_explorer_window.py, which is compiled from
    qud_explorer_window.ui (designed graphically in Qt Designer) by the UIC executable that comes
    with PySide2."""
    def __init__(self, app: QApplication, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.app = app
        self.setupUi(self)  # lay out the inherited UI as in the graphical designer
        # instantiate custom QTreeView subclass
        self.treeView = QudTreeView(self.tree_selection_handler, self.centralwidget)
        self.init_qud_tree_view()
        icon = QIcon("book.png")
        self.setWindowIcon(icon)
        self.lineEdit.textChanged.connect(self.search_changed)
        self.actionOpen_ObjectBlueprints_xml.triggered.connect(self.open_xml)
        if os.path.exists('last_xml_location'):
            with open('last_xml_location') as f:
                filename = f.read()
            self.open_xml(filename)
        self.show()

    def open_xml(self, filename: None):
        """Browse for and open ObjectBluePrints.xml."""
        if not filename:
            filename = QFileDialog.getOpenFileName()[0]
        if filename.endswith('ObjectBlueprints.xml'):
            self.qud_object_root = qud_object_tree.load(filename)
            self.init_qud_tree_model()
        with open('last_xml_location', 'w') as f:
            f.write(filename)
        filename_widget = QLabel(text=filename)
        self.statusbar.addWidget(filename_widget)

    def init_qud_tree_view(self):
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.treeView.sizePolicy().hasHeightForWidth())
        self.treeView.setSizePolicy(size_policy)
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.treeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.treeView.setObjectName("treeView")
        self.verticalLayout_2.addWidget(self.treeView)
        self.treeView.setIndentation(10)

    def init_qud_tree_model(self):
        self.qud_object_model = QStandardItemModel()
        self.treeView.setModel(self.qud_object_model)
        # self.qud_object_model.setHorizontalHeaderLabels(['Name', 'Display Name'])
        self.items_to_expand = []  # filled out during recursion of the Qud object tree
        # We only need to add Object to the model, since all other Objects are loaded as children:
        root_item = self.init_qud_object(self.qud_object_model, self.qud_object_root)
        root_item.setSelectable(False)
        self.qud_object_model.appendRow(root_item)
        for item in self.items_to_expand:
            recursive_expand(item, self.treeView, self.qud_object_model)

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

        if qud_object.name in config['Interface']['Initial expansion targets']:
            self.items_to_expand.append(item)
        return item

    def tree_selection_handler(self, indices):
        """Registered with custom QudTreeView class as the handler for selection."""
        text = ""
        for index in indices:
            item = self.qud_object_model.itemFromIndex(index)
            qud_object = item.data()
            text += qud_object.wikify()
        self.plainTextEdit.setPlainText(text)

    def search_changed(self):
        pass


app = QApplication(sys.argv)
app.setApplicationName("Qud Blueprint Explorer")
main_window = MainWindow(app)
app.exec_()

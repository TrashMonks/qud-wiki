import sys
import os

from PySide2.QtCore import QSize
from PySide2.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap
from PySide2.QtWidgets import QMainWindow, QApplication, QTreeView, QSizePolicy, QAbstractItemView, \
    QFileDialog, QLabel, QHeaderView

import qud_object_tree
from config import config
from qud_explorer_window import Ui_MainWindow
from qudobject import QudObject
from qudtile import blank_qtimage
from wiki_config import site
from wikipage import WikiPage


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
        self.treeView = QudTreeView(self.tree_selection_handler, self.tree_target_widget)
        self.init_qud_tree_view()
        icon = QIcon("book.png")
        self.setWindowIcon(icon)
        self.search_line_edit.textChanged.connect(self.search_changed)
        self.actionOpen_ObjectBlueprints_xml.triggered.connect(self.open_xml)
        if os.path.exists('last_xml_location'):
            with open('last_xml_location') as f:
                filename = f.read()
            self.open_xml(filename)
        self.expand_all_button.clicked.connect(self.expand_all)
        self.collapse_all_button.clicked.connect(self.collapse_all)
        self.restore_all_button.clicked.connect(self.expand_default)
        self.upload_templates_button.clicked.connect(self.upload_selected_templates)
        self.upload_tiles_button.clicked.connect(self.upload_selected_tiles)
        self.currently_selected = []
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
        self.setWindowTitle("Qud Blueprint Explorer - " + filename)

    def init_qud_tree_view(self):
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.treeView.sizePolicy().hasHeightForWidth())
        self.treeView.setSizePolicy(size_policy)
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.treeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.treeView.setObjectName("treeView")
        self.verticalLayout.addWidget(self.treeView)
        self.treeView.setIndentation(10)
        self.treeView.setIconSize(QSize(16, 24))

    def init_qud_tree_model(self):
        self.qud_object_model = QStandardItemModel()
        self.treeView.setModel(self.qud_object_model)
        self.qud_object_model.setHorizontalHeaderLabels(['Name', 'Display'])
        header = self.treeView.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.items_to_expand = []  # filled out during recursion of the Qud object tree

        # We only need to add Object to the model, since all other Objects are loaded as children:
        self.qud_object_model.appendRow(self.init_qud_object_children(self.qud_object_root))
        self.expand_default()

    def init_qud_object_children(self, qud_object: QudObject):
        """Recursive function to translate hierarchy from the Qud object AnyTree model to the
        Qt StandardItemModel model."""
        item = QStandardItem(qud_object.name)
        if qud_object.is_specified('tag_BaseObject'):
            item.setSelectable(False)
        display_name = QStandardItem(qud_object.displayname)
        display_name.setSelectable(False)
        display_name.setSizeHint(QSize(0, 25))
        if qud_object.tile is None:
            display_name.setIcon(QIcon(QPixmap.fromImage(blank_qtimage)))
        else:
            display_name.setIcon(QIcon(QPixmap.fromImage(qud_object.tile.qtimage)))
        item.setData(qud_object)
        if not qud_object.is_leaf:
            for child in qud_object.children:
                item.appendRow(self.init_qud_object_children(child))
        if qud_object.name in config['Interface']['Initial expansion targets']:
            self.items_to_expand.append(item)
        return [item, display_name]

    def recursive_expand(self, item: QStandardItem):
        index = self.qud_object_model.indexFromItem(item)
        self.treeView.expand(index)
        if item.parent() is not None:
            self.recursive_expand(item.parent())

    def tree_selection_handler(self, indices: list):
        """Registered with custom QudTreeView class as the handler for selection."""
        self.currently_selected = indices
        self.statusbar.clearMessage()
        text = ""
        for index in indices:
            if index.column() == 0:
                item = self.qud_object_model.itemFromIndex(index)
                qud_object = item.data()
                text += qud_object.wikify()
                self.statusbar.showMessage(qud_object.ui_inheritance_path())
                if qud_object.tile is not None:
                    self.tile_label.setPixmap(QPixmap.fromImage(qud_object.tile.get_big_qtimage()))
                else:
                    self.tile_label.clear()
        self.plainTextEdit.setPlainText(text)

    def collapse_all(self):
        self.treeView.collapseAll()

    def expand_all(self):
        self.treeView.expandAll()

    def expand_default(self):
        self.collapse_all()
        for item in self.items_to_expand:
            self.recursive_expand(item)

    def search_changed(self):
        if self.search_line_edit.text() != '':
            self.treeView.scrollToTop()  # keyboardSearch is bad
            self.treeView.clearSelection()  # keyboardSearch is bad
            self.treeView.keyboardSearch(self.search_line_edit.text())
            selected = self.treeView.selectedIndexes()
            if len(selected) > 0:
                item = self.qud_object_model.itemFromIndex(selected[0]).data()
                self.recursive_expand(self.qud_object_model.itemFromIndex(selected[0]))

    def upload_selected_templates(self):
        for index in self.currently_selected:
            if index.column() == 0:
                item = self.qud_object_model.itemFromIndex(index)
                qud_object = item.data()
                page = WikiPage(qud_object)
                print(f'Page {page} exists:', page.exists())
                page.upload_template()

    def upload_selected_tiles(self):
        for index in self.currently_selected:
            if index.column() == 0:
                item = self.qud_object_model.itemFromIndex(index)
                qud_object = item.data()
                if qud_object.name in config['Templates']['Image overrides']:
                    filename = config['Templates']['Image overrides'][qud_object.name]
                else:
                    filename = qud_object.image
                print(site.upload(qud_object.tile.get_big_bytesio(),
                            filename=filename,
                            description='Automatically rendered by [[Qud Blueprint Explorer]].',
                            comment='automatically rendered by Qud Blueprint Explorer'))


app = QApplication(sys.argv)
app.setApplicationName("Qud Blueprint Explorer")
main_window = MainWindow(app)
app.exec_()

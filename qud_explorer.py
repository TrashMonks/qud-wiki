import sys
import os

from PySide2.QtCore import QSize, QThread
from PySide2.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap
from PySide2.QtWidgets import QMainWindow, QApplication, QTreeView, QSizePolicy, \
    QAbstractItemView, QFileDialog, QHeaderView

import qud_object_tree
from config import config
from qud_explorer_window import Ui_MainWindow
from qudobject import QudObject
from qudtile import blank_qtimage
from wiki_config import site, wiki_config
from wikipage import WikiPage

HEADER_LABELS = ['Name', 'Display', 'Article exists', 'Image exists']


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
        icon = QIcon("book.png")
        self.setWindowIcon(icon)
        self.qud_object_model = QStandardItemModel()
        self.items_to_expand = []  # filled out during recursion of the Qud object tree
        self.treeView = QudTreeView(self.tree_selection_handler, self.tree_target_widget)
        self.init_qud_tree_view()
        self.search_line_edit.textChanged.connect(self.search_changed)
        self.actionOpen_ObjectBlueprints_xml.triggered.connect(self.open_xml)
        if os.path.exists('last_xml_location'):
            with open('last_xml_location') as f:
                filename = f.read()
            self.open_xml(filename)
        self.expand_all_button.clicked.connect(self.expand_all)
        self.collapse_all_button.clicked.connect(self.collapse_all)
        self.restore_all_button.clicked.connect(self.expand_default)
        self.check_selected_button.clicked.connect(self.wiki_check_selected)
        self.compare_selected_button.clicked.connect(self.wiki_compare_selected)
        self.upload_templates_button.clicked.connect(self.upload_selected_templates)
        self.upload_tiles_button.clicked.connect(self.upload_selected_tiles)
        self.currently_selected = []
        self.show()

    def open_xml(self, filename=None):
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
        """Do some configuration for the QudTreeView."""
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
        """Initialize the Qud object model tree by setting up the root object."""
        self.treeView.setModel(self.qud_object_model)
        self.qud_object_model.setHorizontalHeaderLabels(HEADER_LABELS)
        header = self.treeView.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        # We only need to add Object to the model, since all other Objects are loaded as children:
        self.qud_object_model.appendRow(self.init_qud_object_children(self.qud_object_root))
        self.expand_default()

    def init_qud_object_children(self, qud_object: QudObject):
        """Recursive function to translate hierarchy from the Qud object AnyTree model to the
        Qt StandardItemModel model.

        Returns a list, which will be the list of column entries for the row."""
        item = QStandardItem(qud_object.name)
        display_name = QStandardItem(qud_object.displayname)
        # display_name.setSelectable(False)
        display_name.setSizeHint(QSize(250, 25))
        if qud_object.tile is None:
            display_name.setIcon(QIcon(QPixmap.fromImage(blank_qtimage)))
        elif qud_object.tile.blacklisted:
            display_name.setIcon(QIcon(QPixmap.fromImage(blank_qtimage)))
        else:
            display_name.setIcon(QIcon(QPixmap.fromImage(qud_object.tile.qtimage)))
        item.setData(qud_object)
        if not qud_object.is_leaf:
            for child in qud_object.children:
                item.appendRow(self.init_qud_object_children(child))
        if qud_object.name in config['Interface']['Initial expansion targets']:
            self.items_to_expand.append(item)
        wiki_article_exists = QStandardItem('')
        image_exists = QStandardItem('')
        if qud_object.is_specified('tag_BaseObject'):
            for _ in item, display_name, wiki_article_exists, image_exists:
                _.setSelectable(False)
        return [item, display_name, wiki_article_exists, image_exists]

    def recursive_expand(self, item: QStandardItem):
        """Expand the currently selected item in the QudTreeView and all its children."""
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
                text += qud_object.wiki_template() + '\n'
                self.statusbar.showMessage(qud_object.ui_inheritance_path())
                if qud_object.tile is not None and not qud_object.tile.blacklisted:
                    self.tile_label.setPixmap(QPixmap.fromImage(qud_object.tile.get_big_qtimage()))
                else:
                    self.tile_label.clear()
        if len(indices) == 0:
            self.tile_label.clear()
        self.plainTextEdit.setPlainText(text)

    def collapse_all(self):
        """Fully collapse all levels of the QudTreeView."""
        self.treeView.collapseAll()

    def expand_all(self):
        """Fully expand all levels of the QudTreeView."""
        self.treeView.expandAll()

    def expand_default(self):
        """Expand the QudTreeView to the levels configured in config.yml."""
        self.collapse_all()
        for item in self.items_to_expand:
            self.recursive_expand(item)

    def search_changed(self):
        """Called when the text in the search box has changed."""
        if self.search_line_edit.text() != '':
            self.treeView.scrollToTop()  # keyboardSearch is bad
            self.treeView.clearSelection()  # keyboardSearch is bad
            self.treeView.keyboardSearch(self.search_line_edit.text())
            selected = self.treeView.selectedIndexes()
            if len(selected) > 0:
                item = self.qud_object_model.itemFromIndex(selected[0]).data()
                self.recursive_expand(self.qud_object_model.itemFromIndex(selected[0]))

    def wiki_check_selected(self):
        """Check the wiki for the existence of the article and image for selected objects, and
        update the columns for those states."""
        # first, blank the cells for ones already checked
        for num, index in enumerate(self.currently_selected):
            if index.column() == 0:
                wiki_exists_qitem = self.qud_object_model.itemFromIndex(self.currently_selected[num + 2])
                tile_exists_qitem = self.qud_object_model.itemFromIndex(self.currently_selected[num + 3])
                wiki_exists_qitem.setText('')
                tile_exists_qitem.setText('')
        # now, do the actual checking and update the cells with 'yes' or 'no'
        for num, index in enumerate(self.currently_selected):
            if index.column() == 0:
                qitem = self.qud_object_model.itemFromIndex(index)
                wiki_exists_qitem = self.qud_object_model.itemFromIndex(self.currently_selected[num+2])
                tile_exists_qitem = self.qud_object_model.itemFromIndex(self.currently_selected[num+3])
                qud_object = qitem.data()
                # Check wiki page first:
                page = WikiPage(qud_object)
                if page.blacklisted:
                    wiki_exists_qitem.setText('-')
                    tile_exists_qitem.setText('-')
                    continue
                if page.exists():
                    wiki_exists_qitem.setText('Yes')
                else:
                    wiki_exists_qitem.setText('No')
                # Now check whether tile image exists:
                uploaded_tile_file = site.images[qud_object.image]
                if uploaded_tile_file.exists:
                    tile_exists_qitem.setText('Yes')
                else:
                    tile_exists_qitem.setText('No')
                self.app.processEvents()

    def wiki_compare_selected(self):
        """Compare the generated templates for the selected objects to the version on the wiki."""


    def upload_selected_templates(self):
        """Upload the generated templates for the selected objects to the wiki."""
        for index in self.currently_selected:
            if index.column() == 0:
                item = self.qud_object_model.itemFromIndex(index)
                qud_object = item.data()
                page = WikiPage(qud_object)
                if page.blacklisted:
                    print(f'{qud_object.name} is not suitable due to its name or displayname.')
                elif page.exists():
                    print(f'Page {page} already exists, updating not supported yet.')
                    continue
                else:
                    page.upload_template()

    def upload_selected_tiles(self):
        """Upload the generated tiles for the selected objects to the wiki."""
        for index in self.currently_selected:
            if index.column() != 0:
                continue
            item = self.qud_object_model.itemFromIndex(index)
            qud_object = item.data()
            if qud_object.tile is None:
                print(f'{qud_object.name} has no tile, so not uploading.')
                continue
            if qud_object.tile.blacklisted:
                print(f'{qud_object.name} had a tile, but bad rendering, so not uploading.')
                continue
            uploaded_tile_file = site.images[qud_object.image]
            if uploaded_tile_file.exists:
                print(f'Image {qud_object.image} already exists, updating not supported yet.')
                continue
            if qud_object.name in config['Templates']['Image overrides']:
                filename = config['Templates']['Image overrides'][qud_object.name]
            else:
                filename = qud_object.image
            descr = f'Rendered by {wiki_config["operator"]} using {config["Wiki name"]} {config["Version"]}.'
            result = site.upload(qud_object.tile.get_big_bytesio(),
                                 filename=filename,
                                 description=descr,
                                 comment=descr
                                 )
            print(result)


app = QApplication(sys.argv)
app.setApplicationName(config['App name'])
main_window = MainWindow(app)
app.exec_()

import io
import os
import sys
from pprint import pformat

from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap
from PySide2.QtWidgets import QMainWindow, QApplication, QTreeView, QSizePolicy, \
    QAbstractItemView, QFileDialog, QHeaderView, QMenu, QAction, QMessageBox

import qud_object_tree
from config import config
from qud_explorer_window import Ui_MainWindow
from qudobject import QudObject
from qudtile import blank_qtimage
from wiki_config import site, wiki_config
from wikipage import WikiPage

HEADER_LABELS = ['Name', 'Display', 'Override', 'Article exists', 'Article matches', 'Image exists',
                 'Image matches']


class QudTreeView(QTreeView):
    def __init__(self, selection_handler, *args, **kwargs):
        """selection_handler: a function in the parent window to pass selected indices to"""
        self.selection_handler = selection_handler
        super().__init__(*args, **kwargs)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(size_policy)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setObjectName("treeView")
        self.setIndentation(10)
        self.setIconSize(QSize(16, 24))
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_menu = QMenu()
        self.context_action_expand = QAction('Expand all', self.tree_menu)
        self.tree_menu.addAction(self.context_action_expand)
        self.context_action_scan = QAction('Scan wiki for selected objects', self.tree_menu)
        self.tree_menu.addAction(self.context_action_scan)
        self.context_action_upload_page = QAction('Upload templates for selected objects', self.tree_menu)
        self.tree_menu.addAction(self.context_action_upload_page)
        self.context_action_upload_tile = QAction('Upload tiles for selected objects', self.tree_menu)
        self.tree_menu.addAction(self.context_action_upload_tile)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def on_context_menu(self, point):
        print(point)
        self.tree_menu.exec_(self.mapToGlobal(point))

    def dothing(self):
        print('test')

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
        self.view_type = 'wiki'
        self.qud_object_model = QStandardItemModel()
        self.items_to_expand = []  # filled out during recursion of the Qud object tree
        self.treeView = QudTreeView(self.tree_selection_handler, self.tree_target_widget)
        self.verticalLayout.addWidget(self.treeView)
        self.search_line_edit.textChanged.connect(self.search_changed)
        # File menu:
        self.actionOpen_ObjectBlueprints_xml.triggered.connect(self.open_xml)
        # View type menu:
        self.actionWiki_template.triggered.connect(self.setview_wiki)
        self.actionAttributes.triggered.connect(self.setview_attr)
        self.actionAll_attributes.triggered.connect(self.setview_allattr)
        # TreeView context menu:
        self.treeView.context_action_expand.triggered.connect(self.expand_all)
        self.treeView.context_action_scan.triggered.connect(self.wiki_check_selected)
        self.treeView.context_action_upload_page.triggered.connect(self.upload_selected_templates)
        self.treeView.context_action_upload_tile.triggered.connect(self.upload_selected_tiles)
        # Wiki menu:
        self.actionScan_wiki.triggered.connect(self.wiki_check_selected)
        self.actionUpload_templates.triggered.connect(self.upload_selected_templates)
        self.actionUpload_tiles.triggered.connect(self.upload_selected_tiles)
        if os.path.exists('last_xml_location'):
            with open('last_xml_location') as f:
                filename = f.read()
            self.open_xml(filename)
        self.expand_all_button.clicked.connect(self.expand_all)
        self.collapse_all_button.clicked.connect(self.collapse_all)
        self.restore_all_button.clicked.connect(self.expand_default)
        self.save_tile_button.clicked.connect(self.save_selected_tile)
        self.save_tile_button.setDisabled(True)
        self.currently_selected = []
        self.currently_selected_for_tile = None
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
        item.setData(qud_object)
        display_name = QStandardItem(qud_object.displayname)
        # display_name.setSelectable(False)
        display_name.setSizeHint(QSize(250, 25))
        if qud_object.tile is None:
            display_name.setIcon(QIcon(QPixmap.fromImage(blank_qtimage)))
        elif qud_object.tile.blacklisted:
            display_name.setIcon(QIcon(QPixmap.fromImage(blank_qtimage)))
        else:
            display_name.setIcon(QIcon(QPixmap.fromImage(qud_object.tile.qtimage)))
        override_name = QStandardItem('')
        if qud_object.name in config['Wiki']['Article overrides']:
            override_name.setText(config['Wiki']['Article overrides'][qud_object.name])
        wiki_article_exists = QStandardItem('')
        wiki_article_matches = QStandardItem('')
        image_exists = QStandardItem('')
        image_matches = QStandardItem('')
        if not qud_object.is_wiki_eligible():
            for _ in item, display_name, override_name, wiki_article_exists, wiki_article_matches, image_exists:
                _.setSelectable(False)
        if qud_object.name in config['Interface']['Initial expansion targets']:
            self.items_to_expand.append(item)
        # recurse through children before returning self
        if not qud_object.is_leaf:
            for child in qud_object.children:
                item.appendRow(self.init_qud_object_children(child))
        return [item, display_name, override_name, wiki_article_exists, wiki_article_matches, image_exists, image_matches]

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
                if self.view_type == 'wiki':
                    text += qud_object.wiki_template() + '\n'
                elif self.view_type == 'attr':
                    text += pformat(qud_object.attributes, width=120)
                elif self.view_type == 'all_attr':
                    text += pformat(qud_object.all_attributes, width=120)
                self.statusbar.showMessage(qud_object.ui_inheritance_path())
                if qud_object.tile is not None and not qud_object.tile.blacklisted:
                    self.tile_label.setPixmap(QPixmap.fromImage(qud_object.tile.get_big_qtimage()))
                    self.currently_selected_for_tile = qud_object
                    self.save_tile_button.setDisabled(False)
                else:
                    self.tile_label.clear()
                    self.currently_selected_for_tile = None
                    self.save_tile_button.setDisabled(True)
        if len(indices) == 0:
            self.tile_label.clear()
            self.currently_selected_for_tile = None
            self.save_tile_button.setDisabled(True)
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
        QApplication.setOverrideCursor(Qt.WaitCursor)
        # first, blank the cells for ones already checked
        for num, index in enumerate(self.currently_selected):
            if index.column() == 0:
                wiki_exists_qitem = self.qud_object_model.itemFromIndex(self.currently_selected[num+3])
                wiki_matches_qitem = self.qud_object_model.itemFromIndex(self.currently_selected[num+4])
                tile_exists_qitem = self.qud_object_model.itemFromIndex(self.currently_selected[num+5])
                tile_matches_qitem = self.qud_object_model.itemFromIndex(self.currently_selected[num+6])
                wiki_exists_qitem.setText('')
                wiki_matches_qitem.setText('')
                tile_exists_qitem.setText('')
                tile_matches_qitem.setText('')
        # now, do the actual checking and update the cells with 'yes' or 'no'
        for num, index in enumerate(self.currently_selected):
            if index.column() == 0:
                qitem = self.qud_object_model.itemFromIndex(index)
                wiki_exists_qitem = self.qud_object_model.itemFromIndex(self.currently_selected[num+3])
                wiki_matches_qitem = self.qud_object_model.itemFromIndex(self.currently_selected[num+4])
                tile_exists_qitem = self.qud_object_model.itemFromIndex(self.currently_selected[num+5])
                tile_matches_qitem = self.qud_object_model.itemFromIndex(self.currently_selected[num + 6])
                qud_object = qitem.data()
                # Check wiki article first:
                if not qud_object.is_wiki_eligible:
                    wiki_exists_qitem.setText('-')
                    wiki_matches_qitem.setText('-')
                    tile_exists_qitem.setText('-')
                    tile_matches_qitem.setText('-')
                    continue
                article = WikiPage(qud_object)
                if article.page.exists:
                    wiki_exists_qitem.setText('✅')
                    # does the template match the article?
                    if qud_object.wiki_template().strip() in article.page.text():
                        wiki_matches_qitem.setText('✅')
                    else:
                        wiki_matches_qitem.setText('❌')
                else:
                    wiki_exists_qitem.setText('❌')
                    wiki_matches_qitem.setText('-')
                # Now check whether tile image exists:
                wiki_tile_file = site.images[qud_object.image]
                if wiki_tile_file.exists:
                    tile_exists_qitem.setText('✅')
                    # It exists, but does it match?
                    if wiki_tile_file.download() == qud_object.tile.get_big_bytes():
                        tile_matches_qitem.setText('✅')
                    else:
                        tile_matches_qitem.setText('❌')
                else:
                    tile_exists_qitem.setText('❌')
                    tile_matches_qitem.setText('-')
                self.app.processEvents()
        QApplication.restoreOverrideCursor()

    def upload_selected_templates(self):
        """Upload the generated templates for the selected objects to the wiki."""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        for num, index in enumerate(self.currently_selected):
            if index.column() == 0:
                item = self.qud_object_model.itemFromIndex(index)
                qud_object = item.data()
                if not qud_object.is_wiki_eligible():
                    print(f'{qud_object.name} is not suitable due to its name or displayname.')
                else:
                    uploadError = False
                    try:
                        page = WikiPage(qud_object)
                        page.upload_template()
                    except ValueError as e:
                        # page exists but format not recognized
                        print("Not uploading")
                        uploadError = True
                    if not uploadError:
                        self.qud_object_model.itemFromIndex(self.currently_selected[num+4]).setText('✅')
                        self.app.processEvents()
        QApplication.restoreOverrideCursor()


    def upload_selected_tiles(self):
        """Upload the generated tiles for the selected objects to the wiki."""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        for num, index in enumerate(self.currently_selected):
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
            wiki_tile_file = site.images[qud_object.image]
            if wiki_tile_file.exists:
                if wiki_tile_file.download() == qud_object.tile.get_big_bytes():
                    print(f'Image {qud_object.image} already exists and matches our version.')
                    continue
                else:
                    box = QMessageBox()
                    box.setText(f'Image for {qud_object.displayname} ({qud_object.image}) already'
                                f' exists but is different from the auto-generated version.')
                    box.setInformativeText(f'Please check the wiki version. Do you really want to'
                                           f' overwrite it?')
                    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    if box.exec_() == QMessageBox.No:
                        continue
            # if we get this far, we are uploading or replacing the wiki file
            if qud_object.name in config['Templates']['Image overrides']:
                filename = config['Templates']['Image overrides'][qud_object.name]
            else:
                filename = qud_object.image
            descr = f'Rendered by {wiki_config["operator"]} using {config["Wiki name"]} {config["Version"]}.'
            result = site.upload(qud_object.tile.get_big_bytesio(),
                                 filename=filename,
                                 description=descr,
                                 ignore=True,  # upload even if same file exists under diff. name
                                 comment=descr
                                 )
            if result.get('result', None) == 'Success':
                self.qud_object_model.itemFromIndex(self.currently_selected[num+6]).setText('✅')
                self.app.processEvents()
            print(result)
        QApplication.restoreOverrideCursor()

    def save_selected_tile(self):
        filename = QFileDialog.getSaveFileName()[0]
        self.currently_selected_for_tile.tile.get_big_image().save(filename, format='png')

    def setview_wiki(self):
        if self.view_type == 'wiki':
            return
        else:
            self.view_type = 'wiki'
            self.actionWiki_template.setChecked(True)
            self.actionAttributes.setChecked(False)
            self.actionAll_attributes.setChecked(False)
            selected = self.treeView.selectedIndexes()
            self.tree_selection_handler(selected)

    def setview_attr(self):
        if self.view_type == 'attr':
            return
        else:
            self.view_type = 'attr'
            self.actionWiki_template.setChecked(False)
            self.actionAttributes.setChecked(True)
            self.actionAll_attributes.setChecked(False)
            selected = self.treeView.selectedIndexes()
            self.tree_selection_handler(selected)

    def setview_allattr(self):
        if self.view_type == 'all_attr':
            return
        else:
            self.view_type = 'all_attr'
            self.actionWiki_template.setChecked(False)
            self.actionAttributes.setChecked(False)
            self.actionAll_attributes.setChecked(True)
            selected = self.treeView.selectedIndexes()
            self.tree_selection_handler(selected)


qbe_app = QApplication(sys.argv)
qbe_app.setApplicationName(config['App name'])
main_window = MainWindow(qbe_app)
qbe_app.exec_()

import difflib
import os
import re
import sys
from pprint import pformat

from PySide2.QtCore import QItemSelectionModel, QRegExp, QSize, QSortFilterProxyModel, Qt
from PySide2.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel
from PySide2.QtWidgets import QAbstractItemView, QAction, QApplication, QFileDialog, QHeaderView, \
    QMainWindow, QMenu, QMessageBox, QSizePolicy, QTreeView

from qudobject_wiki import QudObjectWiki
from hagadias.gameroot import GameRoot
from config import config
from qud_explorer_window import Ui_MainWindow
from hagadias.qudobject import QudObject
from hagadias.qudtile import blank_qtimage
from wiki_config import site, wiki_config
from wikipage import WikiPage

HEADER_LABELS = ['Name', 'Display', 'Override', 'Article exists', 'Article matches', 'Image exists',
                 'Image matches']
# TEMPLATE_RE copied from wikipage.py except that start/end patterns converted to non-capturing (?:)
TEMPLATE_RE = r"(?:.*?)(^{{(?:Item|Character|Food|Corpse).*^}}$)(?:.*)"


class QudFilterModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(QudFilterModel, self).__init__(parent)
        self.setRecursiveFilteringEnabled = True
        self.setFilterKeyColumn(0)
        self.filterSelections = []
        self.filterSelectionIDs = []
        # use of separate itemIDs list is a workaround for issue bugreports.qt.io/browse/PYSIDE-74,
        # which causes errors when using the 'in' operator on the filterSelections list's QItems

    def pop_selections(self):
        val1 = self.filterSelections
        val2 = self.filterSelectionIDs
        self.filterSelections = []
        self.filterSelectionIDs = []
        return val1, val2

    def _accept_index(self, idx):  # recursive search
        if idx.isValid():
            text = idx.data(role=Qt.DisplayRole).lower()
            found = text.find(self.filterRegExp().pattern().lower()) >= 0  # use QRegExp method?
            if found:
                item = self.sourceModel().itemFromIndex(idx)
                if item.isSelectable() and id(item) not in self.filterSelectionIDs:
                    self.filterSelections.append(item)
                    self.filterSelectionIDs.append(id(item))
                return True
            for childnum in range(idx.model().rowCount(idx)):
                if self._accept_index(idx.model().index(childnum, 0, idx)):
                    return True
        return False

    def filterAcceptsRow(self, source_row, source_parent):
        idx = self.sourceModel().index(source_row, 0, source_parent)  # 0 = first column
        return self._accept_index(idx)


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
        self.context_action_upload_page = QAction('Upload templates for selected objects',
                                                  self.tree_menu)
        self.tree_menu.addAction(self.context_action_upload_page)
        self.context_action_upload_tile = QAction('Upload tiles for selected objects',
                                                  self.tree_menu)
        self.tree_menu.addAction(self.context_action_upload_tile)
        self.context_action_diff = QAction('Diff template against wiki', self.tree_menu)
        self.tree_menu.addAction(self.context_action_diff)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def on_context_menu(self, point):
        # print(str(point) + "  '" + self.indexAt(point).data() + "'")
        self.tree_menu.exec_(self.mapToGlobal(point))

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
        self.qud_object_proxyfilter = QudFilterModel()
        self.qud_object_proxyfilter.setSourceModel(self.qud_object_model)
        self.items_to_expand = []  # filled out during recursion of the Qud object tree
        self.treeView = QudTreeView(self.tree_selection_handler, self.tree_target_widget)
        self.verticalLayout.addWidget(self.treeView)
        self.search_line_edit.textChanged.connect(self.search_changed)
        self.search_line_edit.returnPressed.connect(self.search_changed_forced)

        # Set up menus
        # File menu:
        self.actionOpen_ObjectBlueprints_xml.triggered.connect(self.open_gameroot)
        # View type menu:
        self.actionWiki_template.triggered.connect(self.setview_wiki)
        self.actionAttributes.triggered.connect(self.setview_attr)
        self.actionAll_attributes.triggered.connect(self.setview_allattr)
        self.actionXML_source.triggered.connect(self.setview_xmlsource)
        # Wiki menu:
        self.actionScan_wiki.triggered.connect(self.wiki_check_selected)
        self.actionUpload_templates.triggered.connect(self.upload_selected_templates)
        self.actionUpload_tiles.triggered.connect(self.upload_selected_tiles)
        # TreeView context menu:
        self.treeView.context_action_expand.triggered.connect(self.expand_all)
        self.treeView.context_action_scan.triggered.connect(self.wiki_check_selected)
        self.treeView.context_action_upload_page.triggered.connect(self.upload_selected_templates)
        self.treeView.context_action_upload_tile.triggered.connect(self.upload_selected_tiles)
        self.treeView.context_action_diff.triggered.connect(self.show_simple_diff)
        self.gameroot = None
        while self.gameroot is None:
            try:
                self.open_gameroot()
            except FileNotFoundError:
                self.set_gamedir()
        self.setWindowTitle("Qud Blueprint Explorer - " + self.gameroot.pathstr)
        self.qud_object_root, qindex_throwaway = self.gameroot.get_object_tree(QudObjectWiki)
        self.init_qud_tree_model()

        self.expand_all_button.clicked.connect(self.expand_all)
        self.collapse_all_button.clicked.connect(self.collapse_all)
        self.restore_all_button.clicked.connect(self.expand_default)
        self.save_tile_button.clicked.connect(self.save_selected_tile)
        self.save_tile_button.setDisabled(True)
        self.currently_selected = []
        self.top_selected = None  # used when multiple items may be selected but we only want one
        self.show()

    def set_gamedir(self):
        """Browse for the root game directory and write it to the file last_xml_location."""
        ask_string = 'Please locate the base directory containing the Caves of Qud executable.'
        dir_name = QFileDialog.getExistingDirectory(caption=ask_string)
        with open('last_xml_location', 'w') as f:
            f.write(dir_name)

    def open_gameroot(self):
        """Attempt to load a GameRoot from the saved root game directory."""
        try:
            with open('last_xml_location') as f:
                dir_name = f.read()
        except FileNotFoundError:
            raise
        self.gameroot = GameRoot(dir_name)

    def init_qud_tree_model(self):
        """Initialize the Qud object model tree by setting up the root object."""
        self.treeView.setModel(self.qud_object_proxyfilter)
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
        row = []
        # first column: displays the object ID and holds a reference to the actual qud_object
        item = QStandardItem(qud_object.name)
        item.setData(qud_object)
        row.append(item)
        # second column: the ingame display name
        display_name = QStandardItem(qud_object.displayname)
        display_name.setSizeHint(QSize(250, 25))
        if qud_object.tile is None:
            display_name.setIcon(QIcon(QPixmap.fromImage(blank_qtimage)))
        elif qud_object.tile.blacklisted:
            display_name.setIcon(QIcon(QPixmap.fromImage(blank_qtimage)))
        else:
            display_name.setIcon(QIcon(QPixmap.fromImage(qud_object.tile.qtimage)))
        row.append(display_name)
        # third column: what the name of the wiki article will be (usually same as second column)
        override_name = QStandardItem('')
        if qud_object.name in config['Wiki']['Article overrides']:
            override_name.setText(config['Wiki']['Article overrides'][qud_object.name])
        row.append(override_name)
        # fourth column: indicator for whether the wiki article exists (after scanning)
        wiki_article_exists = QStandardItem('')
        row.append(wiki_article_exists)
        # fifth column: indicator for whether the wiki article matches our generated template
        wiki_article_matches = QStandardItem('')
        row.append(wiki_article_matches)
        # sixth column: indicator for whether the tile image exists on the wiki (after scanning)
        image_exists = QStandardItem('')
        row.append(image_exists)
        # seventh column: indicator for whether the tile image on the wiki matches generated tile
        image_matches = QStandardItem('')
        row.append(image_matches)

        if not qud_object.is_wiki_eligible():
            for _ in row:
                _.setSelectable(False)
        if qud_object.name in config['Interface']['Initial expansion targets']:
            self.items_to_expand.append(item)
        # recurse through children before returning self
        if not qud_object.is_leaf:
            for child in qud_object.children:
                item.appendRow(self.init_qud_object_children(child))
        return row

    def recursive_expand(self, item: QStandardItem):
        """Expand the currently selected item in the QudTreeView and all its children."""
        index = self.qud_object_model.indexFromItem(item)
        self.treeView.expand(self.qud_object_proxyfilter.mapFromSource(index))
        if item.parent() is not None:
            self.recursive_expand(item.parent())

    def tree_selection_handler(self, indices: list):
        """Registered with custom QudTreeView class as the handler for selection."""
        self.currently_selected = indices
        self.statusbar.clearMessage()
        text = ""
        for index in indices:
            model_index = self.qud_object_proxyfilter.mapToSource(index)
            if model_index.column() == 0:
                item = self.qud_object_model.itemFromIndex(model_index)
                qud_object = item.data()
                if self.view_type == 'wiki':
                    text += qud_object.wiki_template() + '\n'
                elif self.view_type == 'attr':
                    text += pformat(qud_object.attributes, width=120)
                elif self.view_type == 'all_attr':
                    text += pformat(qud_object.all_attributes, width=120)
                elif self.view_type == 'xml_source':
                    # cosmetic: add two spaces to indent the opening <object> tag
                    text += '  ' + qud_object.source
                self.statusbar.showMessage(qud_object.ui_inheritance_path())
                self.top_selected = qud_object
                if qud_object.tile is not None and not qud_object.tile.blacklisted:
                    self.tile_label.setPixmap(QPixmap.fromImage(qud_object.tile.get_big_qtimage()))
                    self.save_tile_button.setDisabled(False)
                else:
                    self.tile_label.clear()
                    self.save_tile_button.setDisabled(True)
        if len(indices) == 0:
            self.tile_label.clear()
            self.top_selected = None
            self.save_tile_button.setDisabled(True)
        self.plainTextEdit.setPlainText(text)

    def collapse_all(self):
        """Fully collapse all levels of the QudTreeView."""
        self.treeView.collapseAll()

    def expand_all(self):
        """Fully expand all levels of the QudTreeView."""
        self.treeView.expandAll()
        self.clear_search_filter(True)

    def expand_default(self):
        """Expand the QudTreeView to the levels configured in config.yml."""
        self.collapse_all()
        for item in self.items_to_expand:
            self.recursive_expand(item)
        self.clear_search_filter(True)

    def scroll_to_selected(self):
        self.currently_selected = self.treeView.selectedIndexes()
        if self.currently_selected is not None and len(self.currently_selected) > 0:
            self.treeView.scrollTo(self.currently_selected[0])

    def clear_search_filter(self, clearfield: bool = False):
        if clearfield and len(self.search_line_edit.text()) > 0:
            self.search_line_edit.clear()
        self.qud_object_proxyfilter.setFilterRegExp('')
        self.scroll_to_selected()

    def search_changed(self, mode: str = ''):
        """Called when the text in the search box has changed. By default, the search box only
           begins filtering after 4 or more letters are entered. However, you can override that and
           search with fewer letters by hitting ENTER ('Forced' mode). You can also hit ENTER to
           move to the next match for an existing/active search query."""
        if len(self.search_line_edit.text()) <= 3:
            self.clear_search_filter(False)
        if len(self.search_line_edit.text()) > 3 \
                or (mode == 'Forced' and self.search_line_edit.text() != ''):
            self.qud_object_proxyfilter.pop_selections()  # clear any lingering data in proxyfilter
            self.qud_object_proxyfilter.setFilterRegExp(  # this applies the actual filtering
                QRegExp(self.search_line_edit.text(), Qt.CaseInsensitive, QRegExp.FixedString))
            self.treeView.expandAll()  # expands to show everything visible after filter is applied
            items, item_ids = self.qud_object_proxyfilter.pop_selections()
            if len(items) > 0:
                item = items[0]
                if mode == 'Forced':  # go to next filtered item each time the user presses ENTER
                    self.currently_selected = self.treeView.selectedIndexes()
                    if self.currently_selected is not None and self.selected_row_count() == 1:
                        currentitem = self.qud_object_model.itemFromIndex(
                            self.qud_object_proxyfilter.mapToSource(self.currently_selected[0]))
                        if id(currentitem) in item_ids:
                            newindex = item_ids.index(id(currentitem)) + 1
                            if newindex < len(items):
                                item = items[newindex]
                idx = self.qud_object_model.indexFromItem(item)
                idx = self.qud_object_proxyfilter.mapFromSource(idx)
                self.treeView.selectionModel().select(
                    idx, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
                self.scroll_to_selected()

    def search_changed_forced(self):
        self.search_changed('Forced')

    def selected_row_count(self):
        if self.currently_selected is not None:
            return len(self.currently_selected) // len(HEADER_LABELS)

    def wiki_check_selected(self):
        """Check the wiki for the existence of the article and image for selected objects, and
        update the columns for those states."""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        check_total = self.selected_row_count()
        check_count = 0
        for num, index in enumerate(self.currently_selected):
            model_index = self.qud_object_proxyfilter.mapToSource(index)
            if model_index.column() == 0:
                if check_total > 1:
                    check_count += 1
                    self.statusbar.showMessage("comparing selected entries against wiki:  " +
                                               str(check_count) + "/" + str(check_total))
                qitem = self.qud_object_model.itemFromIndex(model_index)
                wiki_exists = self.qud_object_model.itemFromIndex(
                    self.qud_object_proxyfilter.mapToSource(self.currently_selected[num + 3]))
                wiki_matches = self.qud_object_model.itemFromIndex(
                    self.qud_object_proxyfilter.mapToSource(self.currently_selected[num + 4]))
                tile_exists = self.qud_object_model.itemFromIndex(
                    self.qud_object_proxyfilter.mapToSource(self.currently_selected[num + 5]))
                tile_matches = self.qud_object_model.itemFromIndex(
                    self.qud_object_proxyfilter.mapToSource(self.currently_selected[num + 6]))
                # first, blank the cells
                for _ in wiki_exists, wiki_matches, tile_exists, tile_matches:
                    _.setText('')
                # now, do the actual checking and update the cells with 'yes' or 'no'
                qud_object = qitem.data()
                # Check wiki article first:
                if not qud_object.is_wiki_eligible:
                    wiki_exists.setText('-')
                    wiki_matches.setText('-')
                    tile_exists.setText('-')
                    tile_matches.setText('-')
                    continue
                article = WikiPage(qud_object)
                if article.page.exists:
                    wiki_exists.setText('✅')
                    # does the template match the article?
                    if qud_object.wiki_template().strip() in article.page.text().strip():
                        wiki_matches.setText('✅')
                    else:
                        wiki_matches.setText('❌')
                else:
                    wiki_exists.setText('❌')
                    wiki_matches.setText('-')
                # Now check whether tile image exists:
                wiki_tile_file = site.images[qud_object.image]
                if wiki_tile_file.exists:
                    tile_exists.setText('✅')
                    # It exists, but does it match?
                    if wiki_tile_file.download() == qud_object.tile.get_big_bytes():
                        tile_matches.setText('✅')
                    else:
                        tile_matches.setText('❌')
                else:
                    tile_exists.setText('❌')
                    tile_matches.setText('-')
                self.app.processEvents()
        # restore cursor and status bar text:
        self.statusbar.showMessage(self.top_selected.ui_inheritance_path())
        QApplication.restoreOverrideCursor()

    def upload_selected_templates(self):
        """Upload the generated templates for the selected objects to the wiki."""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        check_total = self.selected_row_count()
        check_count = 0
        for num, index in enumerate(self.currently_selected):
            model_index = self.qud_object_proxyfilter.mapToSource(index)
            if model_index.column() == 0:
                if check_total > 1:
                    check_count += 1
                    self.statusbar.showMessage("uploading selected templates to wiki:  " +
                                               str(check_count) + "/" + str(check_total))
                item = self.qud_object_model.itemFromIndex(model_index)
                qud_object = item.data()
                if not qud_object.is_wiki_eligible():
                    print(f'{qud_object.name} is disincluded from the wiki by blacklist or type.')
                else:
                    upload_processed = False
                    try:
                        page = WikiPage(qud_object)
                        if page.upload_template() == 'Success':
                            wiki_matches = self.qud_object_proxyfilter.mapToSource(
                                self.currently_selected[num + 4])
                            self.qud_object_model.itemFromIndex(wiki_matches).setText('✅')
                            self.app.processEvents()
                            upload_processed = True
                    except ValueError:
                        print("Not uploading: page exists but format not recognized")
                        upload_processed = True
                    finally:
                        if not upload_processed:  # unhandled exception during upload
                            self.statusbar.showMessage(self.top_selected.ui_inheritance_path())
                            QApplication.restoreOverrideCursor()
        # restore cursor and status bar text:
        self.statusbar.showMessage(self.top_selected.ui_inheritance_path())
        QApplication.restoreOverrideCursor()

    def upload_selected_tiles(self):
        """Upload the generated tiles for the selected objects to the wiki."""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        check_total = self.selected_row_count()
        check_count = 0
        for num, index in enumerate(self.currently_selected):
            model_index = self.qud_object_proxyfilter.mapToSource(index)
            if model_index.column() != 0:
                continue
            if check_total > 1:
                check_count += 1
                self.statusbar.showMessage("uploading selected tiles to wiki:  " +
                                           str(check_count) + "/" + str(check_total))
            item = self.qud_object_model.itemFromIndex(model_index)
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
                    QApplication.restoreOverrideCursor()  # restore mouse cursor for dialog
                    box = QMessageBox()
                    box.setText(f'Image for {qud_object.displayname} ({qud_object.image}) already'
                                f' exists but is different from the auto-generated version.')
                    box.setInformativeText(f'Please check the wiki version. Do you really want to'
                                           f' overwrite it?')
                    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    if box.exec_() == QMessageBox.No:
                        QApplication.setOverrideCursor(Qt.WaitCursor)
                        continue
                    QApplication.setOverrideCursor(Qt.WaitCursor)
            # if we get this far, we are uploading or replacing the wiki file
            if qud_object.name in config['Templates']['Image overrides']:
                filename = config['Templates']['Image overrides'][qud_object.name]
            else:
                filename = qud_object.image
            descr = f'Rendered by {wiki_config["operator"]} using' \
                    ' {config["Wiki name"]} {config["Version"]}.'
            upload_processed = False
            try:
                result = site.upload(qud_object.tile.get_big_bytesio(),
                                     filename=filename,
                                     description=descr,
                                     ignore=True,  # upload even if same file exists under diff name
                                     comment=descr
                                     )
                if result.get('result', None) == 'Success':
                    tile_matches = self.qud_object_proxyfilter.mapToSource(
                        self.currently_selected[num + 6])
                    self.qud_object_model.itemFromIndex(tile_matches).setText('✅')
                    self.app.processEvents()
                # print(result)
                upload_processed = True
            finally:
                if not upload_processed:  # unhandled exception during upload
                    self.statusbar.showMessage(self.top_selected.ui_inheritance_path())
                    QApplication.restoreOverrideCursor()
        # restore cursor and status bar text:
        self.statusbar.showMessage(self.top_selected.ui_inheritance_path())
        QApplication.restoreOverrideCursor()

    def save_selected_tile(self):
        if self.top_selected.tile is not None:
            filename = QFileDialog.getSaveFileName()[0]
            self.top_selected.tile.get_big_image().save(filename, format='png')

    def show_simple_diff(self):
        qud_object = self.top_selected
        if not qud_object.is_wiki_eligible():
            return
        article = WikiPage(qud_object)
        if not article.page.exists:
            return
        txt = qud_object.wiki_template().strip()
        wiki_txt = article.page.text().strip()
        qbe_pattern = re.compile(TEMPLATE_RE,
                                 re.MULTILINE | re.DOTALL)
        msg_box = QMessageBox()
        msg_box.setTextFormat(Qt.RichText)
        if txt in wiki_txt:
            msg_box.setText("No template differences detected.")
        else:
            m = qbe_pattern.match(txt)
            m_wiki = qbe_pattern.match(wiki_txt)
            if m is None:
                msg_box.setText('Unable to compare because the QBE template'
                                ' is not formatted as expected.')
            elif m_wiki is None:
                msg_box.setText('Unable to compare because the wiki template'
                                ' is not formatted as expected.')
            else:
                lines = m.group(1).splitlines()
                wiki_lines = m_wiki.group(1).splitlines()
                diff_lines = ''
                for line in difflib.unified_diff(wiki_lines, lines, "wiki", "QBE", lineterm=""):
                    diff_lines += '\n' + line
                msg_box.setText(f'Unified diff of the QBE template and the currently published'
                                f' wiki template:\n<pre>{diff_lines}</pre>')
        msg_box.exec()

    def setview(self, view: str):
        """Process a request to set the view type and update the checkmarks in the View menu.

        Parameters: view: one of 'wiki', 'attr', 'all_attr', 'xml_source'"""
        if self.view_type == view:
            return
        actions = {'wiki': self.actionWiki_template,
                   'attr': self.actionAttributes,
                   'all_attr': self.actionAll_attributes,
                   'xml_source': self.actionXML_source,
                   }
        self.view_type = view
        for action in actions.values():
            action.setChecked(False)
        actions[view].setChecked(True)
        selected = self.treeView.selectedIndexes()
        self.tree_selection_handler(selected)  # redraw the text view in the new type

    def setview_wiki(self):
        """Change the view type to wiki template."""
        self.setview('wiki')

    def setview_attr(self):
        """Change the view type to Attributes."""
        self.setview('attr')

    def setview_allattr(self):
        """Change the view type to All attributes."""
        self.setview('all_attr')

    def setview_xmlsource(self):
        """Change the view type to XML source."""
        self.setview('xml_source')


qbe_app = QApplication(sys.argv)
qbe_app.setApplicationName(config['App name'])
main_window = MainWindow(qbe_app)
qbe_app.exec_()

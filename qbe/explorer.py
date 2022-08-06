"""Main file for Qud Blueprint Explorer."""
import difflib
import os
import re
from pprint import pformat
from typing import Union, Callable

import yaml
from PIL import Image, ImageQt
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSize, Qt
from PySide6.QtGui import QIcon, QImage, QMovie, QPixmap, QStandardItem, QStandardItemModel, \
    QColor, QFont
from PySide6.QtWidgets import QApplication, QFileDialog, QHeaderView, QMainWindow, QMessageBox, \
    QDialog
from hagadias.gameroot import GameRoot
from hagadias.qudobject import QudObject
from hagadias.tileanimator import GifHelper

from qbe.config import config
from qbe.helpers import load_fonts_from_dir
from qbe.qud_explorer_image_modal import Ui_WikiImageUpload
from qbe.qud_explorer_window import Ui_MainWindow
from qbe.qudobject_wiki import QudObjectWiki
from qbe.search_filter import QudObjFilterModel, QudPopFilterModel, QudSearchBehaviorHandler
from qbe.tree_view import QudObjTreeView, QudPopTreeView
from qbe.wiki_config import site
from qbe.wiki_page import TEMPLATE_RE, TEMPLATE_RE_OLD, WikiPage, upload_wiki_image

OBJ_HEADER_LABELS = ['Object Name', 'Display Name', 'Wiki Title Override', 'Article?',
                     'Article matches?', 'Image?', 'Image matches?', 'Extra images?',
                     'Extra images match?']
POP_HEADER_LABELS = ['Name', 'Type']
OBJ_TAB_INDEX = 0
POP_TAB_INDEX = 1

blank_image = Image.new('RGBA', (16, 24), color=(0, 0, 0, 0))
blank_qtimage = ImageQt.ImageQt(blank_image)


def set_gamedir():
    """Browse for the root game directory and write it to the file last_xml_location."""
    ask_string = 'Please locate the base directory containing the Caves of Qud executable.'
    dir_name = QFileDialog.getExistingDirectory(caption=ask_string)
    try:
        with open('userconfig.yml', 'r') as f:
            user_settings = yaml.safe_load(f)
    except FileNotFoundError:
        user_settings = dict()
    user_settings['base directory'] = dir_name
    with open('userconfig.yml', 'w') as f:
        yaml.safe_dump(user_settings, f)


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main application window for Qud Blueprint Explorer.

    The UI layout is derived from qud_explorer_window.py, which is compiled from
    qud_explorer_window.ui (designed graphically in Qt Designer) by the UIC executable that comes
    with PySide6."""

    def __init__(self, app: QApplication, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.app = app
        load_fonts_from_dir('helpers')  # load Source Code Pro fonts for UI theme
        self.apply_theme()
        self.setupUi(self)  # lay out the inherited UI as in the graphical designer
        icon = QIcon("qbe/icon.png")
        self.setWindowIcon(icon)
        self.obj_view_type = 'wiki'
        self.qud_object_model = QStandardItemModel()
        self.qud_object_proxyfilter = QudObjFilterModel()
        self.qud_object_proxyfilter.setSourceModel(self.qud_object_model)
        self.objects_to_expand = []  # filled out during recursion of the Qud object tree
        self.objTreeView = QudObjTreeView(
            self.tree_selection_handler, OBJ_HEADER_LABELS, self.tree_target_widget)
        self.verticalLayout_3.addWidget(self.objTreeView)
        self.objTreeSearchHandler = QudSearchBehaviorHandler(
            self.search_line_edit, self.qud_object_proxyfilter, self.objTreeView)
        self.search_line_edit.textChanged.connect(self.objTreeSearchHandler.search_changed)
        self.search_line_edit.returnPressed.connect(self.objTreeSearchHandler.search_changed_forced)

        self.qud_pop_model = QStandardItemModel()
        self.qud_pop_proxyfilter = QudPopFilterModel()
        self.qud_pop_proxyfilter.setSourceModel(self.qud_pop_model)
        self.popTreeView = QudPopTreeView(self.pop_tree_selection_handler, POP_HEADER_LABELS,
                                          self.pop_tree_target_widget)
        self.pop_layout2_bottom.addWidget(self.popTreeView)
        self.popTreeSearchHandler = QudSearchBehaviorHandler(
            self.pop_search_line_edit, self.qud_pop_proxyfilter, self.popTreeView)
        self.pop_search_line_edit.textChanged.connect(self.popTreeSearchHandler.search_changed)
        self.pop_search_line_edit.returnPressed.connect(
            self.popTreeSearchHandler.search_changed_forced)
        self._prompt_for_image_changes = True

        # Set up menus
        # File menu:
        self.actionExit.triggered.connect(self.app.quit)
        # View type menu:
        self.actionWiki_template.triggered.connect(self.setview_wiki)
        self.actionAttributes.triggered.connect(self.setview_attr)
        self.actionAll_attributes.triggered.connect(self.setview_allattr)
        self.actionXML_source.triggered.connect(self.setview_xmlsource)
        self.actionToggle_Qud_mode.triggered.connect(self.toggle_qudmode)
        # Wiki menu:
        self.actionScan_wiki.triggered.connect(self.wiki_check_selected)
        self.actionDiff_template_against_wiki.triggered.connect(self.show_simple_diff)
        self.actionUpload_templates.triggered.connect(self.upload_selected_templates)
        self.actionUpload_tiles.triggered.connect(self.upload_selected_tiles)
        self.actionUpload_extra_image_s_for_selected_objects.triggered\
            .connect(self.upload_extra_images)
        self.actionSuppress_image_comparison_popups.triggered.connect(self.toggle_img_comparisons)
        # Help menu:
        self.actionShow_help.triggered.connect(self.show_help)
        # TreeView context menu:
        self.objTreeView.context_action_expand.triggered.connect(self.expand_all)
        self.objTreeView.context_action_scan.triggered.connect(self.wiki_check_selected)
        self.objTreeView.context_action_upload_page.triggered\
            .connect(self.upload_selected_templates)
        self.objTreeView.context_action_upload_tile.triggered.connect(self.upload_selected_tiles)
        self.objTreeView.context_action_upload_extra.triggered.connect(self.upload_extra_images)
        self.objTreeView.context_action_diff.triggered.connect(self.show_simple_diff)
        self.gameroot: Union[GameRoot, None] = None
        while self.gameroot is None:
            try:
                self.open_gameroot()
            except (FileNotFoundError, KeyError):
                set_gamedir()
        title_string = f'Qud Blueprint Explorer: CoQ version {self.gameroot.gamever} at ' \
                       f'{self.gameroot.pathstr}'
        self.setWindowTitle(title_string)
        self.qud_object_root, qindex_throwaway = self.gameroot.get_object_tree(QudObjectWiki)
        self.init_obj_tree_model()
        self.tabWidget.currentChanged.connect(self.tab_changed)
        self.population_data = None

        self.expand_all_button.clicked.connect(self.expand_all)
        self.collapse_all_button.clicked.connect(self.collapse_all)
        self.restore_all_button.clicked.connect(self.expand_default)

        self.pop_expand_all_button.clicked.connect(self.pop_expand_all)
        self.pop_collapse_all_button.clicked.connect(self.pop_collapse_all)
        self.pop_restore_all_button.clicked.connect(self.pop_collapse_all)

        self.save_tile_button.clicked.connect(self.save_selected_tile)
        self.save_tile_button.setDisabled(True)
        self.swap_tile_button.clicked.connect(self.swap_tile_mode)
        self.swap_tile_button.setDisabled(True)

        # GIF rendering attributes
        self.qbytearray: Union[QByteArray, None] = None
        self.qbuffer: Union[QBuffer, None] = None
        self.qmovie: Union[QMovie, None] = None
        self.gif_mode = False

        self.show()

    def open_gameroot(self):
        """Attempt to load a GameRoot from the saved root game directory."""
        try:
            with open('userconfig.yml', 'r') as f:
                user_settings = yaml.safe_load(f)
                dir_name = user_settings['base directory']
        except FileNotFoundError:
            try:
                # load path from legacy last_xml_location file if present
                with open('last_xml_location') as f:
                    dir_name = f.read()
                user_settings = {'base directory': dir_name}
                with open('userconfig.yml', 'w') as f:
                    yaml.safe_dump(user_settings, f)
                os.remove('last_xml_location')
            except FileNotFoundError:
                raise
        except KeyError:
            raise
        self.gameroot = GameRoot(dir_name)

    def init_obj_tree_model(self):
        """Initialize the Qud object model tree by setting up the root object."""
        self.objTreeView.setModel(self.qud_object_proxyfilter)
        self.qud_object_model.setHorizontalHeaderLabels(OBJ_HEADER_LABELS)
        header = self.objTreeView.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)

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
        elif qud_object.tile.hasproblems:
            display_name.setIcon(QIcon(QPixmap.fromImage(blank_qtimage)))
        else:
            display_name.setIcon(QIcon(QPixmap.fromImage(ImageQt.ImageQt(qud_object.tile.image))))
        row.append(display_name)
        # third column: what the name of the wiki article will be (usually same as second column)
        override_name = QStandardItem('')
        if qud_object.name in config['Wiki']['Article overrides']:
            override_name.setText(config['Wiki']['Article overrides'][qud_object.name])
        row.append(override_name)
        # fourth column: indicator for whether the wiki article exists (after scanning)
        wiki_article_exists = QStandardItem('')
        wiki_article_exists.setTextAlignment(Qt.AlignCenter)
        row.append(wiki_article_exists)
        # fifth column: indicator for whether the wiki article matches our generated template
        wiki_article_matches = QStandardItem('')
        wiki_article_matches.setTextAlignment(Qt.AlignCenter)
        row.append(wiki_article_matches)
        # sixth column: indicator for whether the tile image exists on the wiki (after scanning)
        image_exists = QStandardItem('')
        image_exists.setTextAlignment(Qt.AlignCenter)
        row.append(image_exists)
        # seventh column: indicator for whether the tile image on the wiki matches generated tile
        image_matches = QStandardItem('')
        image_matches.setTextAlignment(Qt.AlignCenter)
        row.append(image_matches)
        # eighth column: indicator for whether the GIF or other additional images exist on the wiki
        # (after scanning)
        extra_image_exists = QStandardItem('')
        extra_image_exists.setTextAlignment(Qt.AlignCenter)
        row.append(extra_image_exists)
        # ninth column: indicator for whether the GIF or other additional images match what's
        # already on the wiki
        extra_image_matches = QStandardItem('')
        extra_image_matches.setTextAlignment(Qt.AlignCenter)
        row.append(extra_image_matches)

        if not qud_object.is_wiki_eligible():
            row[0].setForeground(QColor.fromRgb(100, 100, 100))
            # for _ in row:
            #     _.setSelectable(False)
        else:
            font = QFont()
            font.setBold(True)
            row[0].setFont(font)
        if qud_object.name in config['Interface']['Initial expansion targets']:
            self.objects_to_expand.append(item)
        # recurse through children before returning self
        if not qud_object.is_leaf:
            for child in qud_object.children:
                item.appendRow(self.init_qud_object_children(child))
        return row

    def recursive_expand(self, item: QStandardItem):
        """Expand the currently selected item in the QudTreeView and all its children."""
        index = self.qud_object_model.indexFromItem(item)
        self.objTreeView.expand(self.qud_object_proxyfilter.mapFromSource(index))
        if item.parent() is not None:
            self.recursive_expand(item.parent())

    def tree_selection_handler(self, indices: list):
        """Registered with custom QudTreeView class as the handler for selection."""
        self.objTreeView.items_selected = indices
        self.statusbar.clearMessage()
        text = ""
        for num, index in enumerate(indices):
            model_index = self.qud_object_proxyfilter.mapToSource(index)
            if model_index.column() == 0:
                item = self.qud_object_model.itemFromIndex(model_index)
                qud_object = item.data()
                if self.obj_view_type == 'wiki':
                    if qud_object.is_wiki_eligible():
                        text += qud_object.wiki_template(self.gameroot.gamever) + '\n'
                    else:
                        text += f'{qud_object.name} is not enabled for wiki upload.' + '\n'
                elif self.obj_view_type == 'attr':
                    text += pformat(qud_object.attributes, width=120)
                elif self.obj_view_type == 'all_attr':
                    text += pformat(qud_object.all_attributes, width=120)
                elif self.obj_view_type == 'xml_source':
                    # cosmetic: add two spaces to indent the opening <object> tag
                    text += '  ' + qud_object.source
                self.statusbar.showMessage(qud_object.ui_inheritance_path())
                self.objTreeView.top_selected_item = qud_object
                self.objTreeView.top_selected_item_index = num
                self.gif_mode = False
                self.update_tile_display()
        if len(indices) == 0:
            self.tile_label.clear()
            self.objTreeView.top_selected_item = None
            self.objTreeView.top_selected_item_index = None
            self.save_tile_button.setDisabled(True)
            self.swap_tile_button.setDisabled(True)
        self.plainTextEdit.setPlainText(text)

    def update_tile_display(self):
        qud_object = self.objTreeView.top_selected_item
        if self.qmovie is not None:
            self.qmovie.stop()
        if self.qbuffer is not None:
            self.qbuffer.close()
        if qud_object is not None:
            self.tile_label.clear()
            if qud_object.tile is not None and not qud_object.tile.hasproblems:
                display_success = False
                if self.gif_mode and qud_object.has_gif_tile():
                    # can take a few moments for some animations
                    QApplication.setOverrideCursor(Qt.WaitCursor)
                    try:
                        gif_img = qud_object.gif_image(0)
                    finally:
                        QApplication.restoreOverrideCursor()
                    self.qbytearray = QByteArray(GifHelper.get_bytes(gif_img))
                    self.qbuffer = QBuffer(self.qbytearray, self)
                    self.qbuffer.open(QIODevice.ReadOnly)
                    self.qmovie = QMovie(self.qbuffer, b'GIF', self)
                    if self.qmovie.isValid():
                        self.qmovie.setCacheMode(QMovie.CacheAll)
                        self.tile_label.setMovie(self.qmovie)
                        self.qmovie.start()
                        display_success = True
                else:
                    pil_qt_image = ImageQt.ImageQt(qud_object.tile.get_big_image())
                    self.tile_label.setPixmap(QPixmap.fromImage(pil_qt_image))
                    display_success = True
                self.save_tile_button.setDisabled(True if not display_success else False)
                self.swap_tile_button.setDisabled(False if qud_object.has_gif_tile() else True)
            else:
                self.save_tile_button.setDisabled(True)
                self.swap_tile_button.setDisabled(True)

    def collapse_all(self):
        """Fully collapse all levels of the QudTreeView."""
        self.objTreeView.collapseAll()

    def expand_all(self):
        """Fully expand all levels of the QudTreeView."""
        self.objTreeView.expandAll()
        self.objTreeSearchHandler.clear_search_filter(True)

    def expand_default(self):
        """Expand the QudTreeView to the levels configured in config.yml."""
        self.collapse_all()
        for item in self.objects_to_expand:
            self.recursive_expand(item)
        self.objTreeSearchHandler.clear_search_filter(True)

    def get_icon_cell(self, index_in_items_selected: int) -> QStandardItem:
        qmodelindex = self.qud_object_proxyfilter\
            .mapToSource(self.objTreeView.items_selected[index_in_items_selected])
        cell = self.qud_object_model.itemFromIndex(qmodelindex)
        return cell

    def set_icon(self, index_in_items_selected: int, icon: str = '✅', update_ui: bool = False):
        cell = self.get_icon_cell(index_in_items_selected)
        cell.setText(icon)
        if icon == '⮿':
            cell.setForeground(QColor.fromRgb(100, 100, 100))  # grey
        if update_ui is True:
            self.app.processEvents()

    def tab_changed(self, idx: int):
        if idx == POP_TAB_INDEX:
            self.menuWiki.setDisabled(True)
            self.load_populations()
        elif idx == OBJ_TAB_INDEX:
            self.menuWiki.setEnabled(True)

    def load_populations(self):
        if self.population_data is not None:
            return
        self.population_data = self.gameroot.get_populations()
        self.init_qud_pop_tree_model()

    def init_qud_pop_tree_model(self):
        """Initialize the Qud object model tree by setting up the root object."""
        self.popTreeView.setModel(self.qud_pop_proxyfilter)
        self.qud_pop_model.setHorizontalHeaderLabels(POP_HEADER_LABELS)
        header = self.popTreeView.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        for pop_name, pop_value in self.population_data.items():
            row = []
            item = QStandardItem(pop_name)
            item.setData(pop_value)
            font = QFont()
            font.setBold(True)
            item.setFont(font)
            row.append(item)  # do this for each additional column
            row.append(QStandardItem('population'))
            for pop_child in pop_value.children:
                item.appendRow(self.init_qud_pop_children(pop_child))
            self.qud_pop_model.appendRow(row)
        self.popTreeView.collapseAll()

    def init_qud_pop_children(self, pop_item):  # pop_item: QudPopItem):
        child = QStandardItem(pop_item.displayname)
        if pop_item.type == 'group':
            for pop_child in pop_item.children:
                child.appendRow(self.init_qud_pop_children(pop_child))
        child.setForeground(QColor.fromRgb(100, 100, 100))
        child_type = QStandardItem(pop_item.type)
        child_type.setForeground(QColor.fromRgb(100, 100, 100))
        return [child, child_type]

    def pop_expand_all(self):
        self.popTreeView.expandAll()
        self.popTreeSearchHandler.clear_search_filter(True)

    def pop_collapse_all(self):
        self.popTreeView.collapseAll()

    def pop_tree_selection_handler(self, indices: list):
        """Registered with custom QudTreeView class as the handler for selection."""
        self.popTreeView.items_selected = indices
        self.statusbar.clearMessage()
        for num, index in enumerate(indices):
            model_index = self.qud_pop_proxyfilter.mapToSource(index)
            if model_index.column() == 0:
                item = self.qud_pop_model.itemFromIndex(model_index)
                pop_entry = item.data()
                if pop_entry is not None:
                    self.pop_plainTextEdit.setPlainText(pop_entry.xml)
                    self.statusbar.showMessage(item.text())  # population name
                else:
                    self.pop_plainTextEdit.clear()
                    self.statusbar.showMessage(item.text())
        if len(indices) == 0:
            self.pop_plainTextEdit.clear()
            pass

    def wiki_check_selected(self):
        """Check the wiki for the existence of the article and image(s) for selected objects, and
        update the columns for those states."""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        statusbar_current = self.statusbar.currentMessage()
        check_total = self.objTreeView.selected_row_count()
        check_count = 0
        for num, index in enumerate(self.objTreeView.items_selected):
            model_index = self.qud_object_proxyfilter.mapToSource(index)
            if model_index.column() == 0:
                if check_total > 1:
                    check_count += 1
                    self.statusbar.showMessage("comparing selected entries against wiki:  " +
                                               str(check_count) + "/" + str(check_total))
                qitem = self.qud_object_model.itemFromIndex(model_index)
                wiki_exists = self.get_icon_cell(num + 3)
                wiki_matches = self.get_icon_cell(num + 4)
                tile_exists = self.get_icon_cell(num + 5)
                tile_matches = self.get_icon_cell(num + 6)
                extra_imgs_exist = self.get_icon_cell(num + 7)
                extra_imgs_match = self.get_icon_cell(num + 8)
                # first, blank the cells
                for _ in wiki_exists, wiki_matches, tile_exists,\
                        tile_matches, extra_imgs_exist, extra_imgs_match:
                    _.setText('')
                # now, do the actual checking and update the cells with 'yes' or 'no'
                qud_object = qitem.data()
                # Check wiki article first:
                if not qud_object.is_wiki_eligible():
                    wiki_exists.setText('⮿')
                    wiki_exists.setForeground(QColor.fromRgb(100, 100, 100))  # grey
                    wiki_matches.setText('⮿')
                    wiki_matches.setForeground(QColor.fromRgb(100, 100, 100))
                    tile_exists.setText('⮿')
                    tile_exists.setForeground(QColor.fromRgb(100, 100, 100))
                    tile_matches.setText('⮿')
                    tile_matches.setForeground(QColor.fromRgb(100, 100, 100))
                    extra_imgs_exist.setText('⮿')
                    extra_imgs_exist.setForeground(QColor.fromRgb(100, 100, 100))
                    extra_imgs_match.setText('⮿')
                    extra_imgs_match.setForeground(QColor.fromRgb(100, 100, 100))
                    continue
                article = WikiPage(qud_object, self.gameroot.gamever)
                if article.page.exists:
                    wiki_exists.setText('✅')
                    # does the template match the article?
                    new_template = qud_object.wiki_template(self.gameroot.gamever).strip()
                    if self.check_template_match(new_template, article.page.text().strip()):
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
                elif qud_object.has_tile():
                    tile_exists.setText('❌')
                    tile_matches.setText('❌')
                else:
                    tile_exists.setText('⮿')
                    tile_exists.setForeground(QColor.fromRgb(100, 100, 100))  # grey
                    tile_matches.setText('⮿')
                    tile_matches.setForeground(QColor.fromRgb(100, 100, 100))
                # Now check whether GIF or other images exist:
                wiki_gif_file = site.images[qud_object.gif]
                gif_exists = wiki_gif_file.exists
                altimages_exist = False
                if qud_object.number_of_tiles() > 1:
                    altimages_exist = True
                    alt_tiles, alt_metas = qud_object.tiles_and_metadata()
                    total_altimages = len(alt_tiles)
                    msg_prefix = self.statusbar.currentMessage()
                    current_index = -1
                    for alt_tile, alt_meta in zip(alt_tiles, alt_metas):
                        current_index += 1
                        self.statusbar.showMessage(msg_prefix +
                                                   '    [scanning wiki for extra images ' +
                                                   f'{current_index + 1}/{total_altimages}]')
                        self.app.processEvents()
                        alt_file = site.images[alt_meta.filename]
                        if not alt_file.exists:
                            altimages_exist = False
                    self.statusbar.showMessage(msg_prefix)
                    self.app.processEvents()
                if gif_exists or altimages_exist:
                    extra_imgs_exist.setText('✅')
                    gif_matches = True
                    altimages_match = True
                    # does the GIF match what's already on the wiki?
                    # TODO: This isn't properly recognizing matching images. If you upload to wiki,
                    #  and then restart QBE, it will indicate that the GIF image doesn't match
                    #  what's on the wiki.
                    if gif_exists and wiki_gif_file.download() != \
                            GifHelper.get_bytes(qud_object.gif_image(0)):
                        gif_matches = False
                    # do all of the alt images match what's already on the wiki?
                    alt_tiles, alt_metas = qud_object.tiles_and_metadata()
                    total_altimages = len(alt_tiles)
                    msg_prefix = self.statusbar.currentMessage()
                    current_index = -1
                    for alt_tile, alt_meta in zip(alt_tiles, alt_metas):
                        current_index += 1
                        self.statusbar.showMessage(msg_prefix +
                                                   '    [comparing extra images to wiki images ' +
                                                   f'{current_index + 1}/{total_altimages}]')
                        self.app.processEvents()
                        alt_file = site.images[alt_meta.filename]
                        if alt_file.exists and alt_file.download() != alt_tile.get_big_bytes():
                            altimages_match = False
                        # Temporarily disabled because comparison with wiki gifs doesn't work:
                        # if alt_meta.is_animated():
                        #     alt_file_gif = site.images[alt_meta.gif_filename]
                        #     if alt_file_gif.exists:
                        #         alt_qbe_gif = qud_object.gif_image(i)
                        #         if alt_file_gif.download() != GifHelper.get_bytes(alt_qbe_gif):
                        #             altimages_match = False
                    self.statusbar.showMessage(msg_prefix)
                    self.app.processEvents()
                    if gif_matches and altimages_match:
                        extra_imgs_match.setText('✅')
                    else:
                        extra_imgs_match.setText('❌')
                else:
                    if qud_object.has_gif_tile() or qud_object.number_of_tiles() > 1:
                        extra_imgs_exist.setText('❌')
                        extra_imgs_match.setText('-')
                    else:
                        extra_imgs_exist.setText('⮿')
                        extra_imgs_exist.setForeground(QColor.fromRgb(100, 100, 100))  # grey
                        extra_imgs_match.setText('⮿')
                        extra_imgs_match.setForeground(QColor.fromRgb(100, 100, 100))  # grey
                self.app.processEvents()
        # restore cursor and status bar text:
        if self.objTreeView.top_selected_item is not None:
            self.statusbar.showMessage(self.objTreeView.top_selected_item.ui_inheritance_path())
        self.statusbar.showMessage(statusbar_current)
        self.app.processEvents()
        QApplication.restoreOverrideCursor()

    def toggle_img_comparisons(self):
        """Toggle whether image comparison pop-ups are shown when uploading tiles or extra images.
        If toggled off, images will be uploaded regardless of differences with no warnings. This is
        not currently saved across sessions."""
        self._prompt_for_image_changes = not self._prompt_for_image_changes

    def upload_selected_templates(self):
        """Upload the generated templates for all currently selected objects to the wiki."""
        self.upload_wikidata(self.upload_wiki_template, 'templates')

    def upload_selected_tiles(self):
        """Upload the generated tiles for all currently selected objects to the wiki."""
        self.upload_wikidata(self.upload_wiki_tile, 'tiles')

    def upload_extra_images(self):
        """Upload extra image(s) for all currently selected objects to the wiki."""
        self.upload_wikidata(self.upload_wiki_extra_images, 'extra images')

    def upload_wikidata(self, object_handler: Callable[[QudObjectWiki, int], None],
                        data_descriptor: str):
        """Generic wiki data upload template. Iterates through all selected objects in the tree,
        calling the object_handler() method on each of them. The handler method is responsible
        for performing the upload.
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        check_total = self.objTreeView.selected_row_count()
        check_count = 0
        for num, index in enumerate(self.objTreeView.items_selected):
            model_index = self.qud_object_proxyfilter.mapToSource(index)
            if model_index.column() == 0:
                if check_total > 1:
                    check_count += 1
                    self.statusbar.showMessage(f'uploading selected {data_descriptor} to wiki:  ' +
                                               str(check_count) + "/" + str(check_total))
                item = self.qud_object_model.itemFromIndex(model_index)
                qud_object = item.data()
                if not qud_object.is_wiki_eligible():
                    print(f'{qud_object.name} is not wiki eligible.')
                else:
                    upload_processed = False
                    try:  # wrapped in try to ensure we always restore the mouse cursor
                        object_handler(qud_object, num)
                        upload_processed = True
                    finally:
                        if not upload_processed:
                            QApplication.restoreOverrideCursor()
                            if self.objTreeView.top_selected_item is not None:
                                self.statusbar.showMessage(
                                    self.objTreeView.top_selected_item.ui_inheritance_path())
        # restore cursor and status bar text:
        QApplication.restoreOverrideCursor()
        if self.objTreeView.top_selected_item is not None:
            self.statusbar.showMessage(self.objTreeView.top_selected_item.ui_inheritance_path())

    def upload_wiki_template(self, qud_object: QudObjectWiki, selection_index: int):
        """Uploads a single template to the relevant wiki page.

        Intended for use as an object_handler provided to the upload_wikidata() method.
        """
        wiki_exists_cell_index = selection_index + 3
        wiki_matches_cell_index = selection_index + 4
        try:
            page = WikiPage(qud_object, self.gameroot.gamever)
            if page.upload_template() == 'Success':
                self.set_icon(wiki_exists_cell_index, '✅')
                self.set_icon(wiki_matches_cell_index, '✅')
                self.app.processEvents()
        except ValueError:
            print(f"Not uploading: page exists but format not recognized ({qud_object.name})")

    def upload_wiki_tile(self, qud_object: QudObjectWiki, selection_index: int):
        """Uploads a single image to the relevant wiki page.

        Intended for use as an object_handler provided to the upload_wikidata() method.
        """
        tile_exists_cell_index = selection_index + 5
        tile_matches_cell_index = selection_index + 6
        if qud_object.tile is None:
            print(f'{qud_object.name} has no tile, so not uploading.')
            self.set_icon(tile_exists_cell_index, '❌', True)
            return
        if qud_object.tile.hasproblems:
            print(f'{qud_object.name} had a tile, but bad rendering, so not uploading.')
            return
        wiki_tile_file = site.images[qud_object.image]
        if wiki_tile_file.exists:
            self.set_icon(tile_exists_cell_index, '✅', True)
            wiki_tile_b = wiki_tile_file.download()
            if wiki_tile_b == qud_object.tile.get_big_bytes():
                self.set_icon(tile_matches_cell_index, '✅', True)
                print(f'Image {qud_object.image} already exists and matches our version.')
                return
            else:
                self.set_icon(tile_matches_cell_index, '❌', True)
                if self._prompt_for_image_changes:
                    QApplication.restoreOverrideCursor()  # temporarily restore cursor for dialog

                    dialog = QDialog()
                    dialog.ui = Ui_WikiImageUpload()
                    dialog.ui.setupUi(dialog)
                    dialog.setAttribute(Qt.WA_DeleteOnClose)
                    # add images
                    qbe_image = ImageQt.ImageQt(qud_object.tile.get_big_image())
                    wiki_image = QImage.fromData(QByteArray(wiki_tile_b))
                    dialog.ui.comparison_tile_1.setPixmap(QPixmap.fromImage(qbe_image))
                    dialog.ui.comparison_tile_2.setPixmap(QPixmap.fromImage(wiki_image))
                    # show compare dialog
                    result = dialog.exec()

                    QApplication.setOverrideCursor(Qt.WaitCursor)
                    if result == QDialog.Rejected:
                        return

        # upload or replace the wiki file
        filename = qud_object.image
        result = upload_wiki_image(qud_object.tile.get_big_bytesio(), filename,
                                   self.gameroot.gamever, qud_object.tile.filename)
        if result.get('result', None) == 'Success':
            self.set_icon(tile_exists_cell_index, '✅')
            self.set_icon(tile_matches_cell_index, '✅', True)

    def upload_wiki_extra_images(self, qud_object: QudObjectWiki, selection_index: int):
        """Uploads a single object's extra image(s) to the relevant wiki page.

        Intended for use as an object_handler provided to the upload_wikidata() method.

        Extra images include GIF animations and alternate tiles (such as those associated with
        the RandomTile or Harvestable parts).
        """
        extraimages_exist_cell_index = selection_index + 7
        extraimages_match_cell_index = selection_index + 8
        has_gif = qud_object.has_gif_tile()
        has_altimages = qud_object.number_of_tiles() > 1
        if not has_gif and not has_altimages:
            self.set_icon(extraimages_exist_cell_index, '⮿', True)
            self.set_icon(extraimages_match_cell_index, '⮿', True)
            print(f'{qud_object.name} has no extra images, so not uploading.')
            return

        success_ct = 0
        fail_ct = 0
        mismatch_ct = 0

        if has_gif:
            attempt_upload = False
            wiki_gif_file = site.images[qud_object.gif]
            if wiki_gif_file.exists:
                self.set_icon(extraimages_exist_cell_index, '✅', True)
                wiki_gif_b = wiki_gif_file.download()
                if wiki_gif_b == GifHelper.get_bytes(qud_object.gif_image(0)):
                    print(f'Image "{qud_object.gif}" already exists and matches our version.')
                    success_ct += 1
                elif not self._prompt_for_image_changes:
                    attempt_upload = True
                else:
                    QApplication.restoreOverrideCursor()  # temporarily restore cursor for dialog

                    dialog = QDialog()
                    dialog.ui = Ui_WikiImageUpload()
                    dialog.ui.setupUi(dialog)
                    dialog.setAttribute(Qt.WA_DeleteOnClose)
                    # add QBE GIF
                    qbe_gif_bytearray = QByteArray(GifHelper.get_bytes(qud_object.gif_image(0)))
                    qbe_gif_buffer = QBuffer(qbe_gif_bytearray)
                    qbe_gif_buffer.open(QIODevice.ReadOnly)
                    qbe_gif_player = QMovie(qbe_gif_buffer, b'GIF')
                    if qbe_gif_player.isValid():
                        qbe_gif_player.setCacheMode(QMovie.CacheAll)
                        dialog.ui.comparison_tile_1.setMovie(qbe_gif_player)
                        qbe_gif_player.start()
                    # add wiki GIF
                    wiki_gif_bytearray = QByteArray(wiki_gif_b)
                    wiki_gif_buffer = QBuffer(wiki_gif_bytearray)
                    wiki_gif_buffer.open(QIODevice.ReadOnly)
                    wiki_gif_player = QMovie(wiki_gif_buffer, b'GIF')
                    if wiki_gif_player.isValid():
                        wiki_gif_player.setCacheMode(QMovie.CacheAll)
                        dialog.ui.comparison_tile_2.setMovie(wiki_gif_player)
                        wiki_gif_player.start()
                    # show compare dialog
                    result = dialog.exec()
                    # close buffers
                    qbe_gif_player.stop()
                    qbe_gif_buffer.close()
                    wiki_gif_player.stop()
                    wiki_gif_buffer.close()

                    QApplication.setOverrideCursor(Qt.WaitCursor)
                    if result != QDialog.Rejected:
                        attempt_upload = True
                    else:
                        mismatch_ct += 1
            else:
                attempt_upload = True

            if attempt_upload:
                # upload or replace the extra image(s) on the wiki
                filename = qud_object.gif
                result = upload_wiki_image(GifHelper.get_bytesio(qud_object.gif_image(0)), filename,
                                           self.gameroot.gamever)
                if result.get('result', None) == 'Success':
                    success_ct += 1
                else:
                    fail_ct += 1

        if has_altimages:
            tiles, metadata = qud_object.tiles_and_metadata()
            statusbar_current = self.statusbar.currentMessage()
            total_altimages = len(tiles)
            current_index = -1

            for tile, meta in zip(tiles, metadata):
                # update statusbar message
                current_index += 1
                self.statusbar.showMessage(f'{statusbar_current}    [uploading image ' +
                                           f'{current_index + 1}/{total_altimages}]')
                self.app.processEvents()

                # first, handle .png image
                should_upload_image = False
                image_file = site.images[meta.filename]
                if not image_file.exists:
                    should_upload_image = True
                else:
                    self.set_icon(extraimages_exist_cell_index, '✅', True)
                    image_b = image_file.download()
                    if image_b == tile.get_big_bytes():
                        print(f'Extra image "{meta.filename}" already exists and ' +
                              'matches our version.')
                        success_ct += 1
                    else:
                        self.set_icon(extraimages_match_cell_index, '❌', True)
                        if not self._prompt_for_image_changes:
                            should_upload_image = True
                        else:
                            # temporarily restore cursor for dialog
                            QApplication.restoreOverrideCursor()

                            dialog = QDialog()
                            dialog.ui = Ui_WikiImageUpload()
                            dialog.ui.setupUi(dialog)
                            dialog.setAttribute(Qt.WA_DeleteOnClose)
                            # add images
                            qbe_image = ImageQt.ImageQt(tile.get_big_image())
                            wiki_image = QImage.fromData(QByteArray(image_b))
                            dialog.ui.comparison_tile_1.setPixmap(QPixmap.fromImage(qbe_image))
                            dialog.ui.comparison_tile_2.setPixmap(QPixmap.fromImage(wiki_image))
                            # show compare dialog
                            result = dialog.exec()

                            QApplication.setOverrideCursor(Qt.WaitCursor)
                            if result == QDialog.Rejected:
                                mismatch_ct += 1
                            else:
                                should_upload_image = True

                # then, handle .gif image
                should_upload_gif = False
                qbe_gif = qud_object.gif_image(current_index)
                wiki_gif = site.images[meta.gif_filename]
                if not wiki_gif.exists:
                    should_upload_gif = True if qbe_gif is not None else False
                elif qbe_gif is not None:
                    self.set_icon(extraimages_exist_cell_index, '✅', True)
                    wiki_gif_b = wiki_gif.download()
                    if wiki_gif_b == GifHelper.get_bytes(qbe_gif):
                        # TODO: This probably doesn't work, so figure out why our comparison to
                        #  wiki .gif is failing
                        print(f'Extra image "{meta.filename}" already exists ' +
                              'and matches our version.')
                        success_ct += 1
                    elif not self._prompt_for_image_changes:
                        should_upload_gif = True
                    else:
                        # temporarily restore cursor for dialog
                        QApplication.restoreOverrideCursor()

                        dialog = QDialog()
                        dialog.ui = Ui_WikiImageUpload()
                        dialog.ui.setupUi(dialog)
                        dialog.setAttribute(Qt.WA_DeleteOnClose)
                        # add QBE GIF
                        qbe_gif_bytearray = QByteArray(GifHelper.get_bytes(qbe_gif))
                        qbe_gif_buffer = QBuffer(qbe_gif_bytearray)
                        qbe_gif_buffer.open(QIODevice.ReadOnly)
                        qbe_gif_player = QMovie(qbe_gif_buffer, b'GIF')
                        if qbe_gif_player.isValid():
                            qbe_gif_player.setCacheMode(QMovie.CacheAll)
                            dialog.ui.comparison_tile_1.setMovie(qbe_gif_player)
                            qbe_gif_player.start()
                        # add wiki GIF
                        wiki_gif_bytearray = QByteArray(wiki_gif_b)
                        wiki_gif_buffer = QBuffer(wiki_gif_bytearray)
                        wiki_gif_buffer.open(QIODevice.ReadOnly)
                        wiki_gif_player = QMovie(wiki_gif_buffer, b'GIF')
                        if wiki_gif_player.isValid():
                            wiki_gif_player.setCacheMode(QMovie.CacheAll)
                            dialog.ui.comparison_tile_2.setMovie(wiki_gif_player)
                            wiki_gif_player.start()
                        # show compare dialog
                        result = dialog.exec()
                        # close buffers
                        qbe_gif_player.stop()
                        qbe_gif_buffer.close()
                        wiki_gif_player.stop()
                        wiki_gif_buffer.close()

                        QApplication.setOverrideCursor(Qt.WaitCursor)
                        if result == QDialog.Rejected:
                            mismatch_ct += 1
                        else:
                            should_upload_gif = True

                if should_upload_image:
                    # upload or replace the extra image(s) on the wiki
                    result = upload_wiki_image(tile.get_big_bytesio(), meta.filename,
                                               self.gameroot.gamever, tile.filename)
                    if result.get('result', None) == 'Success':
                        success_ct += 1
                    else:
                        fail_ct += 1

                if should_upload_gif:
                    result = upload_wiki_image(GifHelper.get_bytesio(qbe_gif), meta.gif_filename,
                                               self.gameroot.gamever)
                    if result.get('result', None) == 'Success':
                        success_ct += 1
                    else:
                        fail_ct += 1

            # restore statusbar message
            self.statusbar.showMessage(statusbar_current)

        self.set_icon(extraimages_exist_cell_index, '✅')
        if success_ct > 0 and fail_ct == 0 and mismatch_ct == 0:
            self.set_icon(extraimages_match_cell_index, '✅', True)
        else:
            self.set_icon(extraimages_match_cell_index, '❌', True)

    def save_selected_tile(self):
        """Save the currently displayed tile as a PNG or GIF to the local filesystem."""
        if self.gif_mode:
            if self.objTreeView.top_selected_item.gif_image(0) is not None:
                filename = QFileDialog.getSaveFileName()[0]
                GifHelper.save(self.objTreeView.top_selected_item.gif_image(0), filename)
        elif self.objTreeView.top_selected_item.tile is not None:
            filename = QFileDialog.getSaveFileName()[0]
            self.objTreeView.top_selected_item.tile.get_big_image().save(filename, format='png')

    def swap_tile_mode(self):
        """Swap between the .png and .gif preview"""
        self.gif_mode = not self.gif_mode
        self.update_tile_display()

    def check_template_match(self, new: str, current: str) -> bool:
        """Checks if the new template text and the wiki's current template text match. Ignores the
        'gameversion' line in the template - otherwise every single page is marked as not matching
        whenever there's a new update, which makes the 'Article Matches?' column kind of useless."""
        new = re.sub(r'^\| gameversion = .*?$', '', new, flags=re.MULTILINE)
        current = re.sub(r'^\| gameversion = .*?$', '', current, flags=re.MULTILINE)
        return new in current

    def show_simple_diff(self):
        """Display a popup showing the diff between our template and the version on the wiki."""
        qud_object = self.objTreeView.top_selected_item
        if qud_object is None or not qud_object.is_wiki_eligible():
            return
        article_exists_index = self.objTreeView.top_selected_item_index + 3
        article_matches_index = self.objTreeView.top_selected_item_index + 4
        article = WikiPage(qud_object, self.gameroot.gamever)
        if not article.page.exists:
            self.set_icon(article_exists_index, '❌', True)
            return
        self.set_icon(article_exists_index, '✅')
        txt = qud_object.wiki_template(self.gameroot.gamever).strip()
        wiki_txt = article.page.text().strip()
        # Capture TEMPLATE_RE from wiki page, but ignore things outside the template.
        template_re = '(?:.*?)' + TEMPLATE_RE + '(?:.*)'
        template_re_old = '(?:.*?)' + TEMPLATE_RE_OLD + '(?:.*)'
        wiki_pattern = re.compile(template_re, re.MULTILINE | re.DOTALL)
        basic_pattern = re.compile(template_re_old, re.MULTILINE | re.DOTALL)
        msg_box = QMessageBox()
        msg_box.setTextFormat(Qt.RichText)
        if txt in wiki_txt:
            msg_box.setText("No template differences detected.")
            match_icon = '✅'
        else:
            m = basic_pattern.match(txt)
            m_wiki = wiki_pattern.match(wiki_txt)
            if m is None:
                msg_box.setText('Unable to compare because the QBE template'
                                ' is not formatted as expected.')
                match_icon = '-'
            elif m_wiki is None:
                # fallback to old logic (doesn't require START QBE and END QBE tags)
                m_wiki = basic_pattern.match(wiki_txt)
                if m_wiki is None:
                    msg_box.setText('Unable to compare because the wiki template'
                                    ' is not formatted as expected.')
                    match_icon = '-'
            if None not in [m, m_wiki]:
                lines = m.group(1).splitlines()
                wiki_lines = m_wiki.group(1).splitlines()
                diff_lines = ''
                for line in difflib.unified_diff(wiki_lines, lines, "wiki", "QBE", lineterm=""):
                    diff_lines += '\n' + line
                msg_box.setText(f'Unified diff of the QBE template and the currently published'
                                f' wiki template:\n<pre>{diff_lines}</pre>')
                match_icon = '❌'
                if self.check_template_match(m.group(1), m_wiki.group(1)):
                    match_icon = '✅'  # only difference is gameversion
        self.set_icon(article_matches_index, match_icon, True)
        msg_box.exec()

    def setview(self, view: str):
        """Process a request to set the view type and update the checkmarks in the View menu.

        Parameters: view: one of 'wiki', 'attr', 'all_attr', 'xml_source'"""
        if self.obj_view_type == view:
            return
        actions = {'wiki': self.actionWiki_template,
                   'attr': self.actionAttributes,
                   'all_attr': self.actionAll_attributes,
                   'xml_source': self.actionXML_source,
                   }
        self.obj_view_type = view
        for action in actions.values():
            action.setChecked(False)
        actions[view].setChecked(True)
        selected = self.objTreeView.selectedIndexes()
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

    def apply_theme(self):
        self.toggle_qudmode(use_current_setting=True)

    def toggle_qudmode(self, use_current_setting: bool = False):
        """Toggles qud mode (dark theme). This preference is saved to userconfig.yml."""
        try:
            with open('userconfig.yml', 'r') as f:
                user_settings = yaml.safe_load(f)
        except FileNotFoundError:
            user_settings = dict()
        try:
            qudmode_active = user_settings['dark mode']
        except KeyError:
            qudmode_active = False

        if qudmode_active == use_current_setting:
            try:
                with open("helpers/stylesheets/ManjaroMix.qss", "r") as f:
                    _style = f.read()
                    self.app.setStyleSheet(_style)
                qudmode_active = True
            except FileNotFoundError:
                print('Error: unable to load style sheet for qud mode theme.')
        else:
            self.app.setStyleSheet('')
            qudmode_active = False
        user_settings['dark mode'] = qudmode_active
        with open('userconfig.yml', 'w') as f:
            yaml.safe_dump(user_settings, f)

    def show_help(self):
        """Show help info. Currently just shows info about search macros."""
        msg_box = QMessageBox()
        msg_box.setText('<b>Search shortcuts</b>'
                        '\n<pre> </pre>'
                        '\n<pre>hasfield:&lt;fieldname&gt;</pre>'
                        '\n<pre>hasfield:&lt;fieldname&gt;=&lt;value&gt;</pre>'
                        '\nshows only objects that have the specified wiki field (optionally '
                        'limited to &lt;value&gt;)'
                        '\n<pre> </pre>'
                        '\n<pre>haspart:&lt;PartName&gt;</pre>'
                        '\nshows only objects that have a specific part (case sensitive)'
                        '\n<pre> </pre>'
                        '\n<pre>hastag:&lt;TagName&gt;</pre>'
                        '\nshows only objects that have a specific tag (case sensitive)'
                        '\n<pre> </pre>')
        msg_box.exec()

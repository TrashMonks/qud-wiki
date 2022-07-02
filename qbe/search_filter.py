"""Search filters for the QBE application window."""

from PySide6.QtCore import QSortFilterProxyModel, Qt, QRegularExpression, QItemSelectionModel
from PySide6.QtWidgets import QLineEdit
from qbe.tree_view import QudTreeView


class QudFilterModel(QSortFilterProxyModel):
    """Custom QBE filter proxy for the object or population tree view."""
    def __init__(self, parent=None):
        super(QudFilterModel, self).__init__(parent)
        self.setRecursiveFilteringEnabled = True
        self.setFilterKeyColumn(0)
        self.filterSelections = []
        self.filterSelectionIDs = []
        # use of separate itemIDs list is a workaround for issue bugreports.qt.io/browse/PYSIDE-74,
        # which causes errors when using the 'in' operator on the filterSelections list's QItems

    def pop_selections(self):
        """Wipe the list of filtered items and return what they previously were."""
        val1 = self.filterSelections
        val2 = self.filterSelectionIDs
        self.filterSelections = []
        self.filterSelectionIDs = []
        return val1, val2

    def _accept_index(self, idx) -> bool:
        """Perform recursive search on an index.

        Causes ancestors of matching objects to be displayed as an inheritance tree, even if the
        ancestors themselves don't match the filter."""
        if idx.isValid():
            filter_str = self.filterRegularExpression().pattern().lower()
            text = idx.data(role=Qt.DisplayRole).lower()
            # use QRegularExpression method?
            found = text.find(filter_str) >= 0
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
        """Overrides filterAcceptsRow to determine if the row should be included.

        Documentation of overridden class:
        Returns true if the item in the row indicated by the given source_row and source_parent
        should be included in the model; otherwise returns false.

        The default implementation returns true if the value held by the relevant item matches the
        filter string, wildcard string or regular expression."""
        idx = self.sourceModel().index(source_row, 0, source_parent)  # 0 = first column
        return self._accept_index(idx)


class QudObjFilterModel(QudFilterModel):
    """Custom filter proxy for the object tree view."""

    def _accept_index(self, idx) -> bool:
        """Override function includes special handling for object search modifiers like 'hasfield:'
        and 'haspart:'"""
        if idx.isValid():
            filter_str = self.filterRegularExpression().pattern().lower()
            if filter_str.startswith('hasfield:'):
                found = self._index_hasfield(idx, filter_str.split(':')[1])
            elif filter_str.startswith('haspart:'):
                found = self._index_haspart(idx,
                                            self.filterRegularExpression().pattern().split(':')[1])
            elif filter_str.startswith('hastag:'):
                found = self._index_hastag(idx,
                                           self.filterRegularExpression().pattern().split(':')[1])
            else:
                text = idx.data(role=Qt.DisplayRole).lower()
                # use QRegularExpression method?
                found = text.find(self.filterRegularExpression().pattern().lower()) >= 0
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

    def _index_hasfield(self, idx, field: str) -> bool:
        """Perform 'hasfield:' search; match only objects with the specified wiki template field"""
        target_val = None
        if len(field.split('=')) == 2:
            target_val = field.split('=')[1]
            field = field.split('=')[0]
        qud_object = self.sourceModel().itemFromIndex(idx).data()
        object_val = getattr(qud_object, field)
        if object_val is not None:
            if qud_object.is_wiki_eligible():
                return target_val is None or target_val == str(object_val)
        return False

    def _index_haspart(self, idx, part: str) -> bool:
        """Perform 'haspart:' search; match only objects with the specified part (case sensitive)"""
        qud_object = self.sourceModel().itemFromIndex(idx).data()
        if getattr(qud_object, f'part_{part}') is not None:
            if qud_object.is_wiki_eligible():
                return True
        return False

    def _index_hastag(self, idx, tag: str) -> bool:
        """Perform 'hastag:' search; match only objects with the specified tag (case sensitive)"""
        qud_object = self.sourceModel().itemFromIndex(idx).data()
        if getattr(qud_object, f'tag_{tag}') is not None:
            if qud_object.is_wiki_eligible():
                return True
        return False


class QudPopFilterModel(QudFilterModel):
    """Custom filter proxy for the population tree view."""


class QudSearchBehaviorHandler:
    def __init__(self, search_edit: QLineEdit, proxy: QudFilterModel, tree_view: QudTreeView):
        """Handles searching behavior for a search text box associated with a tree view.

        Args:
            search_edit: The search edit bar widget
            proxy: The proxy filter for the tree view
            tree_view: The tree view associated with the search edit bar
        """
        self.search_edit = search_edit
        self.proxy_filter = proxy
        self.tree_view = tree_view

    @property
    def source_model(self):
        """The underlying source model for the tree view and its proxy filter model."""
        return self.proxy_filter.sourceModel()

    def search_changed(self, mode: str = ''):
        """Called when the text in the search box has changed.

        By default, the search box only begins filtering after 4 or more letters are entered.
        However, you can override that and search with fewer letters by hitting ENTER ('Forced'
        mode). You can also hit ENTER to move to the next match for an existing/active search
        query."""
        if len(self.search_edit.text()) <= 3:
            self.clear_search_filter(False)
        if len(self.search_edit.text()) > 3 \
                or (mode == 'Forced' and self.search_edit.text() != ''):
            self.proxy_filter.pop_selections()  # clear any lingering data in proxyfilter
            self.proxy_filter.setFilterRegularExpression(  # apply the actual filtering
                QRegularExpression(self.search_edit.text()))
            self.tree_view.expandAll()  # expands to show everything visible after filter applied
            items, item_ids = self.proxy_filter.pop_selections()
            if len(items) > 0:
                item = items[0]
                if mode == 'Forced':  # go to next filtered item each time the user presses ENTER
                    self.tree_view.items_selected = self.tree_view.selectedIndexes()
                    if self.tree_view.items_selected is not None \
                            and self.tree_view.selected_row_count() == 1:
                        currentitem = self.source_model.itemFromIndex(
                            self.proxy_filter.mapToSource(self.tree_view.items_selected[0]))
                        if id(currentitem) in item_ids:
                            newindex = item_ids.index(id(currentitem)) + 1
                            if newindex < len(items):
                                item = items[newindex]
                idx = self.source_model.indexFromItem(item)
                idx = self.proxy_filter.mapFromSource(idx)
                self.tree_view.selectionModel().select(
                    idx, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
                self.scroll_to_selected()

    def search_changed_forced(self):
        self.search_changed('Forced')

    def clear_search_filter(self, clearfield: bool = False):
        """Remove any filtering that has been applied to the tree view."""
        if clearfield and len(self.search_edit.text()) > 0:
            self.search_edit.clear()
        self.proxy_filter.setFilterRegularExpression('')
        self.scroll_to_selected()

    def scroll_to_selected(self):
        """Scroll the tree view to the first selected item."""
        self.tree_view.items_selected = self.tree_view.selectedIndexes()
        if self.tree_view.items_selected is not None and len(self.tree_view.items_selected) > 0:
            self.tree_view.scrollTo(self.tree_view.items_selected[0])

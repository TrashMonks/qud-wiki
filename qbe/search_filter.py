"""Search filter for the QBE application window."""

from PySide6.QtCore import QSortFilterProxyModel, Qt


class QudFilterModel(QSortFilterProxyModel):
    """Custom filter proxy for the tree view."""
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

    def filterAcceptsRow(self, source_row, source_parent):
        """Overrides filterAcceptsRow to determine if the row should be included.

        Documentation of overridden class:
        Returns true if the item in the row indicated by the given source_row and source_parent
        should be included in the model; otherwise returns false.

        The default implementation returns true if the value held by the relevant item matches the
        filter string, wildcard string or regular expression."""
        idx = self.sourceModel().index(source_row, 0, source_parent)  # 0 = first column
        return self._accept_index(idx)

"""Search filter for the QBE application window."""

from PySide2.QtCore import QSortFilterProxyModel, Qt


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

    def _accept_index(self, idx):
        """Perform recursive search on an index.

        Causes ancestors of matching objects to be displayed as an inheritance tree, even if the
        ancestors themselves don't match the filter."""
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
        """Overrides filterAcceptsRow to determine if the row should be included.

        Documentation of overridden class:
        Returns true if the item in the row indicated by the given source_row and source_parent
        should be included in the model; otherwise returns false.

        The default implementation returns true if the value held by the relevant item matches the
        filter string, wildcard string or regular expression."""
        idx = self.sourceModel().index(source_row, 0, source_parent)  # 0 = first column
        return self._accept_index(idx)

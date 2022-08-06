from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QTreeView, QSizePolicy, QAbstractItemView, QMenu


class QudTreeView(QTreeView):
    def __init__(self, selection_handler, header_labels, *args, **kwargs):
        """Custom tree view for QBE object and population hierarchy browsers.

        Args:
            selection_handler: a function in the parent window to pass selected indices to
            header_labels: the tree view header row labels above each column
        """
        self.selection_handler = selection_handler
        super().__init__(*args, **kwargs)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(size_policy)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setIndentation(10)
        self.header_labels = header_labels
        self.items_selected = []
        # used if we only want one of potential multiple items:
        self.top_selected_item = None
        self.top_selected_item_index = None

    def selected_row_count(self):
        """Returns the number of currently selected rows in the tree."""
        if self.items_selected is not None:
            return len(self.items_selected) // len(self.header_labels)

    def selectionChanged(self, selected, deselected):
        """Custom override to handle all forms of selection (keyboard, mouse)"""
        indices = self.selectedIndexes()
        self.selection_handler(indices)
        super().selectionChanged(selected, deselected)


class QudObjTreeView(QudTreeView):
    def __init__(self, selection_handler, header_labels, *args, **kwargs):
        """Custom tree view for QBE object hierarchy browser, including icons.

        Args:
            selection_handler: a function in the parent window to pass selected indices to
            header_labels: the tree view header row labels above each column
        """
        super().__init__(selection_handler, header_labels, *args, **kwargs)
        self.setObjectName("objTreeView")
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
        self.context_action_upload_extra = QAction('Upload extra image(s) for selected objects',
                                                   self.tree_menu)
        self.tree_menu.addAction(self.context_action_upload_extra)
        self.context_action_diff = QAction('Diff template against wiki', self.tree_menu)
        self.tree_menu.addAction(self.context_action_diff)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def on_context_menu(self, point):
        """Callback registered for right click in the tree view."""
        self.tree_menu.exec(self.mapToGlobal(point))


class QudPopTreeView(QudTreeView):
    def __init__(self, selection_handler, header_labels, *args, **kwargs):
        """Custom tree view for QBE population hierarchy browser.

        Args:
            selection_handler: a function in the parent window to pass selected indices to
            header_labels: the tree view header row labels above each column
        """
        super().__init__(selection_handler, header_labels, *args, **kwargs)
        self.setObjectName("popTreeView")

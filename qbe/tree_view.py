from PySide2.QtCore import QSize, Qt
from PySide2.QtWidgets import QTreeView, QSizePolicy, QAbstractItemView, QMenu, QAction


class QudTreeView(QTreeView):
    """Custom tree view for the object hierarchy browser, including icons."""
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
        self.context_action_upload_extra = QAction('Upload extra image(s) for selected objects',
                                                   self.tree_menu)
        self.tree_menu.addAction(self.context_action_upload_extra)
        self.context_action_diff = QAction('Diff template against wiki', self.tree_menu)
        self.tree_menu.addAction(self.context_action_diff)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def on_context_menu(self, point):
        """Callback registered for right click in the tree view."""
        self.tree_menu.exec_(self.mapToGlobal(point))

    def selectionChanged(self, selected, deselected):
        """Custom override to handle all forms of selection (keyboard, mouse)"""
        indices = self.selectedIndexes()
        self.selection_handler(indices)
        super().selectionChanged(selected, deselected)

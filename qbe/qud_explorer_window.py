# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qud_explorer_window.ui'
##
## Created by: Qt User Interface Compiler version 5.15.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1024, 768)
        self.actionOpen_ObjectBlueprints_xml = QAction(MainWindow)
        self.actionOpen_ObjectBlueprints_xml.setObjectName(u"actionOpen_ObjectBlueprints_xml")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionWiki_template = QAction(MainWindow)
        self.actionWiki_template.setObjectName(u"actionWiki_template")
        self.actionWiki_template.setCheckable(True)
        self.actionWiki_template.setChecked(True)
        self.actionAttributes = QAction(MainWindow)
        self.actionAttributes.setObjectName(u"actionAttributes")
        self.actionAttributes.setCheckable(True)
        self.actionAll_attributes = QAction(MainWindow)
        self.actionAll_attributes.setObjectName(u"actionAll_attributes")
        self.actionAll_attributes.setCheckable(True)
        self.actionScan_wiki = QAction(MainWindow)
        self.actionScan_wiki.setObjectName(u"actionScan_wiki")
        self.actionUpload_templates = QAction(MainWindow)
        self.actionUpload_templates.setObjectName(u"actionUpload_templates")
        self.actionUpload_tiles = QAction(MainWindow)
        self.actionUpload_tiles.setObjectName(u"actionUpload_tiles")
        self.actionXML_source = QAction(MainWindow)
        self.actionXML_source.setObjectName(u"actionXML_source")
        self.actionXML_source.setCheckable(True)
        self.actionShow_help = QAction(MainWindow)
        self.actionShow_help.setObjectName(u"actionShow_help")
        self.actionUpload_extra_image_s_for_selected_objects = QAction(MainWindow)
        self.actionUpload_extra_image_s_for_selected_objects.setObjectName(u"actionUpload_extra_image_s_for_selected_objects")
        self.actionDiff_template_against_wiki = QAction(MainWindow)
        self.actionDiff_template_against_wiki.setObjectName(u"actionDiff_template_against_wiki")
        self.actionDark_mode = QAction(MainWindow)
        self.actionDark_mode.setObjectName(u"actionDark_mode")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.plainTextEdit = QPlainTextEdit(self.centralwidget)
        self.plainTextEdit.setObjectName(u"plainTextEdit")
        font = QFont()
        font.setFamily(u"Consolas")
        font.setPointSize(10)
        self.plainTextEdit.setFont(font)
        self.plainTextEdit.setUndoRedoEnabled(False)
        self.plainTextEdit.setReadOnly(True)

        self.horizontalLayout.addWidget(self.plainTextEdit)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.tile_label = QLabel(self.centralwidget)
        self.tile_label.setObjectName(u"tile_label")
        self.tile_label.setMinimumSize(QSize(160, 240))
        font1 = QFont()
        font1.setFamily(u"Segoe UI")
        self.tile_label.setFont(font1)
        self.tile_label.setStyleSheet(u"background-color: rgb(15, 59, 58);")

        self.verticalLayout_4.addWidget(self.tile_label)

        self.save_tile_button = QPushButton(self.centralwidget)
        self.save_tile_button.setObjectName(u"save_tile_button")
        font2 = QFont()
        font2.setFamily(u"Segoe UI")
        font2.setPointSize(10)
        self.save_tile_button.setFont(font2)

        self.verticalLayout_4.addWidget(self.save_tile_button)

        self.swap_tile_button = QPushButton(self.centralwidget)
        self.swap_tile_button.setObjectName(u"swap_tile_button")
        self.swap_tile_button.setEnabled(True)
        self.swap_tile_button.setFont(font2)

        self.verticalLayout_4.addWidget(self.swap_tile_button)


        self.horizontalLayout.addLayout(self.verticalLayout_4)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.search_label = QLabel(self.centralwidget)
        self.search_label.setObjectName(u"search_label")
        self.search_label.setMinimumSize(QSize(0, 0))
        self.search_label.setFont(font2)

        self.horizontalLayout_2.addWidget(self.search_label)

        self.search_line_edit = QLineEdit(self.centralwidget)
        self.search_line_edit.setObjectName(u"search_line_edit")
        self.search_line_edit.setFont(font2)

        self.horizontalLayout_2.addWidget(self.search_line_edit)

        self.expand_all_button = QPushButton(self.centralwidget)
        self.expand_all_button.setObjectName(u"expand_all_button")
        self.expand_all_button.setMinimumSize(QSize(90, 0))
        self.expand_all_button.setFont(font2)

        self.horizontalLayout_2.addWidget(self.expand_all_button)

        self.collapse_all_button = QPushButton(self.centralwidget)
        self.collapse_all_button.setObjectName(u"collapse_all_button")
        self.collapse_all_button.setMinimumSize(QSize(90, 0))
        self.collapse_all_button.setFont(font2)

        self.horizontalLayout_2.addWidget(self.collapse_all_button)

        self.restore_all_button = QPushButton(self.centralwidget)
        self.restore_all_button.setObjectName(u"restore_all_button")
        self.restore_all_button.setMinimumSize(QSize(130, 0))
        self.restore_all_button.setFont(font2)

        self.horizontalLayout_2.addWidget(self.restore_all_button)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.tree_target_widget = QWidget(self.centralwidget)
        self.tree_target_widget.setObjectName(u"tree_target_widget")
        self.tree_target_widget.setFont(font1)

        self.verticalLayout_3.addWidget(self.tree_target_widget, 0, Qt.AlignBottom)


        self.verticalLayout.addLayout(self.verticalLayout_3)


        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1024, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        self.menuWiki = QMenu(self.menubar)
        self.menuWiki.setObjectName(u"menuWiki")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuWiki.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionOpen_ObjectBlueprints_xml)
        self.menuFile.addAction(self.actionExit)
        self.menuView.addAction(self.actionWiki_template)
        self.menuView.addAction(self.actionAttributes)
        self.menuView.addAction(self.actionAll_attributes)
        self.menuView.addAction(self.actionXML_source)
        self.menuView.addSeparator()
        self.menuView.addAction(self.actionDark_mode)
        self.menuWiki.addAction(self.actionScan_wiki)
        self.menuWiki.addAction(self.actionDiff_template_against_wiki)
        self.menuWiki.addAction(self.actionUpload_templates)
        self.menuWiki.addAction(self.actionUpload_tiles)
        self.menuWiki.addAction(self.actionUpload_extra_image_s_for_selected_objects)
        self.menuHelp.addAction(self.actionShow_help)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Qud Blueprint Explorer", None))
        self.actionOpen_ObjectBlueprints_xml.setText(QCoreApplication.translate("MainWindow", u"Open ObjectBlueprints.xml...", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionWiki_template.setText(QCoreApplication.translate("MainWindow", u"Wiki template", None))
        self.actionAttributes.setText(QCoreApplication.translate("MainWindow", u"Attributes", None))
        self.actionAll_attributes.setText(QCoreApplication.translate("MainWindow", u"All attributes", None))
        self.actionScan_wiki.setText(QCoreApplication.translate("MainWindow", u"Scan wiki for selected objects", None))
        self.actionUpload_templates.setText(QCoreApplication.translate("MainWindow", u"Upload templates for selected objects", None))
        self.actionUpload_tiles.setText(QCoreApplication.translate("MainWindow", u"Upload tiles for selected objects", None))
        self.actionXML_source.setText(QCoreApplication.translate("MainWindow", u"XML source", None))
        self.actionShow_help.setText(QCoreApplication.translate("MainWindow", u"Show help", None))
        self.actionUpload_extra_image_s_for_selected_objects.setText(QCoreApplication.translate("MainWindow", u"Upload extra image(s) for selected objects", None))
        self.actionDiff_template_against_wiki.setText(QCoreApplication.translate("MainWindow", u"Diff template against wiki", None))
        self.actionDark_mode.setText(QCoreApplication.translate("MainWindow", u"Toggle dark mode", None))
        self.tile_label.setText("")
        self.save_tile_button.setText(QCoreApplication.translate("MainWindow", u"Save tile...", None))
        self.swap_tile_button.setText(QCoreApplication.translate("MainWindow", u"Toggle .png/.gif", None))
        self.search_label.setText(QCoreApplication.translate("MainWindow", u"Search:", None))
        self.expand_all_button.setText(QCoreApplication.translate("MainWindow", u"Expand all", None))
        self.collapse_all_button.setText(QCoreApplication.translate("MainWindow", u"Collapse all", None))
        self.restore_all_button.setText(QCoreApplication.translate("MainWindow", u"Default expansion", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"View type", None))
        self.menuWiki.setTitle(QCoreApplication.translate("MainWindow", u"Wiki", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
    # retranslateUi


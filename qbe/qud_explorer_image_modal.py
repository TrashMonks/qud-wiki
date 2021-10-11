# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qud_explorer_image_modal.ui'
##
## Created by: Qt User Interface Compiler version 5.15.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class Ui_WikiImageUpload(object):
    def setupUi(self, WikiImageUpload):
        if not WikiImageUpload.objectName():
            WikiImageUpload.setObjectName(u"WikiImageUpload")
        WikiImageUpload.resize(631, 477)
        self.buttonBox = QDialogButtonBox(WikiImageUpload)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(50, 410, 531, 51))
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        font = QFont()
        font.setFamily(u"Segoe UI")
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.buttonBox.setFont(font)
        self.buttonBox.setLayoutDirection(Qt.LeftToRight)
        self.buttonBox.setAutoFillBackground(False)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.verticalLayoutWidget = QWidget(WikiImageUpload)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(90, 70, 200, 280))
        self.verticalLayout_1 = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_1.setObjectName(u"verticalLayout_1")
        self.verticalLayout_1.setContentsMargins(10, 10, 10, 10)
        self.comparison_tile_1 = QLabel(self.verticalLayoutWidget)
        self.comparison_tile_1.setObjectName(u"comparison_tile_1")
        self.comparison_tile_1.setMinimumSize(QSize(180, 260))
        self.comparison_tile_1.setMaximumSize(QSize(180, 260))
        self.comparison_tile_1.setStyleSheet(u"background-color: rgb(15, 59, 58);")
        self.comparison_tile_1.setAlignment(Qt.AlignCenter)

        self.verticalLayout_1.addWidget(self.comparison_tile_1)

        self.verticalLayoutWidget_2 = QWidget(WikiImageUpload)
        self.verticalLayoutWidget_2.setObjectName(u"verticalLayoutWidget_2")
        self.verticalLayoutWidget_2.setGeometry(QRect(340, 70, 200, 280))
        self.verticalLayout_2 = QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(10, 10, 10, 10)
        self.comparison_tile_2 = QLabel(self.verticalLayoutWidget_2)
        self.comparison_tile_2.setObjectName(u"comparison_tile_2")
        self.comparison_tile_2.setMinimumSize(QSize(180, 260))
        self.comparison_tile_2.setMaximumSize(QSize(180, 260))
        self.comparison_tile_2.setStyleSheet(u"background-color: rgb(15, 59, 58);")
        self.comparison_tile_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.comparison_tile_2)

        self.comparison_label_1 = QLabel(WikiImageUpload)
        self.comparison_label_1.setObjectName(u"comparison_label_1")
        self.comparison_label_1.setGeometry(QRect(90, 20, 201, 51))
        font1 = QFont()
        font1.setFamily(u"Segoe UI")
        font1.setPointSize(15)
        self.comparison_label_1.setFont(font1)
        self.comparison_label_1.setAlignment(Qt.AlignCenter)
        self.comparison_label_2 = QLabel(WikiImageUpload)
        self.comparison_label_2.setObjectName(u"comparison_label_2")
        self.comparison_label_2.setGeometry(QRect(341, 20, 201, 51))
        self.comparison_label_2.setFont(font1)
        self.comparison_label_2.setAlignment(Qt.AlignCenter)
        self.comparison_label_3 = QLabel(WikiImageUpload)
        self.comparison_label_3.setObjectName(u"comparison_label_3")
        self.comparison_label_3.setGeometry(QRect(50, 360, 531, 41))
        font2 = QFont()
        font2.setFamily(u"Segoe UI")
        font2.setPointSize(14)
        self.comparison_label_3.setFont(font2)
        self.comparison_label_3.setAlignment(Qt.AlignCenter)

        self.retranslateUi(WikiImageUpload)
        self.buttonBox.accepted.connect(WikiImageUpload.accept)
        self.buttonBox.rejected.connect(WikiImageUpload.reject)

        QMetaObject.connectSlotsByName(WikiImageUpload)
    # setupUi

    def retranslateUi(self, WikiImageUpload):
        WikiImageUpload.setWindowTitle(QCoreApplication.translate("WikiImageUpload", u"Wiki Image Upload", None))
        self.comparison_tile_1.setText("")
        self.comparison_tile_2.setText("")
        self.comparison_label_1.setText(QCoreApplication.translate("WikiImageUpload", u"New Image", None))
        self.comparison_label_2.setText(QCoreApplication.translate("WikiImageUpload", u"Current Wiki Image", None))
        self.comparison_label_3.setText(QCoreApplication.translate("WikiImageUpload", u"Are you sure you want to overwrite the existing wiki image?", None))
    # retranslateUi


# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/root/autodane/source/addhost.ui'
#
# Created: Wed Sep 30 22:28:03 2015
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(402, 78)
        self.formLayout = QtGui.QFormLayout(Dialog)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.splitter_2 = QtGui.QSplitter(Dialog)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_2.setObjectName(_fromUtf8("splitter_2"))
        self.label = QtGui.QLabel(self.splitter_2)
        self.label.setObjectName(_fromUtf8("label"))
        self.txtHost = QtGui.QLineEdit(self.splitter_2)
        self.txtHost.setObjectName(_fromUtf8("txtHost"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.SpanningRole, self.splitter_2)
        self.splitter = QtGui.QSplitter(Dialog)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.btnOK = QtGui.QPushButton(self.splitter)
        self.btnOK.setObjectName(_fromUtf8("btnOK"))
        self.btnCancel = QtGui.QPushButton(self.splitter)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.splitter)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Add Host", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "  IP Address", None, QtGui.QApplication.UnicodeUTF8))
        self.btnOK.setText(QtGui.QApplication.translate("Dialog", "OK", None, QtGui.QApplication.UnicodeUTF8))
        self.btnCancel.setText(QtGui.QApplication.translate("Dialog", "Cancel", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Dialog = QtGui.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())


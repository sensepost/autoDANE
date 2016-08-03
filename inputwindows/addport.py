# -*- coding: utf-8 -*-

from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import QDialog

from .Ui_addport import Ui_Dialog


class AddPort(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
    
    @pyqtSignature("")
    def on_btnOK_clicked(self):
        self.accept()
    
    @pyqtSignature("")
    def on_btnCancel_clicked(self):
        self.reject()

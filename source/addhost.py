# -*- coding: utf-8 -*-

from PyQt4.QtGui import QDialog,  QMessageBox
from PyQt4.QtCore import pyqtSignature

from Ui_addhost import Ui_Dialog

import footprintfunctions

class addhost(QDialog, Ui_Dialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
    def getResult(self):
        return self.txtHost.text()
    
    @pyqtSignature("")
    def on_btnCancel_clicked(self):
        self.reject()
    
    @pyqtSignature("")
    def on_btnOK_clicked(self):
        if footprintfunctions.isInternalIP(self.txtHost.text()):
            self.accept()
        else:
            QMessageBox.information(self, "Information", "You need to enter an IP")

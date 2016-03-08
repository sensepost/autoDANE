from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import QDialog, QMessageBox

from .Ui_adddomaincreds import Ui_Dialog

class wndAddDomainCreds(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
    
    @pyqtSignature("")
    def on_btnOK_clicked(self):
        if self.txtDomain.text() != "" and self.txtUsername.text():
            self.accept()
        else:
            QMessageBox.information(self, "Information", "You need to provide at least a domain and username")
    
    @pyqtSignature("")
    def on_btnCancel_clicked(self):
        self.reject()

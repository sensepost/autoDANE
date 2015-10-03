from PyQt4.QtGui import QDialog,  QMessageBox
from PyQt4.QtCore import pyqtSignature

from Ui_adddomaincreds import Ui_dialog

class AddDomainCredsDialog(QDialog, Ui_dialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

    def getResult(self):
        return [ self.txtDomainName.text(),  self.txtUsername.text(), self.txtPassword.text() ]

    @pyqtSignature("")
    def on_btnOk_clicked(self):
        if self.txtDomainName.text() != "" and self.txtUsername.text() != "" and self.txtPassword.text() != "":
            self.accept()
        else:
            QMessageBox.information(self, "Information", "You need to fill in all three fields")
    
    @pyqtSignature("")
    def on_btnCancel_clicked(self):
        self.reject()

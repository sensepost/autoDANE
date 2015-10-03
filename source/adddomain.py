from PyQt4.QtGui import QDialog,  QMessageBox
from PyQt4.QtCore import pyqtSignature

from Ui_adddomain import Ui_Dialog

class AddDomainDialog(QDialog, Ui_Dialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
    def getResult(self):
        return self.txtDomain.text()
    
    @pyqtSignature("")
    def on_btnOk_clicked(self):
        if self.txtDomain.text() != "":
            self.accept()
        else:
            QMessageBox.information(self, "Information", "You need to enter a domain")
    
    @pyqtSignature("")
    def on_btnCancel_clicked(self):
        self.reject()

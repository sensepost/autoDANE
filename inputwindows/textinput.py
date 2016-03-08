from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import QDialog, QMessageBox

from .Ui_textinput import Ui_Dialog


class wndTextInput(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
    
    @pyqtSignature("")
    def on_btnOk_clicked(self):
        if self.txtDomain.text() == "" or self.txtLootFileName.text() == "":
            QMessageBox.information(self, "Information", "You need to fill in both fields")
        else:
            self.accept()
    
    @pyqtSignature("")
    def on_btnCancel_clicked(self):
        self.reject()

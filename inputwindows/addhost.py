from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import QDialog, QMessageBox

from .Ui_addhost import Ui_Dialog

class wndAddHost(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
 
    def valid(self):
        res = False
        try:
            octs = str(self.txtIPAddress.text()).split(".")
            if 4 == len(octs):
                if int(octs[0]) + int(octs[1]) + int(octs[2]) + int(octs[3]) < (255 * 4):
                    res = True
        except:
            res = False
            
        return res
        
    @pyqtSignature("")
    def on_btnOK_clicked(self):
        if self.valid() == True:
            self.accept()
        else:
            QMessageBox.information(self, "Information", "That's not a valid IP")
    
    @pyqtSignature("")
    def on_btnCancel_clicked(self):
        self.reject()

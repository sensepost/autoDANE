from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import QDialog
from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import QString

from .Ui_confirmation import Ui_Dialog


class wndConfirmation(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        logoPixmap = QtGui.QPixmap(QString.fromUtf8('images/confirm.png'))
        logoScaledPixmap = logoPixmap.scaled(self.lblImage.size(),  QtCore.Qt.KeepAspectRatio)
        self.lblImage.setPixmap(logoScaledPixmap)
    
    @pyqtSignature("")
    def on_btnYes_clicked(self):
        self.accept()
    
    @pyqtSignature("")
    def on_btnNo_clicked(self):
        self.reject()

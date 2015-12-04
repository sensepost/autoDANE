from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import pyqtSignature, pyqtSignal
from PyQt4.QtGui import *


from PyQt4.QtCore import QString
#from PyQt4.QtGui import QApplication

import ConfigParser
import threading
import MySQLdb
from MySQLdb import OperationalError
import time

from .Ui_dbconnecting import Ui_Dialog

class DBConnecting(QDialog, Ui_Dialog):
    tickLabelTimerTrigger = pyqtSignal()
    tickLabelTimer = None
    currentDotsVal = ""
    connectedToDB = False
    errorMessage = ""
    conf = ConfigParser.ConfigParser()
    
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.conf.read("settings.ini")
        self.tickLabelTimerTrigger.connect(self.handletickLabelTimerTrigger)
        self.tickLabelTimer = threading.Timer(0.5, self.calltickLabelTimerTrigger)
        self.tickLabelTimer.start()
        
        logoPixmap = QtGui.QPixmap(QString.fromUtf8('images/db-connection.jpg'))
        logoScaledPixmap = logoPixmap.scaled(self.lblDBLogo.size(),  QtCore.Qt.KeepAspectRatio)
        self.lblDBLogo.setPixmap(logoScaledPixmap)

    def calltickLabelTimerTrigger(self):
        try:
            MySQLdb.connect(host=self.conf.get('MySQL',  'host'), user=self.conf.get('MySQL',  'user'), passwd=self.conf.get('MySQL',  'pass'), db=self.conf.get('MySQL',  'db'))
            self.connectedToDB = True
        except OperationalError as e:
            self.errorMessage = e[1]
            time.sleep(1)
        except Exception as e:
            self.errorMessage = e.strerror
            time.sleep(1)

        self.tickLabelTimerTrigger.emit()

    def handletickLabelTimerTrigger(self):
        if (self.connectedToDB):
            self.accept()
        else:
            threading.Timer(0.5, self.calltickLabelTimerTrigger).start()
            self.currentDotsVal += "."
            if self.currentDotsVal == "....":
                self.currentDotsVal = ""

            self.label.setText("Connecting " + self.currentDotsVal)
            self.lblError.setText(self.errorMessage)
            
    @pyqtSignature("")
    def on_btnCancel_clicked(self):
        self.reject()

from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import QDialog, QMessageBox

from .Ui_newtask import Ui_Dialog

class NewTask(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
    
    db = None
    
    def setup(self):
        cursor = self.db.cursor()
        cursor.execute("select category from task_categories")
        items = [ "" ]
        for row in cursor.fetchall():
            items.append(row[0])
        self.cmbCategory.addItems(items)
        cursor.close()
        
    def validate(self):
        result = False

        if self.cmbCategory.currentText() != "" and self.txtName.text() != "" and self.txtDescription.toPlainText() != "" and self.txtFileName.text() != "":
            result = True
        
        return result
        
    @pyqtSignature("")
    def on_btnSave_clicked(self):
        if self.validate():
            self.accept()
        else:
            QMessageBox.information(self, "Information", "You need to fill in all the fields")
    
    @pyqtSignature("")
    def on_btnCancel_clicked(self):
        self.reject()

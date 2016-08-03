from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import QDialog, QMessageBox

from .Ui_newtrigger import Ui_Dialog


class NewTrigger(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
    db = None
    
    categories = { "":-1 }
    triggers = { "":-1 }
    def setup(self):
        self.cmbCategory.addItem("")
        cursor = self.db.cursor()
        cursor.execute ("select id, category from task_categories")
        for row in cursor.fetchall():
            self.categories[row[1]] = row[0]
            self.cmbCategory.addItem(row[1])
        cursor.close()
        
        self.cmbTriggers.addItem("")
        cursor = self.db.cursor()
        cursor.execute ("select id, trigger_name from trigger_descriptions")
        for row in cursor.fetchall():
            self.triggers[row[1]] = row[0]
            self.cmbTriggers.addItem(row[1])
        cursor.close()
        
        
    def validate(self):
        if self.cmbTriggers.currentText() != "" and self.txtValueMask.text() != "" and self.cmbCategory.currentText() != "" and self.cmbTasks.currentText() != "":
            return True
        else:
            return False
    
    @pyqtSignature("")
    def on_btnSave_clicked(self):
        if self.validate():
            cursor = self.db.cursor()
            sql = "insert into trigger_events (trigger_descriptions_id, task_descriptions_id, value_mask, enabled) values (%s, %s, %s, %s)"
            trigger_id = self.triggers[str(self.cmbTriggers.currentText())]
            task_id = self.tasks[str(self.cmbTasks.currentText())]
            cursor.execute(sql, (trigger_id, task_id, str(self.txtValueMask.text()), self.cbxEnabled.isChecked(), ))
            cursor.close()
            self.accept()
        else:
            QMessageBox.information(self, "Information", "You need to fill in all the fields")
    
    @pyqtSignature("")
    def on_btnCancel_clicked(self):
        self.reject()
    
    tasks = { "":-1 }
    @pyqtSignature("int")
    def on_cmbCategory_currentIndexChanged(self, index):
        self.tasks = { "":-1 }
        self.cmbTasks.clear()
        self.cmbTasks.addItem("")
        sql = "select id, task_name from task_descriptions where task_categories_id = %s"
        cursor = self.db.cursor()
        cursor.execute(sql, (self.categories[str(self.cmbCategory.currentText())], ))
        for row in cursor.fetchall():
            self.tasks[row[1]] = row[0]
            self.cmbTasks.addItem(row[1])

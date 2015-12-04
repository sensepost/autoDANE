from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .Ui_choosefootprint import Ui_Dialog
from inputwindows.newtask import NewTask
from inputwindows.newtrigger import NewTrigger

class ChooseFootprint(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.tblEvents.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblTasks.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblTriggers.setSelectionBehavior(QAbstractItemView.SelectRows)
        
    db = None
    
    def setFootprints(self, _footprints):
        self.cmbFootprints.addItems(_footprints)
        
    def updateUI(self):
        self.updateCmbTaskCategories()
        self.updateTblTriggers()
        self.updateCmbTriggers()
        
    
    @pyqtSignature("")
    def on_btnOK_clicked(self):
        if self.txtFootprintName.text() == "":
            QMessageBox.information(self, "Information", "You need to choose a name")
        else:
            self.accept()
    
    @pyqtSignature("")
    def on_btnCancel_clicked(self):
        self.reject()
    
    @pyqtSignature("QString")
    def on_txtFootprintName_textEdited(self, p0):
        self.cmbFootprints.setCurrentIndex(0)
        
    @pyqtSignature("QString")
    def on_cmbFootprints_currentIndexChanged(self, p0):
        if p0 != "":
            self.txtFootprintName.setText(p0)
            
    @pyqtSignature("QString")
    def on_cmbCategories_currentIndexChanged(self, p0):
        self.updateTblTasks(p0)
    
    @pyqtSignature("QString")
    def on_cmbTriggers_currentIndexChanged(self, p0):
        self.updateTblEvents(p0)
    
    def updateCmbTaskCategories(self):
        cursor = self.db.cursor()
        cursor.execute("select category from task_categories order by category")
        self.cmbCategories.addItems([""])
        for row in cursor.fetchall():
            self.cmbCategories.addItems([row[0]])
        cursor.close()
        
    def updateCmbTriggers(self):
        cursor = self.db.cursor()
        cursor.execute("select trigger_name from trigger_descriptions order by trigger_name")
        self.cmbTriggers.addItems([""])
        for row in cursor.fetchall():
            self.cmbTriggers.addItems([row[0]])
        cursor.close()
    
    tasks = []
    current_task_index = -1
    def updateTblTasks(self, category):
        i = 0
        self.tblTasks.setRowCount(0)
        self.tasks = []
        cursor = self.db.cursor()
        cursor.execute("select tc.id, tc.category, td.id, td.task_name, td.description, td.file_name, td.uses_metasploit, td.is_recursive, td.enabled from task_categories tc join task_descriptions td on tc.id = td.task_categories_id where tc.category = %s", (category))
        for row in cursor.fetchall():
            self.tasks.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6] == '\x01', row[7] == '\x01', row[8] == '\x01'])
            self.tblTasks.setRowCount(self.tblTasks.rowCount() + 1)
            self.tblTasks.setItem(i, 0, QTableWidgetItem(row[1]))
            self.tblTasks.setItem(i, 1, QTableWidgetItem(row[3]))
            i = i + 1
        cursor.close()
        self.tblTasks.resizeColumnsToContents()

    def updateTblTriggers(self):
        sql = "select trigger_name, trigger_description, (select count(*) from trigger_events where trigger_descriptions_id = td.id) as 'count' from trigger_descriptions td order by trigger_name"
        cursor = self.db.cursor()
        cursor.execute(sql)
        i = 0
        self.tblTriggers.setRowCount(0)
        for row in cursor.fetchall():
            self.tblTriggers.setRowCount(self.tblTriggers.rowCount() + 1)
            self.tblTriggers.setItem(i, 0, QTableWidgetItem(row[0]))
            self.tblTriggers.setItem(i, 1, QTableWidgetItem(row[1]))
            self.tblTriggers.setItem(i, 2, QTableWidgetItem(str(row[2])))
            i = i + 1
        cursor.close()
        self.tblTriggers.resizeColumnsToContents()
        
    events = []
    current_event_index = 0
    def updateTblEvents(self, trigger):
        sql = "select te.id, trd.trigger_name, te.value_mask, tc.category, td.task_name, te.enabled from task_categories tc join task_descriptions td on tc.id = td.task_categories_id join trigger_events te on te.task_descriptions_id = td.id join trigger_descriptions trd on trd.id = te.trigger_descriptions_id where trd.trigger_name = %s"
        cursor = self.db.cursor()
        cursor.execute(sql, (trigger))
        i = 0
        self.tblEvents.setRowCount(0)
        self.events = []
        for row in cursor.fetchall():
            self.events.append(row[0])
            self.tblEvents.setRowCount(self.tblEvents.rowCount() + 1)
            self.tblEvents.setItem(i, 0, QTableWidgetItem(row[1]))
            self.tblEvents.setItem(i, 1, QTableWidgetItem(row[2]))
            self.tblEvents.setItem(i, 2, QTableWidgetItem(str(row[3])))
            self.tblEvents.setItem(i, 3, QTableWidgetItem(str(row[4])))
            self.tblEvents.setItem(i, 4, QTableWidgetItem(str(row[5] == '\x01')))
            i = i + 1
        cursor.close()
        self.tblEvents.resizeColumnsToContents()

    @pyqtSignature("int, int")
    def on_tblTasks_cellClicked(self, row, column):
        self.current_task_index = row
        self.txtTaskName.setText(QString(self.tasks[row][3]))
        self.txtTaskDescription.setText(QString(self.tasks[row][4]))
        self.txtFileName.setText(QString(self.tasks[row][5]))
        self.cbxUsesMetasploit.setChecked(self.tasks[row][6])
        self.cbxIsRecursive.setChecked(self.tasks[row][7])
        self.cbxTaskEnabled.setChecked(self.tasks[row][8])
    
    @pyqtSignature("")
    def on_btnCreateTask_clicked(self):
        wndNewTask = NewTask()
        wndNewTask.db = self.db
        wndNewTask.setup()
        
        if wndNewTask.exec_():
            sql = "insert into task_descriptions (task_categories_id, task_name, description, file_name, uses_metasploit, is_recursive, enabled) values ((select id from task_categories where category = %s), %s, %s, %s, %s, %s, %s)"
            cursor = self.db.cursor()
            cursor.execute(sql, (wndNewTask.cmbCategory.currentText(), wndNewTask.txtName.text(), wndNewTask.txtDescription.toPlainText(), wndNewTask.txtFileName.text(), wndNewTask.cbxUsesMetasploit.isChecked(), wndNewTask.cbxIsRecursive.isChecked(), wndNewTask.cbxEnabled.isChecked()))
            cursor.close()
                
            self.updateTblTasks(str(self.cmbCategories.currentText()))
    
    @pyqtSignature("")
    def on_btnSaveTasksChanges_clicked(self):
        cursor = self.db.cursor()
        sql = "update task_descriptions set task_name = %s, description = %s, file_name = %s, uses_metasploit = %s, is_recursive = %s, enabled = %s where id = %s"
        r = self.tasks[self.current_task_index]
        cursor.execute(sql, (self.txtTaskName.text(), self.txtTaskDescription.toPlainText(), self.txtFileName.text(), self.cbxUsesMetasploit.isChecked(), self.cbxIsRecursive.isChecked(), self.cbxTaskEnabled.isChecked(), r[2]))
        cursor.close()
        self.updateTblTasks(str(self.cmbCategories.currentText()))
        
        self.tblTasks.selectRow(self.current_task_index)
    
    @pyqtSignature("int, int")
    def on_tblTriggers_cellClicked(self, row, column):
        self.txtTriggerName.setText(QString(self.tblTriggers.item(row, 0).text()))
        self.txtTriggerDescription.setText(QString(self.tblTriggers.item(row, 1).text()))
    
    @pyqtSignature("int, int")
    def on_tblEvents_cellClicked(self, row, column):
        self.current_event_index = row
        self.txtEventValueMask.setText(QString(self.tblEvents.item(row, 1).text()))
        self.cbxEventEnabled.setChecked(self.tblEvents.item(row, 4).text() == 'True')
    
    @pyqtSignature("")
    def on_btnAddEvent_clicked(self):
        wndNewTrigger = NewTrigger()
        wndNewTrigger.db = self.db
        wndNewTrigger.setup()
        if wndNewTrigger.exec_():
            self.updateTblEvents("")
            self.updateTblTriggers()
    
    @pyqtSignature("")
    def on_btnSaveEvent_clicked(self):
        sql = "update trigger_events set value_mask = %s, enabled = %s where id = %s"
        cursor = self.db.cursor()
        cursor.execute(sql, (self.txtEventValueMask.text(), self.cbxEventEnabled.isChecked(), self.events[self.current_event_index]))
        cursor.close()
        self.updateTblEvents(str(self.cmbTriggers.currentText()))
        self.tblEvents.selectRow(self.current_event_index)

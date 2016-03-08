from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .Ui_choosefootprint import Ui_Dialog
from inputwindows.newtask import NewTask
from inputwindows.newtrigger import NewTrigger
from inputwindows.adddomaincreds import wndAddDomainCreds
from inputwindows.confirmation import wndConfirmation

import netifaces

class ChooseFootprint(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.tblEvents.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblEvents.setSelectionMode(QAbstractItemView.SingleSelection)
        
        self.tblTasks.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblTasks.setSelectionMode(QAbstractItemView.SingleSelection)
        
        self.tblTriggers.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblTriggers.setSelectionMode(QAbstractItemView.SingleSelection)
        
        self.tblHostEnumerationPlugins.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        icon = QIcon('images/refresh.ico')
        self.btnRefreshNetworkInterfaces.setIcon(icon)
        
    db = None
    footprintDepth = {}
    
    def setFootprints(self, _footprints):
        self.cmbFootprints.addItems(_footprints)
        
    def updateUI(self):
        self.updateCmbTaskCategories()
        self.updateTblTriggers()
        self.updateCmbTriggers()
        self.updateFootprintDepths()
        self.updateHostEnumerationPlugins()
        self.on_btnRefreshNetworkInterfaces_clicked()
    
    @pyqtSignature("")
    def on_btnRefreshNetworkInterfaces_clicked(self):
        items = netifaces.interfaces()
        items.remove("lo")
        self.cmbNetworkInterface.clear()
        self.cmbNetworkInterface.addItems(items)
    
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
        cursor.execute("select category from task_categories order by position_id")
        self.cmbCategories.addItems([""])
        for row in cursor.fetchall():
            self.cmbCategories.addItems([row[0]])
        cursor.close()

    def updateFootprintDepths(self):
        cursor = self.db.cursor()
        cursor.execute("select category, description, position_id from task_categories order by position_id")
        self.footprintDepth[0] = ["Do nothing","No work will be done. This option will simply show previous results"]
        for row in cursor.fetchall():
            self.footprintDepth[row[2]] = [row[0], row[1]]
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
        cursor.execute("select tc.id, tc.category, td.id, td.task_name, td.description, td.file_name, td.uses_metasploit, td.is_recursive, td.enabled from task_categories tc join task_descriptions td on tc.id = td.task_categories_id where tc.category = %s", (category, ))
        for row in cursor.fetchall():
            self.tasks.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6] == '\x01', row[7] == '\x01', row[8] == '\x01'])
            self.tblTasks.setRowCount(self.tblTasks.rowCount() + 1)
            self.tblTasks.setItem(i, 0, QTableWidgetItem(row[1]))
            self.tblTasks.setItem(i, 1, QTableWidgetItem(row[3]))
            i = i + 1
        cursor.close()
        self.tblTasks.resizeColumnsToContents()

    enumerationPlugins = {}
    enumerationPluginsIndex = -1
    def updateHostEnumerationPlugins(self):
        self.tblHostEnumerationPlugins.setRowCount(0)
        self.enumerationPlugins = {}
        
        cursor = self.db.cursor()
        cursor.execute("select id, task_name, description from task_descriptions where task_categories_id = 1 and enabled = 1 order by task_name")
        i = 0
        for row in cursor.fetchall():
            self.enumerationPlugins[i] = [row[0], row[1],  row[2],  True]
            self.tblHostEnumerationPlugins.setRowCount(self.tblHostEnumerationPlugins.rowCount() + 1)
            self.tblHostEnumerationPlugins.setItem(i, 0, QTableWidgetItem(row[1]))
            self.tblHostEnumerationPlugins.setItem(i, 1, QTableWidgetItem(str(True)))
            i = i + 1
        cursor.close()
        self.tblHostEnumerationPlugins.resizeColumnsToContents()

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
        cursor.execute(sql, (trigger, ))
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
    
    @pyqtSignature("")
    def on_btnCreateTask_clicked(self):
        wndNewTask = NewTask()
        wndNewTask.db = self.db
        wndNewTask.setup()
        
        if wndNewTask.exec_():
            sql = "insert into task_descriptions (task_categories_id, task_name, description, file_name, uses_metasploit, is_recursive, enabled) values ((select id from task_categories where category = %s), %s, %s, %s, %s, %s, %s)"
            cursor = self.db.cursor()
            cursor.execute(sql, (wndNewTask.cmbCategory.currentText(), wndNewTask.txtName.text(), wndNewTask.txtDescription.toPlainText(), wndNewTask.txtFileName.text(), wndNewTask.cbxUsesMetasploit.isChecked(), wndNewTask.cbxIsRecursive.isChecked(), wndNewTask.cbxEnabled.isChecked(), ))
            cursor.close()
                
            self.updateTblTasks(str(self.cmbCategories.currentText()))
    
    @pyqtSignature("")
    def on_btnSaveTasksChanges_clicked(self):
        cursor = self.db.cursor()
        sql = "update task_descriptions set task_name = %s, description = %s, file_name = %s, uses_metasploit = %s, is_recursive = %s, enabled = %s where id = %s"
        r = self.tasks[self.current_task_index]
        
        cursor.execute(sql, (self.txtTaskName.text(), self.txtTaskDescription.toPlainText(), self.txtFileName.text(), self.cbxUsesMetasploit.isChecked(), self.cbxIsRecursive.isChecked(), self.cbxTaskEnabled.isChecked(), r[2], ))
        cursor.close()
        
        tmp_index = self.current_task_index
        self.updateTblTasks(str(self.cmbCategories.currentText()))
        self.current_task_index = tmp_index
        
        self.tblTasks.selectRow(self.current_task_index)
    
    @pyqtSignature("int, int, int, int")
    def on_tblHostEnumerationPlugins_currentCellChanged(self, row, currentColumn, previousRow, previousColumn):
        self.enumerationPluginsIndex = row
        #print self.enumerationPlugins[row]
        self.cbxRunHostEnumerationPlugin.setChecked(self.enumerationPlugins[row][3])
        self.lblHostEnumerationPluginDescription.setText(self.enumerationPlugins[row][2])

    @pyqtSignature("int")
    def on_cbxRunHostEnumerationPlugin_stateChanged(self, p0):
        if self.enumerationPluginsIndex != -1:
            self.enumerationPlugins[self.enumerationPluginsIndex][3] = (p0 != 0)
            self.tblHostEnumerationPlugins.setItem(self.enumerationPluginsIndex, 1, QTableWidgetItem(str(p0 != 0)))
            self.tblHostEnumerationPlugins.resizeColumnsToContents()
    
    @pyqtSignature("int, int, int, int")
    def on_tblTriggers_currentCellChanged(self, row, currentColumn, previousRow, previousColumn):
        self.txtTriggerName.setText(QString(self.tblTriggers.item(row, 0).text()))
        self.txtTriggerDescription.setText(QString(self.tblTriggers.item(row, 1).text()))
    
    @pyqtSignature("int, int, int, int")
    def on_tblEvents_currentCellChanged(self, row, currentColumn, previousRow, previousColumn):
        self.current_event_index = row
        self.txtEventValueMask.setText(QString(self.tblEvents.item(row, 1).text()))
        self.cbxEventEnabled.setChecked(self.tblEvents.item(row, 4).text() == 'True')
    
    @pyqtSignature("")
    def on_btnAddDomainCreds_clicked(self):
        w = wndAddDomainCreds()
        if w.exec_():
            i = self.tblDomainCreds.rowCount()
            self.tblDomainCreds.setRowCount(self.tblDomainCreds.rowCount() + 1)
            self.tblDomainCreds.setItem(i, 0, QTableWidgetItem(w.txtDomain.text()))
            self.tblDomainCreds.setItem(i, 1, QTableWidgetItem(w.txtUsername.text()))
            self.tblDomainCreds.setItem(i, 2, QTableWidgetItem(w.txtPassword.text()))
            self.tblDomainCreds.setItem(i, 3, QTableWidgetItem(w.txtLMHash.text()))
            self.tblDomainCreds.setItem(i, 4, QTableWidgetItem(w.txtNTLMHash.text()))
            self.tblDomainCreds.setItem(i, 5, QTableWidgetItem(str(w.cbxCheckAgainstDC.isChecked() == True)))
            self.tblDomainCreds.resizeColumnsToContents()
    
    @pyqtSignature("")
    def on_btnDeleteDomainCreds_clicked(self):
        w = wndConfirmation()
        if w.exec_():
            self.tblDomainCreds.removeRow(self.tblDomainCreds.currentRow())
    
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
        cursor.execute(sql, (self.txtEventValueMask.text(), self.cbxEventEnabled.isChecked(), self.events[self.current_event_index], ))
        cursor.close()
        self.updateTblEvents(str(self.cmbTriggers.currentText()))
        self.tblEvents.selectRow(self.current_event_index)
    
    @pyqtSignature("int")
    def on_sldTestDepth_valueChanged(self, value):
        self.lblDepthCategory.setText(self.footprintDepth[value][0])
        self.lblDepthDescription.setText(self.footprintDepth[value][1])
    
    @pyqtSignature("int, int, int, int")
    def on_tblTasks_currentCellChanged(self, currentRow, currentColumn, previousRow, previousColumn):
        self.current_task_index = currentRow
        self.txtTaskName.setText(QString(self.tasks[currentRow][3]))
        self.txtTaskDescription.setText(QString(self.tasks[currentRow][4]))
        self.txtFileName.setText(QString(self.tasks[currentRow][5]))
        self.cbxUsesMetasploit.setChecked(self.tasks[currentRow][6])
        self.cbxIsRecursive.setChecked(self.tasks[currentRow][7])
        self.cbxTaskEnabled.setChecked(self.tasks[currentRow][8])
    


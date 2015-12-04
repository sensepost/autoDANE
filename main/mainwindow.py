from PyQt4.QtCore import *
from PyQt4.QtGui import *

import threading

from worker.workerthread import WorkerThread

from .Ui_mainwindow import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    workerThreads = []
    footprint_id = 0
    db = None
    
    updateSummaryTrigger = pyqtSignal()
    updateSummaryInterval = 1
    
    updateTaskListTrigger = pyqtSignal()
    updateTaskListInterval = 1
    
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.initHostsTreeview()
        self.updateSummaryTrigger.connect(self.handleUpdateSummaryTrigger)
        self.updateTaskListTrigger.connect(self.handleUpdateTaskListTrigger)
        
        logoPixmap = QPixmap(QString.fromUtf8('images/logo.png'))
        logoScaledPixmap = logoPixmap.scaled(self.lblSensePostLogo.size(),  Qt.KeepAspectRatio)
        self.lblSensePostLogo.setPixmap(logoScaledPixmap)
        
        emailPixmap = QPixmap(QString.fromUtf8('images/email.png'))
        emailScaledPixmap = emailPixmap.scaled(self.lblEmailIcon.size(),  Qt.KeepAspectRatio)
        self.lblEmailIcon.setPixmap(emailScaledPixmap)
        
        emailScaledPixmap = emailPixmap.scaled(self.lblEmailIcon2.size(),  Qt.KeepAspectRatio)
        self.lblEmailIcon2.setPixmap(emailScaledPixmap)
        
        skypePixmap = QPixmap(QString.fromUtf8('images/skype.png'))
        skypeScaledPixmap = skypePixmap.scaled(self.lblSkypeLogo.size(),  Qt.KeepAspectRatio)
        self.lblSkypeLogo.setPixmap(skypeScaledPixmap)
    
    def callUpdateSummaryTrigger(self):
        self.updateSummaryTrigger.emit()

    def handleUpdateSummaryTrigger(self):
        self.on_btnUpdateSummary_clicked()
    
    def callUpdateTaskListTrigger(self):
        self.updateTaskListTrigger.emit()

    def handleUpdateTaskListTrigger(self):
        self.on_btnUpdateTaskList_clicked()
        
    def closeEvent(self, event):
        for wt in self.workerThreads:
            try:
                wt.stop()
            except:
                pass
            
        try:
            wt.metasploitProcess.terminate()
        except:
            pass
        event.accept()
        
    def startWork(self):
        normal_tasks = [1, 2, 3, 4, 5, 6, 7, 11, 12, 14, 18, 19]
        recursive_tasks = [9,  16]
        metasploit_tasks = [8, 10, 13, 15, 17]
        
        tasks = []
        for i in normal_tasks:
            tasks.append(i)
        for i in recursive_tasks:
            tasks.append(i)
        for i in metasploit_tasks:
            tasks.append(i)
        
        #wt1 = WorkerThread()
        #wt1.init(self.footprint_id, normal_tasks)
        #wt1.start()
        #self.workerThreads.append(wt1)
        
        #wt2 = WorkerThread()
        #wt2.init(self.footprint_id, recursive_tasks)
        #wt2.start()
        #self.workerThreads.append(wt2)
        
        #wt3 = WorkerThread()
        #wt3.init(self.footprint_id, metasploit_tasks)
        #wt3.start()
        #self.workerThreads.append(wt3)
        
        wt1 = WorkerThread()
        wt1.init(self.footprint_id, tasks)
        wt1.start()
        self.workerThreads.append(wt1)
        
        #wt2 = WorkerThread()
        #wt2.init(self.footprint_id, tasks)
        #wt2.start()
        #self.workerThreads.append(wt2)
        
    taskLogs = []
    @pyqtSignature("")
    def on_btnUpdateTaskLogs_clicked(self):
        self.taskLogs = []
        self.tblTaskLogs.setRowCount(0)
        sql = """select
                    tc.category,
                    td.task_name,
                    tl.log
                from
                    task_list tl
                    join task_descriptions td on td.id = tl.task_descriptions_id
                    join task_categories tc on tc.id = td.task_categories_id
                where 
                    tl.footprint_id = %s and
                    tl.completed = 1 and
                    tl.log is not null
                order by 
                    tc.category,
                    td.task_name"""
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id))
        for row in cursor.fetchall():
            self.taskLogs.append(row[2])
            self.tblTaskLogs.setRowCount(self.tblTaskLogs.rowCount() + 1)
            self.tblTaskLogs.setItem(self.tblTaskLogs.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblTaskLogs.setItem(self.tblTaskLogs.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
        self.tblTaskLogs.resizeColumnsToContents()
        cursor.close()
        
    @pyqtSignature("int, int")
    def on_tblTaskLogs_cellClicked(self, row, column):
        self.txtTaskLog.setPlainText(self.taskLogs[row])
        
    website_ids = []
    def updateWebsites(self):
        self.tblWebsites.setRowCount(0)
        self.website_ids = []
        sql = "select hd.ip_address, hd.host_name, pd.port_number, w.html_title, w.id from host_data hd join port_data pd on hd.id = pd.host_data_id join websites w on w.port_data_id = pd.id where hd.footprint_id = %s"
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id))
        for row in cursor.fetchall():
            self.website_ids.append(row[4])
            self.tblWebsites.setRowCount(self.tblWebsites.rowCount() + 1)
            self.tblWebsites.setItem(self.tblWebsites.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblWebsites.setItem(self.tblWebsites.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblWebsites.setItem(self.tblWebsites.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
            self.tblWebsites.setItem(self.tblWebsites.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
        cursor.close()

    def updateDomainsSummary(self):
        self.tblDomains.setRowCount(0)
        sql = "select domain_name from domains where footprint_id = %s order by domain_name"
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id))
        for row in cursor.fetchall():
            self.tblDomains.setRowCount(self.tblDomains.rowCount() + 1)
            self.tblDomains.setItem(self.tblDomains.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
        cursor.close()
        
    def updatePortsSummary(self):
        self.tblOpenPortsSummary.setRowCount(0)
        sql = "select port_number, count(port_number) from host_data hd join port_data pd on hd.id = pd.host_data_id where footprint_id = %s group by port_number"
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id))
        for row in cursor.fetchall():
            self.tblOpenPortsSummary.setRowCount(self.tblOpenPortsSummary.rowCount() + 1)
            self.tblOpenPortsSummary.setItem(self.tblOpenPortsSummary.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblOpenPortsSummary.setItem(self.tblOpenPortsSummary.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
        cursor.close()

    def updateSummaryLabel(self):
        sql = """select
                (select count(*) from host_data where footprint_id = %s) as 'hosts',
                (select count(*) from host_data hd join port_data pd on hd.id = pd.host_data_id where hd.footprint_id = %s) as 'ports',
                (select count(*) from host_data hd join port_data pd on hd.id = pd.host_data_id join vulnerabilities v on pd.id = v.port_data_id where hd.footprint_id = %s) as 'vulns'
        """
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id, self.footprint_id, self.footprint_id))
        row = cursor.fetchone()
        self.lblSummaryLabel.setText("Identified {0} hosts, {1} open ports, {2} shells".format(row[0], row[1],  row[2]))
        cursor.close()
    
    def updateCredsSummary(self):
        sql = """select 'Local Credentials' as label, (select count(distinct lc.username, lc.cleartext_password)  from local_credentials_map m join host_data hd on hd.id = m.host_data_id join local_credentials lc on lc.id = m.local_credentials_id where hd.footprint_id = %s and lc.cleartext_password != '' and m.valid = 1) as count
                union select 'Domain Credentials' as label, (select count(distinct domain, username, cleartext_password) from domain_credentials where footprint_id = %s) as count
                union select 'Impersonation Tokens' as label, (select count(distinct t.token) from host_data hd join tokens t on hd.id = t.host_id where hd.footprint_id = %s order by t.token) as count"""
        self.tblCredsSummary.setRowCount(0)
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id, self.footprint_id, self.footprint_id))
        for row in cursor.fetchall():
            self.tblCredsSummary.setRowCount(self.tblCredsSummary.rowCount() + 1)
            self.tblCredsSummary.setItem(self.tblCredsSummary.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblCredsSummary.setItem(self.tblCredsSummary.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
        self.tblCredsSummary.resizeColumnsToContents()
        cursor.close()

    def updateVulnSummary(self):
        self.tblVulnsSummary.setRowCount(0)
        sql = "select vd.description, count(vd.description) from host_data hd join port_data pd on hd.id = pd.host_data_id join vulnerabilities v on v.port_data_id = pd.id join vulnerability_descriptions vd on vd.id = v.vulnerability_descriptions_id where hd.footprint_id = %s group by vd.description"
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id))
        for row in cursor.fetchall():
            self.tblVulnsSummary.setRowCount(self.tblVulnsSummary.rowCount() + 1)
            self.tblVulnsSummary.setItem(self.tblVulnsSummary.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblVulnsSummary.setItem(self.tblVulnsSummary.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
        self.tblVulnsSummary.resizeColumnsToContents()
        cursor.close()
        
    tvHostsModel = None
    def initHostsTreeview(self):
        view = self.tvHosts
        view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tvHosts.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tvHostsModel = QStandardItemModel()
        self.tvHostsModel.setHorizontalHeaderLabels(['Host',  'Name'])
        view.setModel(self.tvHostsModel)
        view.setColumnWidth(0, 150)
        view.setUniformRowHeights(True)

    def updateHostsTreeview(self):
        self.initHostsTreeview()
        sql = "select net_range from net_ranges where footprint_id = %s order by net_range"
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id))
        for row in cursor.fetchall():
            node = QStandardItem(row[0])
            self.tvHostsModel.appendRow(node)
        cursor.close()
    
    @pyqtSignature("")
    def on_btnUpdateHosts_clicked(self):
        self.tblHostPorts.setRowCount(0)
        self.tblHostVulns.setRowCount(0)
        self.updateHostsTreeview()
    
    @pyqtSignature("")
    def on_btnUpdateSummary_clicked(self):
        self.updatePortsSummary()
        self.updateVulnSummary()
        self.updateCredsSummary()
        self.updateSummaryLabel()
        self.updateDomainsSummary()
        
        if self.cbxUpdateSummary.isChecked() == True:
            threading.Timer(self.updateSummaryInterval, self.callUpdateSummaryTrigger).start()
            
    @pyqtSignature("int")
    def on_cbxUpdateSummary_stateChanged(self, p0):
        if p0:
            threading.Timer(self.updateSummaryInterval, self.callUpdateSummaryTrigger).start()
        
    exploit_logs = []
    @pyqtSignature("QModelIndex")
    def on_tvHosts_clicked(self, index):
        node = index.model().itemFromIndex(index)
        
        if str(node.text()).find("0/24") != -1:
            net_range = node.text().replace("0/24", "%")
            self.tblHostPorts.setRowCount(0)
            self.tblHostVulns.setRowCount(0)
            
            for i in range(0, node.rowCount()):
                node.removeRow(0)
            cursor = self.db.cursor()
            cursor.execute("select ip_address, host_name from host_data where ip_address like %s and footprint_id = %s order by INET_ATON(ip_address)", (net_range, self.footprint_id))
            for row in cursor.fetchall():
                node.appendRow( [ QStandardItem(row[0]),  QStandardItem(row[1]) ] )
            cursor.close()
        else:
            sql = "select computer_name, os, architecture, system_language, domain from host_data where ip_address = %s and footprint_id = %s"
            cursor = self.db.cursor()
            cursor.execute(sql, (node.text(), self.footprint_id))
            row = cursor.fetchone()
            self.lblComputerName.setText(row[0])
            self.lblOS.setText(row[1])
            self.lblArchitecture.setText(row[2])
            self.lblLanguage.setText(row[3])
            self.lblDomain.setText(row[4])
            cursor.close()
            
            sql = "select pd.port_number from host_data hd join port_data pd on hd.id = pd.host_data_id where hd.ip_address = %s and hd.footprint_id = %s order by pd.port_number"
            cursor = self.db.cursor()
            cursor.execute(sql, (node.text(), self.footprint_id))
            self.tblHostPorts.setRowCount(0)
            for row in cursor.fetchall():
                self.tblHostPorts.setRowCount(self.tblHostPorts.rowCount() + 1)
                self.tblHostPorts.setItem(self.tblHostPorts.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblHostPorts.resizeColumnsToContents()
            cursor.close()
            
            sql = "select pd.port_number, vd.description from host_data hd join port_data pd on hd.id = pd.host_data_id join vulnerabilities v on v.port_data_id = pd.id join vulnerability_descriptions vd on vd.id = v.vulnerability_descriptions_id where hd.ip_address = %s and hd.footprint_id = %s"
            cursor = self.db.cursor()
            cursor.execute(sql, (node.text(), self.footprint_id))
            self.tblHostVulns.setRowCount(0)
            for row in cursor.fetchall():
                self.tblHostVulns.setRowCount(self.tblHostVulns.rowCount() + 1)
                self.tblHostVulns.setItem(self.tblHostVulns.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
                self.tblHostVulns.setItem(self.tblHostVulns.rowCount() - 1, 1, QTableWidgetItem(row[1]))
            self.tblHostVulns.resizeColumnsToContents()
            cursor.close()
            
            #sql = "select vd.description, el.log from host_data hd join port_data pd on hd.id = pd.host_data_id join vulnerabilities v on pd.id = v.port_data_id join vulnerability_descriptions vd on vd.id = v.vulnerability_descriptions_id join exploit_logs el on el.vulnerability_id = v.id where hd.ip_address = %s and hd.footprint_id = %s"
            sql = "select vd.description, el.log from host_data hd join exploit_logs el on hd.id = el.host_data_id join vulnerability_descriptions vd on vd.id = el.vulnerability_description_id where hd.ip_address = %s and hd.footprint_id = %s"
            cursor = self.db.cursor()
            cursor.execute(sql, (node.text(), self.footprint_id))
            self.tblExploitLogs.setRowCount(0)
            self.exploit_logs = []
            for row in cursor.fetchall():
                self.tblExploitLogs.setRowCount(self.tblExploitLogs.rowCount() + 1)
                self.tblExploitLogs.setItem(self.tblExploitLogs.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
                self.exploit_logs.append(row[1])
            self.tblExploitLogs.resizeColumnsToContents()
            cursor.close()
            
            sql = "select lc.username, lc.cleartext_password, lc.lm_hash, lc.ntlm_hash from host_data hd join local_credentials lc on hd.id = lc.host_data_id where hd.ip_address = %s and hd.footprint_id = %s order by lc.username"
            cursor = self.db.cursor()
            cursor.execute(sql, (node.text(), self.footprint_id))
            self.tblLocalCreds.setRowCount(0)
            for row in cursor.fetchall():
                self.tblLocalCreds.setRowCount(self.tblLocalCreds.rowCount() + 1)
                self.tblLocalCreds.setItem(self.tblLocalCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
                self.tblLocalCreds.setItem(self.tblLocalCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
                self.tblLocalCreds.setItem(self.tblLocalCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
                self.tblLocalCreds.setItem(self.tblLocalCreds.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
            self.tblLocalCreds.resizeColumnsToContents()
            cursor.close()
            
            sql = """select 'Local Credentials' as label, (select count(distinct lc.username, lc.cleartext_password)  from local_credentials_map m join host_data hd on hd.id = m.host_data_id join local_credentials lc on lc.id = m.local_credentials_id where hd.footprint_id = %s and hd.ip_address = %s and lc.cleartext_password != '' and m.valid = 1) as count
                    union select 'Domain Credentials' as label, (select count(*) from domain_credentials_map m join host_data hd on hd.id = m.host_data_id where hd.footprint_id = %s and hd.ip_address = %s) as count
                    union select 'Impersonation Tokens' as label, (select count(t.token) from host_data hd join tokens t on hd.id = t.host_id where hd.footprint_id = %s and hd.ip_address = %s order by t.token) as count"""
            cursor = self.db.cursor()
            cursor.execute(sql, (self.footprint_id, node.text(), self.footprint_id, node.text(), self.footprint_id, node.text()))
            self.tblHostCredsSummary.setRowCount(0)
            for row in cursor.fetchall():
                self.tblHostCredsSummary.setRowCount(self.tblHostCredsSummary.rowCount() + 1)
                self.tblHostCredsSummary.setItem(self.tblHostCredsSummary.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
                self.tblHostCredsSummary.setItem(self.tblHostCredsSummary.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblHostCredsSummary.resizeColumnsToContents()
            cursor.close()
            
            sql = "select t.token from host_data hd join tokens t on hd.id = t.host_id where hd.ip_address = %s and hd.footprint_id = %s order by t.token"
            cursor = self.db.cursor()
            cursor.execute(sql, (node.text(), self.footprint_id))
            self.tblAvailableTokens.setRowCount(0)
            for row in cursor.fetchall():
                self.tblAvailableTokens.setRowCount(self.tblAvailableTokens.rowCount() + 1)
                self.tblAvailableTokens.setItem(self.tblAvailableTokens.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblAvailableTokens.resizeColumnsToContents()
            cursor.close()
            
            sql = "select dc.domain, dc.username, dc.cleartext_password from host_data hd join domain_credentials_map m on m.host_data_id = hd.id join domain_credentials dc on dc.id = m.domain_credentials_id where hd.footprint_id = %s and hd.ip_address = %s"
            cursor = self.db.cursor()
            cursor.execute(sql, (self.footprint_id, node.text()))
            self.tblDomainCreds.setRowCount(0)
            for row in cursor.fetchall():
                self.tblDomainCreds.setRowCount(self.tblDomainCreds.rowCount() + 1)
                self.tblDomainCreds.setItem(self.tblDomainCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
                self.tblDomainCreds.setItem(self.tblDomainCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
                self.tblDomainCreds.setItem(self.tblDomainCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
            self.tblDomainCreds.resizeColumnsToContents()
            cursor.close()
    
    @pyqtSignature("int, int")
    def on_tblExploitLogs_cellClicked(self, row, column):
        self.txtExploitLog.setText(self.exploit_logs[row])
        
    @pyqtSignature("int, int")
    def on_tblWebsites_cellClicked(self, row, column):
        cursor = self.db.cursor()
        cursor.execute("select html_title, html_body, screenshot from websites where id = %s", (self.website_ids[row]))
        row = cursor.fetchone()
        cursor.close()
        
        with open("temp/websites_website.jpg", 'w') as f:
            f.write(row[2])
        
        websitePixmap = QPixmap(QString.fromUtf8('temp/websites_website.jpg'))
        #websitePixmapScaledPixmap = websitePixmap.scaled(self.lblWebsitesScreenshot.size(),  Qt.KeepAspectRatio)
        #self.lblWebsitesScreenshot.setPixmap(websitePixmap.scaledToWidth(self.lblWebsitesScreenshot.width()))
        self.lblWebsitesScreenshot.setPixmap(websitePixmap)
        self.txtWebsiteHtml.setPlainText(row[1])
        
    
    @pyqtSignature("")
    def on_btnUpdateCreds_clicked(self):
        sqlAllDomainCreds = "select distinct domain, username, cleartext_password from domain_credentials where footprint_id = %s"
        sqlValidDomainCreds = "select hd.ip_address, dc.domain, dc.username, dc.cleartext_password from domain_credentials_map m join host_data hd on hd.id = m.host_data_id join domain_credentials dc on dc.id = m.domain_credentials_id where hd.footprint_id = %s and m.valid = %s"
        sqlAllLocalCreds = "select distinct lc.username, lc.cleartext_password, lc.lm_hash, lc.ntlm_hash from local_credentials_map m join host_data hd on hd.id = m.host_data_id join local_credentials lc on lc.id = m.local_credentials_id where hd.footprint_id = %s and m.valid = 1"
        sqlValidLocalCreds = "select hd.ip_address, lc.username, lc.cleartext_password, lc.lm_hash, lc.ntlm_hash, m.valid from local_credentials_map m join host_data hd on hd.id = m.host_data_id join local_credentials lc on lc.id = m.local_credentials_id where hd.footprint_id = %s and m.valid = %s"
        sqlTokens = "select distinct t.token from host_data hd join tokens t on hd.id = t.host_id where hd.footprint_id = %s order by token"
        
        cursor = self.db.cursor()
        cursor.execute(sqlAllDomainCreds, (self.footprint_id))
        self.tblAllDomainCreds.setRowCount(0)
        for row in cursor.fetchall():
            self.tblAllDomainCreds.setRowCount(self.tblAllDomainCreds.rowCount() + 1)
            self.tblAllDomainCreds.setItem(self.tblAllDomainCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblAllDomainCreds.setItem(self.tblAllDomainCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblAllDomainCreds.setItem(self.tblAllDomainCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
        self.tblAllDomainCreds.resizeColumnsToContents()
        cursor.close()
        
        cursor = self.db.cursor()
        cursor.execute(sqlValidDomainCreds, (self.footprint_id, "1"))
        self.tblValidDomainCreds.setRowCount(0)
        for row in cursor.fetchall():
            self.tblValidDomainCreds.setRowCount(self.tblValidDomainCreds.rowCount() + 1)
            self.tblValidDomainCreds.setItem(self.tblValidDomainCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblValidDomainCreds.setItem(self.tblValidDomainCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblValidDomainCreds.setItem(self.tblValidDomainCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
            self.tblValidDomainCreds.setItem(self.tblValidDomainCreds.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
        self.tblValidDomainCreds.resizeColumnsToContents()
        cursor.close()
        
        cursor = self.db.cursor()
        cursor.execute(sqlValidDomainCreds, (self.footprint_id, "0"))
        self.tblInvalidDomainCreds.setRowCount(0)
        for row in cursor.fetchall():
            self.tblInvalidDomainCreds.setRowCount(self.tblInvalidDomainCreds.rowCount() + 1)
            self.tblInvalidDomainCreds.setItem(self.tblInvalidDomainCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblInvalidDomainCreds.setItem(self.tblInvalidDomainCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblInvalidDomainCreds.setItem(self.tblInvalidDomainCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
            self.tblInvalidDomainCreds.setItem(self.tblInvalidDomainCreds.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
        self.tblInvalidDomainCreds.resizeColumnsToContents()
        cursor.close()
        
        cursor = self.db.cursor()
        cursor.execute(sqlAllLocalCreds, (self.footprint_id))
        self.tblAllLocalCreds.setRowCount(0)
        for row in cursor.fetchall():
            self.tblAllLocalCreds.setRowCount(self.tblAllLocalCreds.rowCount() + 1)
            self.tblAllLocalCreds.setItem(self.tblAllLocalCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblAllLocalCreds.setItem(self.tblAllLocalCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblAllLocalCreds.setItem(self.tblAllLocalCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
            self.tblAllLocalCreds.setItem(self.tblAllLocalCreds.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
        self.tblAllLocalCreds.resizeColumnsToContents()
        cursor.close()
        
        cursor = self.db.cursor()
        cursor.execute(sqlValidLocalCreds, (self.footprint_id, "1"))
        self.tblValidLocalCreds.setRowCount(0)
        for row in cursor.fetchall():
            self.tblValidLocalCreds.setRowCount(self.tblValidLocalCreds.rowCount() + 1)
            self.tblValidLocalCreds.setItem(self.tblValidLocalCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblValidLocalCreds.setItem(self.tblValidLocalCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblValidLocalCreds.setItem(self.tblValidLocalCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
            self.tblValidLocalCreds.setItem(self.tblValidLocalCreds.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
            self.tblValidLocalCreds.setItem(self.tblValidLocalCreds.rowCount() - 1, 4, QTableWidgetItem(str(row[4])))
        self.tblValidLocalCreds.resizeColumnsToContents()
        cursor.close()
        
        cursor = self.db.cursor()
        cursor.execute(sqlValidLocalCreds, (self.footprint_id, "0"))
        self.tblInvalidLocalCreds.setRowCount(0)
        for row in cursor.fetchall():
            self.tblInvalidLocalCreds.setRowCount(self.tblInvalidLocalCreds.rowCount() + 1)
            self.tblInvalidLocalCreds.setItem(self.tblInvalidLocalCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblInvalidLocalCreds.setItem(self.tblInvalidLocalCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblInvalidLocalCreds.setItem(self.tblInvalidLocalCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
        self.tblInvalidLocalCreds.resizeColumnsToContents()
        cursor.close()
        
        cursor = self.db.cursor()
        cursor.execute(sqlTokens, (self.footprint_id))
        self.tblTokens.setRowCount(0)
        for row in cursor.fetchall():
            self.tblTokens.setRowCount(self.tblTokens.rowCount() + 1)
            self.tblTokens.setItem(self.tblTokens.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
        self.tblTokens.resizeColumnsToContents()
        cursor.close()

    @pyqtSignature("")
    def on_btnUpdateWebsites_clicked(self):
        self.updateWebsites()
        
    @pyqtSignature("")
    def on_btnUpdateVulns_clicked(self):
        sql = """
            select 
                distinct vd.description
                #distinct concat(SUBSTRING(hd.ip_address, 1, length(hd.ip_address) - locate('.', reverse(hd.ip_address))), '.0/24') as ranges
            from 
                host_data hd
                join port_data pd on hd.id = pd.host_data_id
                join vulnerabilities v on v.port_data_id = pd.id
                join vulnerability_descriptions vd on vd.id = v.vulnerability_descriptions_id
            where 
                hd.footprint_id = %s"""
                
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id))
        for row in cursor.fetchall():
            print row[0]
            node = QStandardItem(row[0])
            self.tvVulnsModel.appendRow(node)
        cursor.close()
    
    @pyqtSignature("")
    def on_btnUpdateTaskList_clicked(self):
        sql = """
        select 
            tc.category, td.task_name, count(td.task_name) as 'count' 
        from task_list tl
            join task_descriptions td on tl.task_descriptions_id = td.id
            join task_categories tc on tc.id = td.task_categories_id
        where tl.footprint_id = %s and
            td.enabled = 1 and tl.in_progress = %s and tl.completed = %s group by td.task_name order by tc.category
        """
        
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id, "0", "0"))
        self.tblTaskListPending.setRowCount(0)
        for row in cursor.fetchall():
            self.tblTaskListPending.setRowCount(self.tblTaskListPending.rowCount() + 1)
            self.tblTaskListPending.setItem(self.tblTaskListPending.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblTaskListPending.setItem(self.tblTaskListPending.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblTaskListPending.setItem(self.tblTaskListPending.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
        self.tblTaskListPending.resizeColumnsToContents()
        cursor.close()
        
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id, "1", "0"))
        self.tblTaskListInProgress.setRowCount(0)
        for row in cursor.fetchall():
            self.tblTaskListInProgress.setRowCount(self.tblTaskListInProgress.rowCount() + 1)
            self.tblTaskListInProgress.setItem(self.tblTaskListInProgress.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblTaskListInProgress.setItem(self.tblTaskListInProgress.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblTaskListInProgress.setItem(self.tblTaskListInProgress.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
        self.tblTaskListInProgress.resizeColumnsToContents()
        cursor.close()
        
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id, "0", "1"))
        self.tblTaskListDone.setRowCount(0)
        for row in cursor.fetchall():
            self.tblTaskListDone.setRowCount(self.tblTaskListDone.rowCount() + 1)
            self.tblTaskListDone.setItem(self.tblTaskListDone.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblTaskListDone.setItem(self.tblTaskListDone.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblTaskListDone.setItem(self.tblTaskListDone.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
        self.tblTaskListDone.resizeColumnsToContents()
        cursor.close()
        
        if self.cbxUpdateTaskList.isChecked() == True:
            threading.Timer(self.updateTaskListInterval, self.callUpdateTaskListTrigger).start()
            
    @pyqtSignature("int")
    def on_cbxUpdateTaskList_stateChanged(self, p0):
        if p0:
            threading.Timer(self.updateTaskListInterval, self.callUpdateTaskListTrigger).start()

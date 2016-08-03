from PyQt4.QtCore import *
from PyQt4.QtGui import *

import base64
import thread
import threading
import time
import os
import random
import string

from worker.workerthread import WorkerThread

from .Ui_mainwindow import Ui_MainWindow
from inputwindows.confirmation import wndConfirmation
from inputwindows.textinput import wndTextInput
from inputwindows.adddomaincreds import wndAddDomainCreds
from inputwindows.addhost import wndAddHost


class MainWindow(QMainWindow, Ui_MainWindow):
    workerThreads = []
    footprint_id = 0
    db = None

    updateSummaryTrigger = pyqtSignal()
    updateSummaryInterval = 1

    updateTaskListTrigger = pyqtSignal()
    updateTaskListInterval = 1

    updateCredsTrigger = pyqtSignal()

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.initHostsTreeview()
        self.updateSummaryTrigger.connect(self.handleUpdateSummaryTrigger)
        self.updateTaskListTrigger.connect(self.handleUpdateTaskListTrigger)
        self.updateCredsTrigger.connect(self.handleUpdateCredsTrigger)

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

    def handleUpdateCredsTrigger(self):
        self.on_btnUpdateCreds_clicked()
        self.updateDomainsSummary()

    def closeEvent(self, event):
        for wt in self.workerThreads:
            try:
                wt.stop()
            except:
                pass

        # try:
        #    wt.metasploitProcess.terminate()
        # except:
        #    pass
        event.accept()

    def setupFilterCombos(self):
        categories = [""]
        sqlCategory = "select category from task_categories order by position_id"
        cursor = self.db.cursor()
        cursor.execute(sqlCategory)
        for r in cursor.fetchall():
            categories.append(r[0])
        cursor.close()

        self.cmbLogsCategory.addItems(categories)

    @pyqtSignature("QString")
    def on_cmbLogsCategory_currentIndexChanged(self, p0):
        tasks = [""]
        sqlTasks = "select td.task_name from task_categories tc join task_descriptions td on tc.id = td.task_categories_id where tc.category = %s and td.enabled = true order by task_name"
        cursor = self.db.cursor()
        cursor.execute(sqlTasks, (str(p0), ))
        for r in cursor.fetchall():
            tasks.append(r[0])
        cursor.close()

        self.cmbLogsTask.clear()
        self.cmbLogsTask.addItems(tasks)

    def getTaskIdsByPosition(self, position):
        sql = "select td.id from task_descriptions td join task_categories tc on tc.id = td.task_categories_id where tc.position_id = %s"
        result = []

        cursor = self.db.cursor()
        cursor.execute(sql, (position, ))
        for row in cursor.fetchall():
            result.append(row[0])
        cursor.close()

        return result

    def getTaskIdsByPositionWoMsf(self, position,  msf):
        sql = "select td.id from task_descriptions td join task_categories tc on tc.id = td.task_categories_id where tc.position_id = %s and td.uses_metasploit = %s"
        result = []

        cursor = self.db.cursor()
        cursor.execute(sql, (position, msf, ))
        for row in cursor.fetchall():
            result.append(row[0])
        cursor.close()

        return result

    def startWork(self, maxDepth, nmapTiming, networkInterface, thread_counts):
        footprinting = []
        footprinting.extend(self.getTaskIdsByPosition(1))
        footprinting.extend(self.getTaskIdsByPosition(2))
        footprinting.extend(self.getTaskIdsByPosition(3))

        vuln_exploits = []  # 4
        vuln_exploits.extend(self.getTaskIdsByPosition(4))

        pivoting_nomsf = []  # 5
        pivoting_nomsf.extend(self.getTaskIdsByPositionWoMsf(5, False))

        pivoting_msf = []  # 5
        pivoting_msf.extend(self.getTaskIdsByPositionWoMsf(5, True))

        domain_enumeration = []  # 6
        domain_enumeration.extend(self.getTaskIdsByPosition(6))

        all_tasks = []
        all_tasks.extend(footprinting)
        all_tasks.extend(vuln_exploits)
        all_tasks.extend(pivoting_nomsf)
        all_tasks.extend(pivoting_msf)
        all_tasks.extend(domain_enumeration)

        #################################################

        for i in range(thread_counts['all']):
            wt = WorkerThread()
            wt.init(self.footprint_id, all_tasks, maxDepth, nmapTiming, networkInterface)
            wt.start()
            self.workerThreads.append(wt)
            time.sleep(5)

        for i in range(thread_counts['footprinting']):
            wt = WorkerThread()
            wt.init(self.footprint_id, footprinting, maxDepth, nmapTiming, networkInterface)
            wt.start()
            self.workerThreads.append(wt)
            time.sleep(5)

        for i in range(thread_counts['exploits']):
            wt = WorkerThread()
            wt.init(self.footprint_id, vuln_exploits, maxDepth, nmapTiming, networkInterface)
            wt.start()
            self.workerThreads.append(wt)
            time.sleep(5)

        for i in range(thread_counts['pivoting']):
            wt = WorkerThread()
            wt.init(self.footprint_id, pivoting_nomsf, maxDepth, nmapTiming, networkInterface)
            wt.start()
            self.workerThreads.append(wt)
            time.sleep(5)

        for i in range(thread_counts['pivoting_msf']):
            wt = WorkerThread()
            wt.init(self.footprint_id, pivoting_msf, maxDepth, nmapTiming, networkInterface)
            wt.start()
            self.workerThreads.append(wt)
            time.sleep(5)

        for i in range(thread_counts['domain_enumeration']):
            wt = WorkerThread()
            wt.init(self.footprint_id, domain_enumeration, maxDepth, nmapTiming, networkInterface)
            wt.start()
            self.workerThreads.append(wt)
            time.sleep(5)

    def importHashesFromLoot(self, domain, filename):
        try:
            with open(filename) as f:
                for line in f:
                    data = line.split(":")
                    username = data[0]
                    lm_hash = data[2]
                    nt_hash = data[3][:-1]
                    if username.find("$") == -1:
                        cursor = self.db.cursor()
                        cursor.execute("select addDomainCreds(%s, %s, %s, %s, '', %s, %s)",  (self.footprint_id, 0, domain, username, lm_hash, nt_hash, ))
                        cursor.close()

            self.syncCredsWithPotFile()
        except:
            pass

    @pyqtSignature("")
    def on_btnImportLoot_clicked(self):
        w = wndTextInput()
        w.setWindowTitle("Enter loot file name")
        if w.exec_():
            thread.start_new_thread(
                self.importHashesFromLoot, (w.txtDomain.text(), w.txtLootFileName.text(), ))

    @pyqtSignature("")
    def on_btnAddHost_clicked(self):
        w = wndAddHost()
        if w.exec_():
            # print w.txtIPAddress.text()
            cursor = self.db.cursor()
            cursor.execute("select addHost(%s, %s::varchar, ''::varchar, false)", (self.footprint_id, str(w.txtIPAddress.text()), ))
            cursor.close()

    @pyqtSignature("")
    def on_btnAddDomainCreds_clicked(self):
        w = wndAddDomainCreds()
        if w.exec_():
            cursor = self.db.cursor()
            cursor.execute("select addDomainCreds(%s, 0, %s, %s, %s, %s, %s)",  (self.footprint_id, str(w.txtDomain.text()), str(w.txtUsername.text()), str(w.txtPassword.text()), str(w.txtLMHash.text()), str(w.txtNTLMHash.text()), ))
            cursor.close()

            if w.cbxCheckAgainstDC.isChecked() is True:
                cursor = self.db.cursor()
                cursor.execute("update domain_credentials set verified = true, valid = true where footprint_id = %s and domain = %s and username = %s", (
                                self.footprint_id, str(w.txtDomain.text()), str(w.txtUsername.text()), ))
                cursor.close()

    @pyqtSignature("")
    def on_btnOpenRDPSession_clicked(self):
        try:
            index = self.tvHosts.selectedIndexes()[0]
            crawler = index.model().itemFromIndex(index)
            host = crawler.text()

            domain = self.tblDomainCreds.item(self.tblDomainCreds.currentRow(), 0).text()
            username = self.tblDomainCreds.item(self.tblDomainCreds.currentRow(), 1).text()
            password = self.tblDomainCreds.item(self.tblDomainCreds.currentRow(), 2).text()

            delimited_pwd = ""
            for c in password:
                delimited_pwd = delimited_pwd + "\{}".format(c)

            cmd = "rdesktop -0 -g 1024x768 -d {} -u {} -p {} {}".format(domain, username, delimited_pwd, host)
            print cmd
            thread.start_new_thread(self.runCmd, (cmd, ))
        except:
            pass

    def runCmd(self, cmd):
        os.popen(cmd)

    @pyqtSignature("")
    def on_btnRerunTask_clicked(self):
        w = wndConfirmation()
        if w.exec_():
            cursor = self.db.cursor()
            cursor.execute("update task_list set completed = false where id = %s", (self.taskLogs[self.task_log_index][1], ))
            cursor.close()

    taskLogs = []

    def is_int(self, v):
        v = str(v).strip()
        return v=='0' or (v if v.find('..') > -1 else v.lstrip('-+').rstrip('0').rstrip('.')).isdigit()


    @pyqtSignature("")
    def on_btnSearchHosts_clicked(self):
        filterValue = self.cmbHostFilterField.currentText()
        sql = ""
        if filterValue == "":
            sql = """select distinct concat(SUBSTRING(ip_address, 1, length(ip_address) - position('.' in reverse(ip_address))), '.0/24')
                     from host_data where footprint_id = %s order by 1"""
        elif filterValue == "IP Address":
            sql = """select distinct concat(SUBSTRING(ip_address, 1, length(ip_address) - position('.' in reverse(ip_address))), '.0/24')
                     from host_data where footprint_id = %s and ip_address like %s order by 1"""
        elif filterValue == "Host Name":
            sql = """select distinct concat(SUBSTRING(ip_address, 1, length(ip_address) - position('.' in reverse(ip_address))), '.0/24')
                     from host_data where footprint_id = %s and upper(host_name) like upper(%s) order by 1"""
        elif filterValue == "Port":
            sql = """select distinct concat(SUBSTRING(ip_address, 1, length(ip_address) - position('.' in reverse(ip_address))), '.0/24')
                     from host_data hd join port_data pd on hd.id = pd.host_data_id where footprint_id = %s and port_number = ANY(%s) order by 1"""
        elif filterValue == "Domain":
            sql = """select distinct concat(SUBSTRING(ip_address, 1, length(ip_address) - position('.' in reverse(ip_address))), '.0/24')
                     from host_data where footprint_id = %s and upper(domain) like upper(%s) order by 1"""

        self.initHostsTreeview()
        cursor = self.db.cursor()
        if filterValue == "":
            cursor.execute(sql, (self.footprint_id, ))
        elif filterValue == "Port":
            ports = ""
            for port in self.txtHostFilterValue.text().split(","):
                if self.is_int(port):
                    ports += port + ","
            ports = ports[:-1]

            cursor.execute(sql, (self.footprint_id, "{" + str(ports) + "}", ))
        else:
            cursor.execute(sql, (self.footprint_id, str("%" + self.txtHostFilterValue.text() + "%"), ))
        for row in cursor.fetchall():
            node = QStandardItem(row[0])
            self.tvHostsModel.appendRow(node)
        cursor.close()




    @pyqtSignature("")
    def on_btnSearchLogs_clicked(self):
        self.taskLogs = []
        self.tblTaskLogs.setRowCount(0)

        sqlNeitherSelected = """select tc.category, td.task_name, tl.log, tl.id from task_list tl join task_descriptions td on td.id = tl.task_descriptions_id join task_categories tc on tc.id = td.task_categories_id where tl.footprint_id = %s and tl.completed = true and tl.log is not null and decode(tl.log, 'base64') like %s order by tc.position_id, td.task_name"""
        sqlCategorySelected = """select tc.category, td.task_name, tl.log, tl.id from task_list tl join task_descriptions td on td.id = tl.task_descriptions_id join task_categories tc on tc.id = td.task_categories_id where  tl.footprint_id = %s and tl.completed = true and tl.log is not null and tc.category = %s and decode(tl.log, 'base64') like %s order by  tc.position_id, td.task_name"""
        sqlBothSelected = """select tc.category, td.task_name, tl.log, tl.id from task_list tl join task_descriptions td on td.id = tl.task_descriptions_id join task_categories tc on tc.id = td.task_categories_id where  tl.footprint_id = %s and tl.completed = true and tl.log is not null and tc.category = %s and td.task_name = %s and decode(tl.log, 'base64') like %s order by  tc.position_id, td.task_name"""
        cursor = self.db.cursor()

        if self.cmbLogsCategory.currentText() == "":
            cursor.execute(sqlNeitherSelected, (self.footprint_id, "%{}%".format(str(self.txtLogContains.text()))))
        elif self.cmbLogsCategory.currentText() != "" and self.cmbLogsTask.currentText() == "":
            cursor.execute(sqlCategorySelected, (self.footprint_id, str(self.cmbLogsCategory.currentText()), "%{}%".format(str(self.txtLogContains.text()))))
        else:
            cursor.execute(sqlBothSelected, (self.footprint_id, str(self.cmbLogsCategory.currentText()), str(self.cmbLogsTask.currentText()), "%{}%".format(str(self.txtLogContains.text()))))

        for row in cursor.fetchall():
            self.taskLogs.append([row[2], row[3]])
            self.tblTaskLogs.setRowCount(self.tblTaskLogs.rowCount() + 1)
            self.tblTaskLogs.setItem(self.tblTaskLogs.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblTaskLogs.setItem(self.tblTaskLogs.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblTaskLogs.setItem(self.tblTaskLogs.rowCount() - 1, 2, QTableWidgetItem(str(row[3])))
        self.tblTaskLogs.resizeColumnsToContents()
        cursor.close()

    task_log_index = -1

    @pyqtSignature("int, int, int, int")
    def on_tblTaskLogs_currentCellChanged(self, row, currentColumn, previousRow, previousColumn):
        try:
            clean = lambda dirty: ''.join(
                filter(string.printable.__contains__, dirty))
            self.txtTaskLog.setPlainText(
                clean(base64.b64decode(self.taskLogs[row][0])))
            self.task_log_index = row
        except:
            self.txtTaskLog.setPlainText("")

    website_ids = []

    def updateWebsites(self):
        self.tblWebsites.setRowCount(0)
        self.website_ids = []
        sql = "select hd.ip_address, hd.host_name, pd.port_number, w.html_title, w.id from host_data hd join port_data pd on hd.id = pd.host_data_id join websites w on w.port_data_id = pd.id where hd.footprint_id = %s and html_body != '' order by w.id"
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id, ))
        for row in cursor.fetchall():
            self.website_ids.append(row[4])
            self.tblWebsites.setRowCount(self.tblWebsites.rowCount() + 1)
            self.tblWebsites.setItem(
                self.tblWebsites.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblWebsites.setItem(
                self.tblWebsites.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblWebsites.setItem(
                self.tblWebsites.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
            self.tblWebsites.setItem(
                self.tblWebsites.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))

            item = QTableWidgetItem()
            item.setData(Qt.EditRole, int(row[4]))
            self.tblWebsites.setItem(self.tblWebsites.rowCount() - 1, 4, item)
        cursor.close()

    def updateDomainsSummary(self):
        self.tblDomains.setRowCount(0)
        sql = "select id, upper(domain_name) from domains where footprint_id = %s order by domain_name"
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id, ))
        for row in cursor.fetchall():
            self.tblDomains.setRowCount(self.tblDomains.rowCount() + 1)
            self.tblDomains.setItem(
                self.tblDomains.rowCount() - 1, 0, QTableWidgetItem(str(row[1])))

            c2 = self.db.cursor()
            sql2 = """select
                        count(distinct dc.username)
                    from
                        domain_credentials dc
                        join domain_credentials_map m on dc.id = m.domain_credentials_id and dc.footprint_id = m.footprint_id
                        join host_data hd on hd.id = m.host_data_id and hd.footprint_id = m.footprint_id
                    where
                        dc.cleartext_password != '' and
                        hd.is_dc = true and
                        m.valid = true and
                        hd.footprint_id = %s and
                        upper(hd.domain) = upper(%s::varchar)"""

            c2.execute(sql2, (self.footprint_id,  row[1], ))
            value = c2.fetchone()[0]
            c2.close()
            self.tblDomains.setItem(
                self.tblDomains.rowCount() - 1, 1, QTableWidgetItem(str(value)))

            c3 = self.db.cursor()
            sql3 = """select (
                        (select count(*) from domain_credentials where footprint_id = %s and ntlm_hash != '' and cleartext_password != '' and upper(domain) = upper(%s::varchar))::float /
                        (select count(*) from domain_credentials where footprint_id = %s and ntlm_hash != '' and upper(domain) = upper(%s::varchar))::float * 100)::int"""

            value = "0"
            try:
                c3.execute(sql3, (self.footprint_id, row[1], self.footprint_id, row[1], ))
                value = str(c3.fetchone()[0])
                
                #c3.close()
            except:
                # print "division by 0, so 0"
                pass
            finally:
                c3.close()
            
            self.tblDomains.setItem(self.tblDomains.rowCount() - 1, 2, QTableWidgetItem(str(value.split(".")[0].replace("None", "0""") + " %")))
        self.tblDomains.resizeColumnsToContents()
        cursor.close()

    def updatePortsSummary(self):
        self.tblOpenPortsSummary.setRowCount(0)
        sql = "select port_number, count(port_number) from host_data hd join port_data pd on hd.id = pd.host_data_id where footprint_id = %s group by port_number"
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id, ))
        for row in cursor.fetchall():
            self.tblOpenPortsSummary.setRowCount(
                self.tblOpenPortsSummary.rowCount() + 1)
            self.tblOpenPortsSummary.setItem(
                self.tblOpenPortsSummary.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblOpenPortsSummary.setItem(
                self.tblOpenPortsSummary.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
        cursor.close()

    def updateSummaryLabel(self):
        sql = """select
                (select count(*) from host_data where footprint_id = %s) as hosts,
                (select count(*) from host_data hd join port_data pd on hd.id = pd.host_data_id where hd.footprint_id = %s) as ports,
                (select count(*) from host_data hd join port_data pd on hd.id = pd.host_data_id join vulnerabilities v on pd.id = v.port_data_id where hd.footprint_id = %s) as vulns
        """
        cursor = self.db.cursor()
        cursor.execute(
            sql, (self.footprint_id, self.footprint_id, self.footprint_id, ))
        row = cursor.fetchone()
        self.lblSummaryLabel.setText(
            "Identified {0} hosts, {1} open ports, {2} shells".format(row[0], row[1],  row[2]))
        cursor.close()

    def updateCredsSummary(self):
        sql = """select 'Local Credentials' as label, (select count(distinct lc.username || lc.cleartext_password)  from local_credentials_map m join host_data hd on hd.id = m.host_data_id join local_credentials lc on lc.id = m.local_credentials_id where hd.footprint_id = %s and lc.cleartext_password != '' and m.valid = true) as count
                union select 'Domain Credentials' as label, (select count(distinct domain || username || cleartext_password) from domain_credentials where footprint_id = %s) as count
                union select 'Impersonation Tokens' as label, (select count(distinct t.token) from host_data hd join tokens t on hd.id = t.host_id where hd.footprint_id = %s) as count"""
        self.tblCredsSummary.setRowCount(0)
        cursor = self.db.cursor()
        cursor.execute(
            sql, (self.footprint_id, self.footprint_id, self.footprint_id, ))
        for row in cursor.fetchall():
            self.tblCredsSummary.setRowCount(
                self.tblCredsSummary.rowCount() + 1)
            self.tblCredsSummary.setItem(
                self.tblCredsSummary.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblCredsSummary.setItem(
                self.tblCredsSummary.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
        self.tblCredsSummary.resizeColumnsToContents()
        cursor.close()

    def updateVulnSummary(self):
        self.tblVulnsSummary.setRowCount(0)
        sql = "select vd.description, count(vd.description) from host_data hd join port_data pd on hd.id = pd.host_data_id join vulnerabilities v on v.port_data_id = pd.id join vulnerability_descriptions vd on vd.id = v.vulnerability_descriptions_id where hd.footprint_id = %s group by vd.description"
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id, ))
        for row in cursor.fetchall():
            self.tblVulnsSummary.setRowCount(
                self.tblVulnsSummary.rowCount() + 1)
            self.tblVulnsSummary.setItem(
                self.tblVulnsSummary.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblVulnsSummary.setItem(
                self.tblVulnsSummary.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
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
        sql = "select distinct net_range from net_ranges where footprint_id = %s order by net_range"
        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id, ))
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
            threading.Timer(self.updateSummaryInterval,
                            self.callUpdateSummaryTrigger).start()

    @pyqtSignature("int")
    def on_cbxUpdateSummary_stateChanged(self, p0):
        if p0:
            threading.Timer(self.updateSummaryInterval,
                            self.callUpdateSummaryTrigger).start()

    def clearHostData(self):
        self.lblComputerName.setText("")
        self.lblOS.setText("")
        self.lblArchitecture.setText("")
        self.lblLanguage.setText("")
        self.lblDomain.setText("")

        self.tblHostPorts.setRowCount(0)
        self.tblHostVulns.setRowCount(0)
        self.tblHostCredsSummary.setRowCount(0)
        self.tblLocalCreds.setRowCount(0)
        self.tblDomainCreds.setRowCount(0)
        self.tblAvailableTokens.setRowCount(0)
        self.tblExploitLogs.setRowCount(0)
        self.txtExploitLog.setText("")

    exploit_logs = []

    @pyqtSignature("QModelIndex")
    def on_tvHosts_clicked(self, index):
        self.clearHostData()
        node = index.model().itemFromIndex(index)

        if str(node.text()).find("0/24") != -1:
            net_range = str(node.text().replace("0/24", "%"))
            self.tblHostPorts.setRowCount(0)
            self.tblHostVulns.setRowCount(0)

            filterValue = self.cmbHostFilterField.currentText()
            sql = ""
            if filterValue == "":
                sql = """select ip_address, host_name
                         from host_data where footprint_id = %s and ip_address like %s order by 1"""
            elif filterValue == "IP Address":
                sql = """select ip_address, host_name
                         from host_data where footprint_id = %s and ip_address like %s and ip_address like %s order by 1"""
            elif filterValue == "Host Name":
                sql = """select ip_address, host_name
                         from host_data where footprint_id = %s and ip_address like %s and upper(host_name) like upper(%s) order by 1"""
            elif filterValue == "Port":
                sql = """select ip_address, host_name
                         from host_data hd join port_data pd on hd.id = pd.host_data_id where footprint_id = %s and ip_address like %s and port_number = ANY(%s) order by 1"""
            elif filterValue == "Domain":
                sql = """select ip_address, host_name
                         from host_data where footprint_id = %s and ip_address like %s and upper(domain) like upper(%s) order by 1"""

            for i in range(0, node.rowCount()):
                node.removeRow(0)
            cursor = self.db.cursor()
            #cursor.execute("select ip_address, host_name from host_data where ip_address like %s and footprint_id = %s order by ip_address", (str(net_range), self.footprint_id, ))

            if filterValue == "":
                cursor.execute(sql, (self.footprint_id, net_range, ))
            elif filterValue == "Port":
                ports = ""
                for port in self.txtHostFilterValue.text().split(","):
                    if self.is_int(port):
                        ports += port + ","
                ports = ports[:-1]

                cursor.execute(sql, (self.footprint_id, net_range, "{" + str(ports) + "}", ))
            else:
                cursor.execute(sql, (self.footprint_id, net_range, str("%" + self.txtHostFilterValue.text() + "%"), ))

            for row in cursor.fetchall():
                node.appendRow([QStandardItem(row[0]),  QStandardItem(row[1])])
            cursor.close()
        else:
            sql = "select computer_name, os, architecture, system_language, domain from host_data where ip_address = %s and footprint_id = %s"
            cursor = self.db.cursor()
            cursor.execute(sql, (str(node.text()), self.footprint_id, ))
            row = cursor.fetchone()
            self.lblComputerName.setText(row[0])
            self.lblOS.setText(row[1])
            self.lblArchitecture.setText(row[2])
            self.lblLanguage.setText(row[3])
            self.lblDomain.setText(row[4])
            cursor.close()

            sql = "select pd.port_number from host_data hd join port_data pd on hd.id = pd.host_data_id where hd.ip_address = %s and hd.footprint_id = %s order by pd.port_number"
            cursor = self.db.cursor()
            cursor.execute(sql, (str(node.text()), self.footprint_id, ))
            self.tblHostPorts.setRowCount(0)
            for row in cursor.fetchall():
                self.tblHostPorts.setRowCount(self.tblHostPorts.rowCount() + 1)
                self.tblHostPorts.setItem(
                    self.tblHostPorts.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblHostPorts.resizeColumnsToContents()
            cursor.close()

            sql = "select pd.port_number, vd.description from host_data hd join port_data pd on hd.id = pd.host_data_id join vulnerabilities v on v.port_data_id = pd.id join vulnerability_descriptions vd on vd.id = v.vulnerability_descriptions_id where hd.ip_address = %s and hd.footprint_id = %s"
            cursor = self.db.cursor()
            cursor.execute(sql, (str(node.text()), self.footprint_id, ))
            self.tblHostVulns.setRowCount(0)
            for row in cursor.fetchall():
                self.tblHostVulns.setRowCount(self.tblHostVulns.rowCount() + 1)
                self.tblHostVulns.setItem(
                    self.tblHostVulns.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
                self.tblHostVulns.setItem(
                    self.tblHostVulns.rowCount() - 1, 1, QTableWidgetItem(row[1]))
            self.tblHostVulns.resizeColumnsToContents()
            cursor.close()

            #sql = "select vd.description, el.log from host_data hd join port_data pd on hd.id = pd.host_data_id join vulnerabilities v on pd.id = v.port_data_id join vulnerability_descriptions vd on vd.id = v.vulnerability_descriptions_id join exploit_logs el on el.vulnerability_id = v.id where hd.ip_address = %s and hd.footprint_id = %s"
            sql = "select vd.description, el.log from host_data hd join exploit_logs el on hd.id = el.host_data_id join vulnerability_descriptions vd on vd.id = el.vulnerability_description_id where hd.ip_address = %s and hd.footprint_id = %s"
            cursor = self.db.cursor()
            cursor.execute(sql, (str(node.text()), self.footprint_id, ))
            self.tblExploitLogs.setRowCount(0)
            self.exploit_logs = []
            for row in cursor.fetchall():
                self.tblExploitLogs.setRowCount(
                    self.tblExploitLogs.rowCount() + 1)
                self.tblExploitLogs.setItem(
                    self.tblExploitLogs.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
                self.exploit_logs.append(row[1])
            self.tblExploitLogs.resizeColumnsToContents()
            cursor.close()

            sql = "select lc.username, lc.cleartext_password, lc.lm_hash, lc.ntlm_hash from host_data hd join local_credentials lc on hd.id = lc.host_data_id where hd.ip_address = %s and hd.footprint_id = %s order by lc.username"
            cursor = self.db.cursor()
            cursor.execute(sql, (str(node.text()), self.footprint_id, ))
            self.tblLocalCreds.setRowCount(0)
            for row in cursor.fetchall():
                self.tblLocalCreds.setRowCount(
                    self.tblLocalCreds.rowCount() + 1)
                self.tblLocalCreds.setItem(
                    self.tblLocalCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
                self.tblLocalCreds.setItem(
                    self.tblLocalCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
                self.tblLocalCreds.setItem(
                    self.tblLocalCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
                self.tblLocalCreds.setItem(
                    self.tblLocalCreds.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
            self.tblLocalCreds.resizeColumnsToContents()
            cursor.close()

            sql = """select 'Local Credentials' as label, (select count(distinct lc.username || lc.cleartext_password)  from local_credentials_map m join host_data hd on hd.id = m.host_data_id join local_credentials lc on lc.id = m.local_credentials_id where hd.footprint_id = %s and hd.ip_address = %s and lc.cleartext_password != '' and m.valid = true) as count
                    union select 'Domain Credentials' as label, (select count(*) from domain_credentials_map m join host_data hd on hd.id = m.host_data_id where hd.footprint_id = %s and hd.ip_address = %s and m.valid = true) as count
                    union select 'Impersonation Tokens' as label, (select count(t.token) from host_data hd join tokens t on hd.id = t.host_id where hd.footprint_id = %s and hd.ip_address = %s) as count"""
            cursor = self.db.cursor()
            cursor.execute(sql, (self.footprint_id, str(node.text()), self.footprint_id, str(
                node.text()), self.footprint_id, str(node.text()), ))
            self.tblHostCredsSummary.setRowCount(0)
            for row in cursor.fetchall():
                self.tblHostCredsSummary.setRowCount(
                    self.tblHostCredsSummary.rowCount() + 1)
                self.tblHostCredsSummary.setItem(
                    self.tblHostCredsSummary.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
                self.tblHostCredsSummary.setItem(
                    self.tblHostCredsSummary.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblHostCredsSummary.resizeColumnsToContents()
            cursor.close()

            sql = """select
                        t.token
                    from host_data hd join tokens t on hd.id = t.host_id
                    where hd.ip_address = %s and hd.footprint_id = %s
                    and t.token not like 'NT AUTHORITY%%'
                    and t.token not like 'NT SERVICE%%'
                    and t.token not like 'Window Manager%%'
                    and t.token not like 'IIS APPPOOL%%'
                    and t.token not like '%%$%%'
                    and t.token != 'error while running command. will try again'
                    order by t.token"""
            cursor = self.db.cursor()
            cursor.execute(sql, (str(node.text()), self.footprint_id, ))
            self.tblAvailableTokens.setRowCount(0)
            for row in cursor.fetchall():
                self.tblAvailableTokens.setRowCount(
                    self.tblAvailableTokens.rowCount() + 1)
                self.tblAvailableTokens.setItem(
                    self.tblAvailableTokens.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblAvailableTokens.resizeColumnsToContents()
            cursor.close()

            sql = "select dc.domain, dc.username, dc.cleartext_password from host_data hd join domain_credentials_map m on m.host_data_id = hd.id join domain_credentials dc on dc.id = m.domain_credentials_id where hd.footprint_id = %s and hd.ip_address = %s and m.valid = true"
            cursor = self.db.cursor()
            cursor.execute(sql, (self.footprint_id, str(node.text()), ))
            self.tblDomainCreds.setRowCount(0)
            for row in cursor.fetchall():
                self.tblDomainCreds.setRowCount(
                    self.tblDomainCreds.rowCount() + 1)
                self.tblDomainCreds.setItem(
                    self.tblDomainCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
                self.tblDomainCreds.setItem(
                    self.tblDomainCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
                self.tblDomainCreds.setItem(
                    self.tblDomainCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
            self.tblDomainCreds.resizeColumnsToContents()
            cursor.close()

    @pyqtSignature("int, int, int, int")
    def on_tblExploitLogs_currentCellChanged(self, row, currentColumn, previousRow, previousColumn):
        logtext = self.exploit_logs[row]
        clean = lambda dirty: ''.join(
            filter(string.printable.__contains__, dirty))
        self.txtExploitLog.setText(clean(base64.b64decode(logtext)))

    @pyqtSignature("int, int, int, int")
    def on_tblDomainGroups_currentCellChanged(self, row, currentColumn, previousRow, previousColumn):
        #        try:
        if True:
            domain = self.tblDomains_2.item(
                self.tblDomains_2.currentRow(), 0).text()
            domain_group = self.tblDomainGroups.item(
                self.tblDomainGroups.currentRow(), 0).text()

            self.tblDomainGroupUsers.setRowCount(0)
            cursor = self.db.cursor()
            cursor.execute("""select
            dc.username
            from domain_user_group_map m join domain_groups dg on dg.id = m.domain_group_id join domain_credentials dc on dc.id = m.domain_credentials_id join domains d on dg.domain_id = d.id
            where dg.footprint_id = %s and dg.group_name = %s and upper(d.domain_name) = upper(%s) order by dc.username""", (self.footprint_id, str(domain_group), str(domain), ))
            for row in cursor.fetchall():
                self.tblDomainGroupUsers.setRowCount(
                    self.tblDomainGroupUsers.rowCount() + 1)
                self.tblDomainGroupUsers.setItem(
                    self.tblDomainGroupUsers.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblDomainGroupUsers.resizeColumnsToContents()
            cursor.close()

            self.tblDomainSubGroups.setRowCount(0)
            cursor = self.db.cursor()
            cursor.execute("""select
                                            child.group_name
                                        from
                                            domains d
                                            join domain_groups parent on parent.domain_id = d.id
                                            join domain_sub_groups map on map.parent_group_id = parent.id
                                            join domain_groups child on map.child_group_id = child.id
                                        where
                                            d.footprint_id = %s and
                                            upper(d.domain_name) = upper(%s) and
                                            upper(parent.group_name) = upper(%s)""", (self.footprint_id, str(domain), str(domain_group), ))
            for row in cursor.fetchall():
                self.tblDomainSubGroups.setRowCount(
                    self.tblDomainSubGroups.rowCount() + 1)
                self.tblDomainSubGroups.setItem(
                    self.tblDomainSubGroups.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblDomainSubGroups.resizeColumnsToContents()
            cursor.close()


#        except:
#            pass

    @pyqtSignature("int, int, int, int")
    def on_tblDomains_2_currentCellChanged(self, row, currentColumn, previousRow, previousColumn):
        domain = ""
        try:
            domain = self.tblDomains_2.item(
                self.tblDomains_2.currentRow(), 0).text()
        except:
            domain = ""

        self.tblDomainGroupUsers.setRowCount(0)

        self.tblDomainControllers.setRowCount(0)
        cursor = self.db.cursor()
        cursor.execute("select hd.ip_address, hd.host_name from host_data hd where hd.footprint_id = %s and hd.is_dc = true and upper(hd.domain) = upper(%s) order by hd.ip_address",
                       (self.footprint_id, str(domain), ))
        for row in cursor.fetchall():
            self.tblDomainControllers.setRowCount(
                self.tblDomainControllers.rowCount() + 1)
            self.tblDomainControllers.setItem(
                self.tblDomainControllers.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblDomainControllers.setItem(
                self.tblDomainControllers.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
        self.tblDomainControllers.resizeColumnsToContents()
        cursor.close()

        self.tblDomainControllerCredMap.setRowCount(0)
        cursor = self.db.cursor()
        cursor.execute("select hd.ip_address, hd.host_name, dc.domain, dc.username, dc.cleartext_password from domain_credentials_map m join host_data hd on hd.id = m.host_data_id join domain_credentials dc on dc.id = m.domain_credentials_id where m.valid = true and hd.footprint_id = %s and upper(hd.domain) = upper(%s) and hd.is_dc = true order by hd.ip_address, dc.username", (self.footprint_id, str(domain), ))
        for row in cursor.fetchall():
            self.tblDomainControllerCredMap.setRowCount(
                self.tblDomainControllerCredMap.rowCount() + 1)
            self.tblDomainControllerCredMap.setItem(
                self.tblDomainControllerCredMap.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblDomainControllerCredMap.setItem(
                self.tblDomainControllerCredMap.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblDomainControllerCredMap.setItem(
                self.tblDomainControllerCredMap.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
            self.tblDomainControllerCredMap.setItem(
                self.tblDomainControllerCredMap.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
            self.tblDomainControllerCredMap.setItem(
                self.tblDomainControllerCredMap.rowCount() - 1, 4, QTableWidgetItem(str(row[4])))
        self.tblDomainControllerCredMap.resizeColumnsToContents()
        cursor.close()

        self.tblDomainGroups.setRowCount(0)
        cursor = self.db.cursor()
        cursor.execute("select distinct dg.group_name from domains d join domain_groups dg on d.id = dg.domain_id and d.footprint_id = dg.footprint_id join domain_user_group_map m on dg.id = m.domain_group_id  where d.footprint_id = %s and d.domain_name = %s order by dg.group_name", (self.footprint_id, str(domain), ))
        for row in cursor.fetchall():
            self.tblDomainGroups.setRowCount(
                self.tblDomainGroups.rowCount() + 1)
            self.tblDomainGroups.setItem(
                self.tblDomainGroups.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
        self.tblDomainGroups.resizeColumnsToContents()
        cursor.close()

    @pyqtSignature("int, int, int, int")
    def on_tblWebsites_currentCellChanged(self, row, currentColumn, previousRow, previousColumn):
        if row == -1:
            self.lblWebsitesScreenshot.clear()
        else:
            cursor = self.db.cursor()
            cursor.execute("select html_title, html_body, screenshot from websites where id = %s", (str(
                self.tblWebsites.item(row, 4).text()), ))
            row = cursor.fetchone()
            cursor.close()

            try:
                with open("temp/websites_website.jpg", 'w') as f:
                    f.write(base64.b64decode(row[2]))

                websitePixmap = QPixmap(QString.fromUtf8('temp/websites_website.jpg'))

                # websitePixmapScaledPixmap = websitePixmap.scaled(self.lblWebsitesScreenshot.size(),  Qt.KeepAspectRatio)
                # self.lblWebsitesScreenshot.setPixmap(websitePixmap.scaledToWidth(self.lblWebsitesScreenshot.width()))
                self.lblWebsitesScreenshot.setPixmap(websitePixmap)
            except:
                self.lblWebsitesScreenshot.clear()
            self.txtWebsiteHtml.setPlainText(row[1])

    def syncCredsWithPotFile(self):
        unknown_hashes_fn = "temp/" + ''.join(random.SystemRandom().choice(
            string.ascii_uppercase + string.digits) for _ in range(6))
        known_passwords_fn = "temp/" + ''.join(random.SystemRandom().choice(
            string.ascii_uppercase + string.digits) for _ in range(6))

        fh = open(known_passwords_fn, 'w')
        cursor = self.db.cursor()
        cursor.execute("""select cleartext_password from domain_credentials where footprint_id = %s and cleartext_password != "" """, (self.footprint_id, ))
        for row in cursor.fetchall():
            fh.write(row[0] + "\n")
        fh.close()
        cursor.close()

        fh = open(unknown_hashes_fn, 'w')
        cursor = self.db.cursor()
        # Including know password/hash combos will feed the john.pot file with
        # creds from memory, which might otherwise have been difficult to
        # recover
        cursor.execute("""select domain, username, ntlm_hash from domain_credentials where footprint_id = %s and ntlm_hash != "" """, (self.footprint_id, ))
        # cursor.execute("""select domain, username, ntlm_hash from domain_credentials where footprint_id = %s and cleartext_password = "" and ntlm_hash != "" """, (params.footprint_id, ))
        for row in cursor.fetchall():
            fh.write("{0}${1}:{2}\n".format(row[0], row[1], row[2]))
        fh.close()
        cursor.close()

        # add any new creds to the pot file
        os.popen("/home/dane/software/john/run/john {0} --format=nt --wordlist={1}".format(
            unknown_hashes_fn, known_passwords_fn))

        # import all creds from pot file
        for row in os.popen("/home/dane/software/john/run/john {0} --format=nt --show".format(unknown_hashes_fn)).read().split("\n"):
            if row != "":
                if row.find("password hashes cracked, ") == -1:
                    domain = row.split("$", 1)[0]
                    username = row.split("$", 1)[1].split(":", 1)[0]
                    password = row.split("$", 1)[1].split(":", 1)[1]

                    # print "found creds: domain:[{}] username:[{}]
                    # password:[{}]".format(domain, username, password)

                    if password != "":
                        try:
                            cursor = self.db.cursor()
                            cursor.execute("select addDomainCreds(%s, %s, %s, %s, %s, '', '')",  (
                                self.footprint_id, 0, domain, username, password, ))
                            cursor.close()
                        except:
                            pass
        self.updateCredsTrigger.emit()

    @pyqtSignature("")
    def on_btnSyncJohnPotFile_clicked(self):
        thread.start_new_thread(self.syncCredsWithPotFile, ())

    @pyqtSignature("")
    def on_btnUpdateCreds_clicked(self):
        sqlAllDomainCreds = "select distinct domain, username, cleartext_password, lm_hash, ntlm_hash from domain_credentials where footprint_id = %s order by domain, username"
        sqlValidDomainCreds = "select hd.ip_address, dc.domain, dc.username, dc.cleartext_password from domain_credentials_map m join host_data hd on hd.id = m.host_data_id join domain_credentials dc on dc.id = m.domain_credentials_id where hd.footprint_id = %s and m.valid = %s"
        sqlAllLocalCreds = "select distinct lc.username, lc.cleartext_password, lc.lm_hash, lc.ntlm_hash from local_credentials_map m join host_data hd on hd.id = m.host_data_id join local_credentials lc on lc.id = m.local_credentials_id where hd.footprint_id = %s and m.valid = true"
        sqlValidLocalCreds = "select hd.ip_address, lc.username, lc.cleartext_password, lc.lm_hash, lc.ntlm_hash, m.valid from local_credentials_map m join host_data hd on hd.id = m.host_data_id join local_credentials lc on lc.id = m.local_credentials_id where hd.footprint_id = %s and m.valid = %s"
        sqlTokens = """select distinct t.token from host_data hd join tokens t on hd.id = t.host_id where hd.footprint_id = %s
                    and t.token not like 'NT AUTHORITY%%'
                    and t.token not like 'NT SERVICE%%'
                    and t.token not like 'Window Manager%%'
                    and t.token not like 'IIS APPPOOL%%'
                    and t.token not like '%%$%%'
                    and t.token != 'error while running command. will try again'
                    order by token"""

        import datetime
        cursor = self.db.cursor()
        cursor.execute(sqlAllDomainCreds, (self.footprint_id, ))
        if True:
            # print "    A: " + str(datetime.datetime.now())
            self.tblAllDomainCreds.setRowCount(0)
            for row in cursor.fetchall():
                self.tblAllDomainCreds.setRowCount(self.tblAllDomainCreds.rowCount() + 1)
                self.tblAllDomainCreds.setItem(self.tblAllDomainCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
                self.tblAllDomainCreds.setItem(self.tblAllDomainCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
                self.tblAllDomainCreds.setItem(self.tblAllDomainCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
                self.tblAllDomainCreds.setItem(self.tblAllDomainCreds.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
                self.tblAllDomainCreds.setItem(self.tblAllDomainCreds.rowCount() - 1, 4, QTableWidgetItem(str(row[4])))
            self.tblAllDomainCreds.resizeColumnsToContents()

        cursor.close()

        cursor = self.db.cursor()
        cursor.execute(sqlValidDomainCreds, (self.footprint_id, "1", ))
        if True:
            #print "    B: " + str(datetime.datetime.now())
            self.tblValidDomainCreds.setRowCount(0)
            for row in cursor.fetchall():
                self.tblValidDomainCreds.setRowCount(self.tblValidDomainCreds.rowCount() + 1)
                self.tblValidDomainCreds.setItem(self.tblValidDomainCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
                self.tblValidDomainCreds.setItem(self.tblValidDomainCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
                self.tblValidDomainCreds.setItem(self.tblValidDomainCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
                self.tblValidDomainCreds.setItem(self.tblValidDomainCreds.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
            self.tblValidDomainCreds.resizeColumnsToContents()
        cursor.close()

        #cursor = self.db.cursor()
        #cursor.execute(sqlValidDomainCreds, (self.footprint_id, "0", ))
        #if True:
        #    print "    C: " + str(datetime.datetime.now())
        #    self.tblInvalidDomainCreds.setRowCount(0)
        #    for row in cursor.fetchall():
        #        self.tblInvalidDomainCreds.setRowCount(self.tblInvalidDomainCreds.rowCount() + 1)
        #        self.tblInvalidDomainCreds.setItem(self.tblInvalidDomainCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
        #        self.tblInvalidDomainCreds.setItem(self.tblInvalidDomainCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
        #        self.tblInvalidDomainCreds.setItem(self.tblInvalidDomainCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
        #        self.tblInvalidDomainCreds.setItem(self.tblInvalidDomainCreds.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
        #    #self.tblInvalidDomainCreds.resizeColumnsToContents()
        #cursor.close()

        cursor = self.db.cursor()
        cursor.execute(sqlAllLocalCreds, (self.footprint_id, ))
        if True:
            #print "    D: " + str(datetime.datetime.now())
            for row in cursor.fetchall():
                self.tblAllLocalCreds.setRowCount(self.tblAllLocalCreds.rowCount() + 1)

                self.tblAllLocalCreds.setItem(self.tblAllLocalCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
                self.tblAllLocalCreds.setItem(self.tblAllLocalCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
                self.tblAllLocalCreds.setItem(self.tblAllLocalCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
                self.tblAllLocalCreds.setItem(self.tblAllLocalCreds.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
            self.tblAllLocalCreds.resizeColumnsToContents()
        cursor.close()

        #cursor = self.db.cursor()
        #cursor.execute(sqlValidLocalCreds, (self.footprint_id, "1", ))
        #if True:
        #    print "    E: " + str(datetime.datetime.now())
        #    self.tblValidLocalCreds.setRowCount(0)
        #    for row in cursor.fetchall():
        #        self.tblValidLocalCreds.setRowCount(self.tblValidLocalCreds.rowCount() + 1)
        #        self.tblValidLocalCreds.setItem(self.tblValidLocalCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
        #        self.tblValidLocalCreds.setItem(self.tblValidLocalCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
        #        self.tblValidLocalCreds.setItem(self.tblValidLocalCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
        #        self.tblValidLocalCreds.setItem(self.tblValidLocalCreds.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
        #        self.tblValidLocalCreds.setItem(self.tblValidLocalCreds.rowCount() - 1, 4, QTableWidgetItem(str(row[4])))
        #    self.tblValidLocalCreds.resizeColumnsToContents()
        #cursor.close()

        #cursor = self.db.cursor()
        #cursor.execute(sqlValidLocalCreds, (self.footprint_id, "0", ))
        #if True:
        #    print "    F: " + str(datetime.datetime.now())
        #    self.tblInvalidLocalCreds.setRowCount(0)
        #    for row in cursor.fetchall():
        #        self.tblInvalidLocalCreds.setRowCount(self.tblInvalidLocalCreds.rowCount() + 1)
        #        self.tblInvalidLocalCreds.setItem(self.tblInvalidLocalCreds.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
        #        self.tblInvalidLocalCreds.setItem(self.tblInvalidLocalCreds.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
        #        self.tblInvalidLocalCreds.setItem(self.tblInvalidLocalCreds.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
        #    self.tblInvalidLocalCreds.resizeColumnsToContents()
        #cursor.close()

        cursor = self.db.cursor()
        cursor.execute(sqlTokens, (self.footprint_id, ))
        if True:
            # print "    G: " + str(datetime.datetime.now())
            self.tblTokens.setRowCount(0)
            for row in cursor.fetchall():
                self.tblTokens.setRowCount(self.tblTokens.rowCount() + 1)
                self.tblTokens.setItem(self.tblTokens.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblTokens.resizeColumnsToContents()
        cursor.close()

    @pyqtSignature("")
    def on_btnUpdateDomains_clicked(self):
        self.tblDomains_2.setRowCount(0)
        cursor = self.db.cursor()
        cursor.execute(
            "select domain_name from domains where footprint_id = %s order by domain_name", (self.footprint_id, ))
        for row in cursor.fetchall():
            self.tblDomains_2.setRowCount(self.tblDomains_2.rowCount() + 1)
            self.tblDomains_2.setItem(
                self.tblDomains_2.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
        self.tblDomains_2.resizeColumnsToContents()
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
        cursor.execute(sql, (self.footprint_id, ))
        for row in cursor.fetchall():
            print row[0]
            node = QStandardItem(row[0])
            self.tvVulnsModel.appendRow(node)
        cursor.close()

    @pyqtSignature("")
    def on_btnUpdateTaskList_clicked(self):
        sql = """
        select
            tc.category, td.task_name, count(td.task_name) as count
        from task_list tl
            join task_descriptions td on tl.task_descriptions_id = td.id
            join task_categories tc on tc.id = td.task_categories_id
        where tl.footprint_id = %s and
            td.enabled = true and tl.in_progress = %s and tl.completed = %s and td.is_recursive = false group by tc.category,td.task_name order by tc.category
        """

        sql2 = """
        select
            tc.category, td.task_name, count(td.task_name) as count
        from task_list tl
            join task_descriptions td on tl.task_descriptions_id = td.id
            join task_categories tc on tc.id = td.task_categories_id
        where tl.footprint_id = %s and
            td.enabled = true and tl.in_progress = %s and tl.completed = %s  group by tc.category,td.task_name order by tc.category
        """

        sqlEventless = """
            select 'Network Pivoting', 'Verify domain credentials', count(id) from domain_credentials where footprint_id = %s and cleartext_password != '' and verified = false
            union
            select 'Network Pivoting', 'Check domain credentials for remote access', count(*) from domain_credentials dc join host_data hd on hd.footprint_id = dc.footprint_id join port_data pd on pd.host_data_id = hd.id and pd.port_number = 445 and (hd.id, dc.id) not in (select host_data_id, domain_credentials_id from domain_credentials_map) where dc.valid = true and hd.footprint_id = %s
            union
            select 'Domain Enumeration', 'Gather domain users', count(*) from domain_groups  where footprint_id = %s and users_gathered = false
        """

        cursor = self.db.cursor()
        cursor.execute(sql, (self.footprint_id, False, False, ))
        self.tblTaskListPending.setRowCount(0)
        for row in cursor.fetchall():
            self.tblTaskListPending.setRowCount(self.tblTaskListPending.rowCount() + 1)
            self.tblTaskListPending.setItem(self.tblTaskListPending.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblTaskListPending.setItem(self.tblTaskListPending.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblTaskListPending.setItem(self.tblTaskListPending.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
        self.tblTaskListPending.resizeColumnsToContents()
        cursor.close()

        cursor = self.db.cursor()
        cursor.execute(sqlEventless, (self.footprint_id, self.footprint_id, self.footprint_id, ))
        self.tblTaskListPending_2.setRowCount(0)
        for row in cursor.fetchall():
            self.tblTaskListPending_2.setRowCount(
                self.tblTaskListPending_2.rowCount() + 1)
            self.tblTaskListPending_2.setItem(
                self.tblTaskListPending_2.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblTaskListPending_2.setItem(
                self.tblTaskListPending_2.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblTaskListPending_2.setItem(
                self.tblTaskListPending_2.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
        self.tblTaskListPending_2.resizeColumnsToContents()
        cursor.close()

        cursor = self.db.cursor()
        cursor.execute(sql2, (self.footprint_id, True, False, ))
        self.tblTaskListInProgress.setRowCount(0)
        for row in cursor.fetchall():
            self.tblTaskListInProgress.setRowCount(
                self.tblTaskListInProgress.rowCount() + 1)
            self.tblTaskListInProgress.setItem(
                self.tblTaskListInProgress.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblTaskListInProgress.setItem(
                self.tblTaskListInProgress.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblTaskListInProgress.setItem(
                self.tblTaskListInProgress.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
        self.tblTaskListInProgress.resizeColumnsToContents()
        cursor.close()

        cursor = self.db.cursor()
        cursor.execute(sql2, (self.footprint_id, False, True, ))
        self.tblTaskListDone.setRowCount(0)
        for row in cursor.fetchall():
            self.tblTaskListDone.setRowCount(
                self.tblTaskListDone.rowCount() + 1)
            self.tblTaskListDone.setItem(
                self.tblTaskListDone.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblTaskListDone.setItem(
                self.tblTaskListDone.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblTaskListDone.setItem(
                self.tblTaskListDone.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
        self.tblTaskListDone.resizeColumnsToContents()
        cursor.close()

        if self.cbxUpdateTaskList.isChecked() == True:
            threading.Timer(self.updateTaskListInterval,
                            self.callUpdateTaskListTrigger).start()

    @pyqtSignature("int")
    def on_cbxUpdateTaskList_stateChanged(self, p0):
        if p0:
            threading.Timer(self.updateTaskListInterval,
                            self.callUpdateTaskListTrigger).start()

    @pyqtSignature("int")
    def on_checkBox_stateChanged(self, p0):
        self.frame.setVisible(p0)

    @pyqtSignature("int")
    def on_cbxTaskLogsFilterVisible_stateChanged(self, p0):
        self.frameLogFilter.setVisible(p0)

    @pyqtSignature("int")
    def on_cbxHostsFilterVisible_stateChanged(self, p0):
        self.frameHostsFilter.setVisible(p0)

    @pyqtSignature("")
    def on_btnStopWorkers_clicked(self):
        for wt in self.workerThreads:
            try:
                wt.stop()
            except:
                pass

    @pyqtSignature("")
    def on_btnRefreshVulnerabilitiesTab_clicked(self):
        currentValue = self.cmbVulnerabilities.currentText()

        self.cmbVulnerabilities.clear()
        vulns = [""]

        cursor = self.db.cursor()
        cursor.execute("""  select
                                            distinct vd.description
                                        from
                                            host_data hd
                                            join port_data pd on hd.id = pd.host_data_id
                                            join vulnerabilities v on v.port_data_id = pd.id
                                            join vulnerability_descriptions vd on vd.id = v.vulnerability_descriptions_id
                                        where
                                            hd.footprint_id = %s
                                        order by
                                            vd.description""",  (self.footprint_id, ))

        for r in cursor.fetchall():
            vulns.append(r[0])

        self.cmbVulnerabilities.addItems(vulns)
        self.cmbVulnerabilities.setCurrentIndex(
            self.cmbVulnerabilities.findText(currentValue, Qt.MatchExactly))

    @pyqtSignature("QString")
    def on_cmbVulnerabilities_currentIndexChanged(self, p0):
        self.tblVulnerableHosts.setRowCount(0)
        cursor = self.db.cursor()
        cursor.execute("""  select
                                            hd.ip_address, hd.host_name, pd.port_number, vd.description, v.details
                                        from
                                            host_data hd
                                            join port_data pd on hd.id = pd.host_data_id
                                            join vulnerabilities v on v.port_data_id = pd.id
                                            join vulnerability_descriptions vd on vd.id = v.vulnerability_descriptions_id
                                        where
                                            hd.footprint_id = %s and
                                            vd.description = %s
                                        order by
                                            hd.ip_address""", (self.footprint_id, str(self.cmbVulnerabilities.currentText()), ))

        for row in cursor.fetchall():
            self.tblVulnerableHosts.setRowCount(
                self.tblVulnerableHosts.rowCount() + 1)
            self.tblVulnerableHosts.setItem(
                self.tblVulnerableHosts.rowCount() - 1, 0, QTableWidgetItem(str(row[0])))
            self.tblVulnerableHosts.setItem(
                self.tblVulnerableHosts.rowCount() - 1, 1, QTableWidgetItem(str(row[1])))
            self.tblVulnerableHosts.setItem(
                self.tblVulnerableHosts.rowCount() - 1, 2, QTableWidgetItem(str(row[2])))
            self.tblVulnerableHosts.setItem(
                self.tblVulnerableHosts.rowCount() - 1, 3, QTableWidgetItem(str(row[3])))
            self.tblVulnerableHosts.setItem(
                self.tblVulnerableHosts.rowCount() - 1, 4, QTableWidgetItem(str(row[4])))
        self.tblVulnerableHosts.resizeColumnsToContents()

        cursor.close()

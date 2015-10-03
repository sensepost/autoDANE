# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from Ui_mainwindow import Ui_MainWindow
from adddomain import AddDomainDialog
from adddomaincreds import AddDomainCredsDialog
from addhost import addhost
from choosefootprint import ChooseFootprintDialog, footprintOptions

import dbfunctions
import footprintfunctions
import thread
import multiprocessing

import ConfigParser
import time
import threads
import threading
import MySQLdb
import sys
import os
import glib

class MainWindow(QMainWindow, Ui_MainWindow):
    class CaptureOutput():
        tblLog = None
        def __init__(self, _tblLog):
            self.tblLog = _tblLog
            
        def write(self, message):
            if message == "\n":
                return
                
            row = self.tblLog.rowCount()
            self.tblLog.setRowCount(row + 1)
            
            self.tblLog.setItem(row, 0, QTableWidgetItem(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())))
            self.tblLog.setItem(row, 1, QTableWidgetItem(message))
            self.tblLog.resizeColumnsToContents()
            
    footprintID = None
    footprintName = None
    doWork = None
    options = None
    db = None
    
    tvHostsModel = None
    tvVulnsModel = None
    
    updateUiTrigger = pyqtSignal()
    updateUiInterval = 1
    
    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        
        self.updateUiTrigger.connect(self.handleUpdateUiTrigger)
        
        #self.tblLog.setRowCount(0)
        
    def callUpdateUiTrigger(self):
        self.updateUiTrigger.emit()
        
    def handleUpdateUiTrigger(self):
        self.updateUI()
        
    def initHostsTreeview(self):
        view = self.tvHosts
        view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tvHostsModel = QStandardItemModel()
        self.tvHostsModel.setHorizontalHeaderLabels(['Host',  'Name'])
        view.setModel(self.tvHostsModel)
        view.setUniformRowHeights(True)
        
    def initVulnsTreeview(self):
        view = self.tvVulns
        view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tvVulnsModel = QStandardItemModel()
        self.tvVulnsModel.setHorizontalHeaderLabels(['Host',  'Name',  'Port',  'Vuln',  'Notes'])
        view.setModel(self.tvVulnsModel)
        view.setUniformRowHeights(True)
     
    def setFootprintInfo(self, _db,  _footprintID,  _footprintName,  _doWork,  _footprintOptions):
        self.db = _db
        self.footprintID = _footprintID 
        self.footprintName = _footprintName
        self.doWork = _doWork
        self.options = _footprintOptions
        
        dbfunctions.setMsfPass(self.db,  self.footprintID,  "")
        
    def start(self):
        self.updateUI()
        
        if self.doWork:
            if self.options.addLocalResolverHosts:
                threads.addLocalResolverHosts(self.footprintID)
                #thread.start_new_thread(threads.addLocalResolverHosts,  (self.footprintID,  ))
            
            if self.options.startMetasploit:
                thread.start_new_thread(threads.startMetasploit,  (self.footprintID,  ))
          
            if self.options.dnsQueriesOnKnownHosts:
                thread.start_new_thread(threads.doDNSLookupsOnKnownHosts,  (self.footprintID,  ))
                
            if self.options.runDnsQueriesOnKnownRanges:
                thread.start_new_thread(threads.doDNSLookupsOnKnownRanges,  (self.footprintID,  ))
            
            if self.options.hostPortScanner:
                thread.start_new_thread(threads.portScanner,  (self.footprintID,  ))
            
            if self.options.netRangePortScanner:
                thread.start_new_thread(threads.rangePortScanner,  (self.footprintID,  ))
            
            if self.options.zoneTransferDomains:
                thread.start_new_thread(threads.zoneTransferDomains,  (self.footprintID,  ))
            
            if self.options.vulnScanner:
                threads.vulnScanner(self.footprintID)
            
            #TODO: pass and read options param
            if self.options.startMetasploit and (self.options.exploitMs08067 or self.options.expoitWeakMsSqlCreds or self.options.exploitWeakTomcatCreds or self.options.credPivot):
                thread.start_new_thread(threads.vulnExploiter,  (self.footprintID,  self.options,  ))
            
            #thread.start_new_thread(threads.credCollector,  (self.footprintID,  ))
            
            #if os.geteuid() > 0:
            #    print "you need to run as root if you want to listen to network broadcasts"
            #else:
            #    cmda = 'nmap --script broadcast-ataoe-discover,broadcast-bjnp-discover,broadcast-db2-discover,broadcast-dhcp6-discover,broadcast-dhcp-discover,broadcast-dns-service-discovery,broadcast-dropbox-listener,broadcast-eigrp-discovery,broadcast-igmp-discovery,broadcast-listener,broadcast-ms-sql-discover,broadcast-netbios-master-browser,broadcast-networker-discover,broadcast-novell-locate,broadcast-pc-anywhere,broadcast-pc-duo,broadcast-pim-discovery,broadcast-ping,broadcast-pppoe-discover,broadcast-rip-discover,broadcast-ripng-discover,broadcast-sybase-asa-discover,broadcast-tellstick-discover,broadcast-upnp-info,broadcast-versant-locate,broadcast-wake-on-lan,broadcast-wpad-discover,broadcast-wsdd-discover,broadcast-xdmcp-discover --script-args timeout=12 | grep -oE "\\b([0-9]{1,3}\.){3}[0-9]{1,3}\\b" | sort -u'
            #    cmdb = 'nmap -sU -p 137,5353,1900 --script broadcast-dns-service-discovery,dns-service-discovery,nbstat,upnp-info,broadcast-listener --script-args timeout=30 | grep -oE "\\b([0-9]{1,3}\.){3}[0-9]{1,3}\\b" | sort -u'
            #    cmdc = 'nmap -sU -p 67,161,123,137,177,502,5353,1900,8611,8612,523 --script nbstat,dns-service-discovery,upnp-info,bjnp-discover,dhcp-discover,lltd-discovery,modbus-discover,smb-os-discovery,wsdd-discover,xdmcp-discover,broadcast-listener --script-args timeout=30 | grep -oE "\\b([0-9]{1,3}\.){3}[0-9]{1,3}\\b" | sort -u'

                #thread.start_new_thread(threads.listenToBroadcasts,  (self.footprintID,  cmda,  ))
                #thread.start_new_thread(threads.listenToBroadcasts,  (self.footprintID,  cmdb,  ))
                #thread.start_new_thread(threads.listenToBroadcasts,  (self.footprintID,  cmdc,  ))
            
            if self.options.dnsQueries10Range:
                thread.start_new_thread(threads.enumerateHosts_10,  (self.footprintID,  ))
            if self.options.dnsQueries172Range:
                thread.start_new_thread(threads.enumerateHosts_172,  (self.footprintID,  ))
            if self.options.dnsQueries192Range:
                thread.start_new_thread(threads.enumerateHosts_192,  (self.footprintID,  ))
                
    def updateHostsTreeview(self):
        cursorRanges = self.db.cursor()
        cursorRanges.execute('select net_range from ranges where footprint_id = %s', (self.footprintID))
        
        for range in cursorRanges.fetchall():
            node = QStandardItem(range[0])
            
            cursorHosts = self.db.cursor()
            cursorHosts.execute("select ip_address, host_name from host_data where footprint_id = %s and ip_address like %s order by ip_address",  (self.footprintID,  format(range[0][:-4] + "%")))
            for host in cursorHosts.fetchall():
                ipItem = QStandardItem(host[0])
                hostItem = QStandardItem(host[1])
                
                #ipItem.appendRow([QStandardItem(""),  QStandardItem(""),  QStandardItem("21")])
                
                
                node.appendRow([ipItem,  hostItem])
                
            cursorHosts.close()
            
            self.tvHostsModel.appendRow(node)
        cursorRanges.close()

    
    def updateVulnsTreeview(self):
        cursorRanges = self.db.cursor()
        cursorRanges.execute('select net_range, (select count(*) from host_data h join ports p on h.id = p.host_data_id where h.footprint_id = %s and h.ip_address like concat(left(net_range, length(net_range)-4), %s) and p.vulnerable = 1) as count from ranges having count > 0', (self.footprintID,  "%"))                 #
        
        for range in cursorRanges.fetchall():
            node = QStandardItem(range[0])
            
            cursorHosts = self.db.cursor()
            cursorHosts.execute("select h.ip_address, h.host_name, p.port_num, p.vulnerability_name, p.notes from host_data h join ports p on h.id = p.host_data_id where h.footprint_id = %s and p.vulnerable = 1 and h.ip_address like %s",  (self.footprintID,  format(range[0][:-4] + "%")))
            for host in cursorHosts.fetchall():
                node.appendRow( [ QStandardItem(host[0]),  QStandardItem(host[1]),  QStandardItem(str(host[2])),  QStandardItem(host[3]),  QStandardItem(host[4]) ] )
                
            cursorHosts.close()
            
            self.tvVulnsModel.appendRow(node)
        cursorRanges.close()
        
    def updateDomainCredsTable(self):
        cursor = self.db.cursor()
        cursor.execute('select domain_name, is_da, username, cleartext_password, lm_hash, ntlm_hash, http_ntlm_hash from domain_creds where footprint_id = %s',  (self.footprintID))
        
        self.tblDomainCreds.setRowCount(0)
        
        for creds in cursor.fetchall():
            row = self.tblDomainCreds.rowCount()
            self.tblDomainCreds.setRowCount(row + 1)
            
            self.tblDomainCreds.setItem(row, 0, QTableWidgetItem(creds[0]))
            if creds[1] == 1:
                self.tblDomainCreds.setItem(row, 1, QTableWidgetItem("Y"))
            else:
                self.tblDomainCreds.setItem(row, 1, QTableWidgetItem("N"))
            
            self.tblDomainCreds.setItem(row, 2, QTableWidgetItem(creds[2]))
            self.tblDomainCreds.setItem(row, 3, QTableWidgetItem(creds[3]))
            self.tblDomainCreds.setItem(row, 4,  QTableWidgetItem(creds[4]))
            self.tblDomainCreds.setItem(row, 5, QTableWidgetItem(creds[5]))
            self.tblDomainCreds.setItem(row, 6, QTableWidgetItem(creds[6]))
        cursor.close()
        self.tblDomainCreds.resizeColumnsToContents()

    def updateSummaryLabel(self):
        cursor = self.db.cursor()
        cursor.execute('select (select count(*) from host_data where footprint_id = %s) as "hosts", (select count(*) from ports where host_data_id in (select id from host_data where footprint_id = %s)) as "ports", (select count(*) from ports where host_data_id in (select id from host_data where footprint_id = %s) and shell = 1) as "shells"',  (self.footprintID,  self.footprintID,  self.footprintID))
        
        row = cursor.fetchone()
        self.lblSummary.setText("Identified {0} hosts, {1} open ports, {2} shells".format(row[0],  row[1],  row[2]))
        
        cursor.close() 

    def updatePortsSummaryTable(self):
        cursor = self.db.cursor()
        cursor.execute('select port_num, count(port_num) from ports where host_data_id in (select id from host_data where footprint_id = %s) group by port_num',  (self.footprintID))
        
        self.tblPortsSummary.setRowCount(0)
        
        for port in cursor.fetchall():
            row = self.tblPortsSummary.rowCount()
            self.tblPortsSummary.setRowCount(row + 1)
            
            self.tblPortsSummary.setItem(row, 0, QTableWidgetItem(str(port[0])))
            self.tblPortsSummary.setItem(row, 1, QTableWidgetItem(str(port[1])))
            
        cursor.close() 
        self.tblPortsSummary.resizeColumnsToContents()

    def updateVulnsSummaryTable(self):
        cursor = self.db.cursor()
        cursor.execute('select vulnerability_name, count(vulnerability_name) as "count" from ports where host_data_id in (select id from host_data where footprint_id = %s) and vulnerable = 1 group by vulnerability_name',  (self.footprintID))
        
        self.tblVulnsSummary.setRowCount(0)
        
        for vuln in cursor.fetchall():
            row = self.tblVulnsSummary.rowCount()
            self.tblVulnsSummary.setRowCount(row + 1)
            
            self.tblVulnsSummary.setItem(row, 0, QTableWidgetItem(vuln[0]))
            self.tblVulnsSummary.setItem(row, 1, QTableWidgetItem(str(vuln[1])))
            
        cursor.close()
        self.tblVulnsSummary.resizeColumnsToContents()
        
    def updateDomainsSummaryTable(self):
        cursor = self.db.cursor()
        cursor.execute('select domain_name from domains where footprint_id = %s',  (self.footprintID))
        
        self.tblDomains.setRowCount(0)
        
        for item in cursor.fetchall():
            row = self.tblDomains.rowCount()
            self.tblDomains.setRowCount(row + 1)
            
            self.tblDomains.setItem(row, 0, QTableWidgetItem(item[0]))
            
        cursor.close() 
        self.tblDomains.resizeColumnsToContents()

    def updateWebServersTable(self):
        cursor = self.db.cursor()
        cursor.execute('select hd.ip_address, hd.host_name, p.port_num, p.http_title from host_data hd join ports p on hd.id = p.host_data_id where hd.footprint_id = %s and p.http_title_checked = 1',  (self.footprintID))
        #cursor.execute('select hd.ip_address, hd.host_name, p.port_num, p.http_title from host_data hd join ports p on hd.id = p.host_data_id where hd.footprint_id = %s and p.http_title != ""',  (self.footprintID))
        
        self.tblWebServers.setRowCount(0)
        
        for item in cursor.fetchall():
            row = self.tblWebServers.rowCount()
            self.tblWebServers.setRowCount(row + 1)
            
            url = "http"
            if item[2] in [443,  8443]:
                url = url + "s"
            url = url + "://{0}:{1}".format(item[0],  item[2])
            
            self.tblWebServers.setItem(row, 0, QTableWidgetItem(item[0]))
            self.tblWebServers.setItem(row, 1, QTableWidgetItem(item[1]))
            self.tblWebServers.setItem(row, 2, QTableWidgetItem(str(item[2])))
            self.tblWebServers.setItem(row, 3, QTableWidgetItem(url))
            self.tblWebServers.setItem(row, 4, QTableWidgetItem(item[3]))
            
        cursor.close()
        self.tblWebServers.resizeColumnsToContents()
        
    def updateDomainsSummaryTable(self):
        cursor = self.db.cursor()
        cursor.execute('select domain_name from domains where footprint_id = %s',  (self.footprintID))
        
        self.tblDomains.setRowCount(0)
        
        for item in cursor.fetchall():
            row = self.tblDomains.rowCount()
            self.tblDomains.setRowCount(row + 1)
            
            self.tblDomains.setItem(row, 0, QTableWidgetItem(item[0]))
            
        cursor.close() 
        self.tblDomains.resizeColumnsToContents()
        
    def updatePendingFootprinting(self):
        cursor = self.db.cursor()
        cursor.execute('call report_pendingFootprinting(%s)',  (self.footprintID))
        
        self.tblPendingFootprinting.setRowCount(0)
        
        for item in cursor.fetchall():
            row = self.tblPendingFootprinting.rowCount()
            self.tblPendingFootprinting.setRowCount(row + 1)
            
            self.tblPendingFootprinting.setItem(row, 0, QTableWidgetItem(item[0]))
            self.tblPendingFootprinting.setItem(row, 1, QTableWidgetItem(str(item[1])))
            
        cursor.close() 
        self.tblPendingFootprinting.resizeColumnsToContents()

    def updatePendingVulnScanning(self):
        cursor = self.db.cursor()
        cursor.execute('call report_pendingVulnScanning(%s)',  (self.footprintID))
        
        self.tblPendingVulnScanning.setRowCount(0)
        
        for item in cursor.fetchall():
            row = self.tblPendingVulnScanning.rowCount()
            self.tblPendingVulnScanning.setRowCount(row + 1)
            
            self.tblPendingVulnScanning.setItem(row, 0, QTableWidgetItem(str(item[0])))
            self.tblPendingVulnScanning.setItem(row, 1, QTableWidgetItem(str(item[1])))
            
        cursor.close() 
        self.tblPendingVulnScanning.resizeColumnsToContents()

    def updateCredMap(self):
        cursor = self.db.cursor()
        cursor.execute('select hd.ip_address, hd.host_name, dc.domain_name, dc.username, dc.cleartext_password, m.successful from cred_host_map m join host_data hd on m.host_data_id = hd.id join domain_creds dc on m.domain_creds_id = dc.id where hd.footprint_id = %s and m.successful = 1',  (self.footprintID))
        
        self.tblValidCreds.setRowCount(0)
        
        for item in cursor.fetchall():
            row = self.tblValidCreds.rowCount()
            self.tblValidCreds.setRowCount(row + 1)
            
            self.tblValidCreds.setItem(row, 0, QTableWidgetItem(str(item[0])))
            self.tblValidCreds.setItem(row, 1, QTableWidgetItem(str(item[1])))
            self.tblValidCreds.setItem(row, 2, QTableWidgetItem(str(item[2])))
            self.tblValidCreds.setItem(row, 3, QTableWidgetItem(str(item[3])))
            self.tblValidCreds.setItem(row, 4, QTableWidgetItem(str(item[4])))
            
        cursor.close() 
        self.tblValidCreds.resizeColumnsToContents()
        
        cursor = self.db.cursor()
        cursor.execute('select hd.ip_address, hd.host_name, dc.domain_name, dc.username, dc.cleartext_password, m.successful from cred_host_map m join host_data hd on m.host_data_id = hd.id join domain_creds dc on m.domain_creds_id = dc.id where hd.footprint_id = %s and m.successful = 0',  (self.footprintID))
        
        self.tblInvalidCreds.setRowCount(0)
        
        for item in cursor.fetchall():
            row = self.tblInvalidCreds.rowCount()
            self.tblInvalidCreds.setRowCount(row + 1)
            
            self.tblInvalidCreds.setItem(row, 0, QTableWidgetItem(str(item[0])))
            self.tblInvalidCreds.setItem(row, 1, QTableWidgetItem(str(item[1])))
            self.tblInvalidCreds.setItem(row, 2, QTableWidgetItem(str(item[2])))
            self.tblInvalidCreds.setItem(row, 3, QTableWidgetItem(str(item[3])))
            self.tblInvalidCreds.setItem(row, 4, QTableWidgetItem(str(item[4])))
            
        cursor.close() 
        self.tblInvalidCreds.resizeColumnsToContents()
        
    def updateUI(self):
        #print "updateUI() called from thread [{0}]".format(threading.current_thread().name)
        self.initHostsTreeview()
        self.updateHostsTreeview()
        
        self.initVulnsTreeview()
        self.updateVulnsTreeview()
        
        self.updateDomainCredsTable()
        
        self.updatePortsSummaryTable()
        self.updateVulnsSummaryTable()
        self.updateDomainsSummaryTable()
        self.updateWebServersTable()
        self.updateSummaryLabel()
        self.updatePendingFootprinting()
        self.updatePendingVulnScanning()
        self.updateCredMap()
        
        if self.cbxUpdateUI.isChecked() == True:
            threading.Timer(self.updateUiInterval, self.callUpdateUiTrigger).start()

    @pyqtSignature("int")
    def on_cbxUpdateUI_stateChanged(self, p0):
        if p0:
            threading.Timer(self.updateUiInterval, self.callUpdateUiTrigger).start()
    
    @pyqtSignature("")
    def on_btnUpdateUI_clicked(self):
        self.updateUI()
        #threading.Timer(self.updateUiInterval, self.callUpdateUiTrigger).start()
    
    @pyqtSignature("")
    def on_btnAddHost_clicked(self):
        addHostWnd = addhost()
        if addHostWnd.exec_():
            dbfunctions.addIP(self.db,  self.footprintID,  addHostWnd.getResult(),  False)
            self.updateUI()
    
    @pyqtSignature("")
    def on_btnAddDomain_clicked(self):
        addDomainWnd = AddDomainDialog()
        if addDomainWnd.exec_():
            dbfunctions.addDomain(self.db,  self.footprintID,  addDomainWnd.getResult())
            self.updateUI()
            
    @pyqtSignature("")
    def on_btnAddDomainCreds_clicked(self):
        addDomainCredsWnd = AddDomainCredsDialog()
        if addDomainCredsWnd.exec_():
            res = addDomainCredsWnd.getResult()
            dbfunctions.addDomainCreds(self.db,  self.footprintID,  res[0],  res[1],  res[2],  "",  "",  "")
            self.updateUI()

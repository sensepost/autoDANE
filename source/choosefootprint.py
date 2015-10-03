# -*- coding: utf-8 -*-

from PyQt4.QtGui import QDialog, QMessageBox
from PyQt4.QtCore import pyqtSignature

from Ui_choosefootprint import Ui_Dialog

class footprintOptions():
    addLocalResolverHosts = False
    zoneTransferDomains = False
    netRangePortScanner = False
    runDnsQueriesOnKnownRanges = False
    dnsQueries10Range = False
    dnsQueries172Range = False
    dnsQueries192Range = False
    dnsQueriesOnKnownHosts = False
    hostPortScanner = False
    vulnScanner = False
    startMetasploit = False
    exploitMs08067 = False
    expoitWeakMsSqlCreds = False
    exploitWeakTomcatCreds = False
    credPivot = False
    
class ChooseFootprintDialog(QDialog, Ui_Dialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
    
    def setFootprints(self, _footprints):
        self.cmbFootprints.addItems(_footprints)
    
    def getResults(self):
        options = footprintOptions
        options.addLocalResolverHosts = self.cbxAddLocalResolverHosts.isChecked()
        options.zoneTransferDomains = self.cbxZoneTransferDomains.isChecked()
        options.netRangePortScanner = self.cbxNetRangePortScanner.isChecked()
        options.runDnsQueriesOnKnownRanges = self.cbxDnsQueryKnownRanges.isChecked()
        options.dnsQueries10Range = self.cbxDnsQuery10range.isChecked()
        options.dnsQueries172Range = self.cbxDnsQuery172range.isChecked()
        options.dnsQueries192Range = self.cbxDnsQuery192range.isChecked()
        options.dnsQueriesOnKnownHosts = self.cbxDnsQueriesOnKnownHosts.isChecked()
        options.hostPortScanner = self.cbxHostPortScanner.isChecked()
        options.vulnScanner = self.cbxVulnScanner.isChecked()
        options.startMetasploit = self.cbxStartMetasploit.isChecked()
        options.exploitMs08067 = self.cbxExploitMs08067.isChecked()
        options.expoitWeakMsSqlCreds = self.cbxExploitWeakMsSqlCreds.isChecked()
        options.exploitWeakTomcatCreds = self.cbxExploitWeakTomcatCreds.isChecked()
        options.credPivot = self.cbxCredPivot.isChecked()
        
        return [self.txtFootprintName.text(),  self.cbxDoWork.isChecked(),  options]
        
    @pyqtSignature("")
    def on_btnCancel_clicked(self):
        self.reject()
    
    @pyqtSignature("")
    def on_btnOK_clicked(self):
        if self.txtFootprintName.text() == "":
            QMessageBox.information(self, "Information", "You need to choose a name")
        else:
            self.accept()
    
    @pyqtSignature("QString")
    def on_cmbFootprints_currentIndexChanged(self, p0):
        if p0 != "":
            self.txtFootprintName.setText(p0)
    
    @pyqtSignature("QString")
    def on_txtFootprintName_textEdited(self, p0):
        self.cmbFootprints.setCurrentIndex(0)

#!/usr/bin/python

from PyQt4 import *
from PyQt4.QtCore import *
from PyQt4.QtGui import QApplication

from splash.dbconnecting import DBConnecting
from initialoptions.choosefootprint import ChooseFootprint
from main.mainwindow import MainWindow

import sys
import os
import MySQLdb
import ConfigParser
import thread

def main():
    app = QApplication(sys.argv)
    #app.setStyle("cleanlooks")
    #plastique
    #cde
    #motif
    #sgi
    #windows
    #cleanlooks
    #mac

    wndDBConnecting = DBConnecting()
    wndChooseFootprint = ChooseFootprint()
    wndMainWindow = MainWindow()

    conf = ConfigParser.ConfigParser()
    conf.read("settings.ini")
        
    showSplash = False
    runApp = True
    
    try:
        MySQLdb.connect(host=conf.get('MySQL',  'host'), user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
        showSplash = False
    except:
        showSplash = True
        
    if showSplash == True:
        runApp = wndDBConnecting.exec_()
        
    if runApp:
        db = MySQLdb.connect(host=conf.get('MySQL',  'host'), user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
        db.autocommit(True)

        cursor = db.cursor()
        cursor.execute("select footprint_name from footprints order by footprint_name")

        footprints_list = [ "" ]
        for row in cursor.fetchall():
            footprints_list.append(row[0])

        cursor.close()
        
        wndChooseFootprint.setFootprints(footprints_list)
        wndChooseFootprint.db = db
        wndChooseFootprint.updateUI()
        
        if wndChooseFootprint.exec_():
            cursor = db.cursor()
            cursor.execute("update task_list set in_progress = 0 where in_progress = 1")
            cursor.close()
            
            cursor = db.cursor()
            cursor.execute("call createFootprint(%s);",  (wndChooseFootprint.txtFootprintName.text(), ))
            footprint_id = cursor.fetchone()[0]
            cursor.close()
            
            wndMainWindow.setWindowTitle("autodane : {0}".format(wndChooseFootprint.txtFootprintName.text()))
            
            wndMainWindow.db = db
            wndMainWindow.footprint_id = footprint_id
            
            #wndMainWindow.on_btnUpdateSummary_clicked()
            #wndMainWindow.on_btnUpdateHosts_clicked()
            #wndMainWindow.on_btnUpdateDomains_clicked()
            #wndMainWindow.on_btnUpdateCreds_clicked()
            #wndMainWindow.on_btnUpdateTaskList_clicked()
            #wndMainWindow.on_btnUpdateTaskLogs_clicked()
            #wndMainWindow.updateWebsites()
            
            #wndMainWindow.show()
            
            for item in wndChooseFootprint.txtExclude.toPlainText().split("\n"):
                if item != "":
                    cursor = db.cursor()
                    cursor.execute("call addScopeItem(%s, %s, %s)", (footprint_id,  3,  item, ))
                    cursor.close()
                    
            cursor = db.cursor()
            cursor.execute("select item_value from scope where footprint_id = %s and item_type = 3", (footprint_id, ))
            os.popen('echo "" > temp/exclude_list')
            for row in cursor.fetchall():
                os.popen("echo {0} >> temp/exclude_list".format(row[0]))
            cursor.close()
            
            #TODO: call these in a thread, so they can take as long as they need to 
            for item in wndChooseFootprint.txtKnownHosts.toPlainText().split("\n"):
                if item != "":
                    cursor = db.cursor()
                    cursor.execute("call addScopeItem(%s, %s, %s)", (footprint_id,  1,  item, ))
                    cursor.close()
                    
            for item in wndChooseFootprint.txtKnownDCs.toPlainText().split("\n"):
                if item != "":
                    cursor = db.cursor()
                    cursor.execute("call addHost(%s, %s, '', 1)", (footprint_id,  item, ))
                    cursor.close()
                
            for item in wndChooseFootprint.txtKnownRanges.toPlainText().split("\n"):
                if item != "":
                    octs = item.split(".")
                    if octs[3] == "0/24":
                        #print "add range: {0}".format(item)
                        cursor = db.cursor()
                        cursor.execute("call addScopeItem(%s, %s, %s)", (footprint_id,  2,  item, ))
                        cursor.close()
                    elif item.split(".")[3] == "0/16":
                        for oct2 in range(0, 256):
                            cursor = db.cursor()
                            cursor.execute("call addScopeItem(%s, %s, %s)", (footprint_id,  2,  "{0}.{1}.{2}.0/24".format(octs[0],  octs[1], oct2), ))
                            cursor.close()
                    else:
                        cursor = db.cursor()
                        cursor.execute("call addScopeItem(%s, %s, %s)", (footprint_id,  2,  item, ))
                        cursor.close()
                    #elif item.split(".")[3] == "0/8":
                    #    for oct1 in range(0, 256):
                    #        for oct2 in range(0, 256):
                    #            print "{0}.{1}.{2}.0/24".format(octs[0],  oct1, oct2)
            
            for row in xrange(0, wndChooseFootprint.tblDomainCreds.rowCount()):
                domain = wndChooseFootprint.tblDomainCreds.item(row, 0).text()
                username =  wndChooseFootprint.tblDomainCreds.item(row, 1).text()
                password = wndChooseFootprint.tblDomainCreds.item(row, 2).text()
                lm_hash = wndChooseFootprint.tblDomainCreds.item(row, 3).text()
                ntlm_hash = wndChooseFootprint.tblDomainCreds.item(row, 4).text()
                valid = (wndChooseFootprint.tblDomainCreds.item(row, 5).text() == "True")
                cursor = db.cursor()
                cursor.execute("call addDomainCreds(%s, %s, %s, %s, %s, %s, %s)",  (footprint_id, 0, domain, username, password, lm_hash, ntlm_hash, ))
                cursor.close()
                
                if valid == True:
                    cursor = db.cursor()
                    cursor.execute("update domain_credentials set verified = 1, valid = 1 where footprint_id = %s and domain = %s and username = %s", (footprint_id, domain, username, ))
                    cursor.close()

            print "on_btnUpdateSummary_clicked"
            wndMainWindow.on_btnUpdateSummary_clicked()
            
            print "on_btnUpdateHosts_clicked"
            wndMainWindow.on_btnUpdateHosts_clicked()
            
            print "on_btnUpdateDomains_clicked"
            wndMainWindow.on_btnUpdateDomains_clicked()
            
            print "on_btnUpdateCreds_clicked"
            wndMainWindow.on_btnUpdateCreds_clicked()
            
            print "on_btnUpdateTaskList_clicked"
            wndMainWindow.on_btnUpdateTaskList_clicked()
            
            print "setupFilterCombos"
            wndMainWindow.setupFilterCombos()
            
            #print "on_btnSearchLogs_clicked"
            #wndMainWindow.on_btnSearchLogs_clicked()
            
            print "updateWebsites"
            wndMainWindow.updateWebsites()
            
            wndMainWindow.show()

            if wndChooseFootprint.sldTestDepth.value() > 0:
                for i in wndChooseFootprint.enumerationPlugins:
                    if wndChooseFootprint.enumerationPlugins[i][3] == True:
                        cursor = db.cursor()
                        #TODO add logic to check whether these tasks have been done before adding them
                        #otherwise the same thing will be run each time the app is opened
                        cursor.execute("insert into task_list (footprint_id, task_descriptions_id, item_identifier) values (%s, %s, 0)", (footprint_id, wndChooseFootprint.enumerationPlugins[i][0], ))
                        cursor.close()
                     
                nmap_timing = wndChooseFootprint.cmbNmapTiming.currentText()
                network_interface = wndChooseFootprint.cmbNetworkInterface.currentText()
                thread_counts = {}
                thread_counts['all'] = wndChooseFootprint.sedAllTasks.value()
                thread_counts['footprinting'] = wndChooseFootprint.sedFootprinting.value()
                thread_counts['exploits'] = wndChooseFootprint.sedExploits.value()
                thread_counts['pivoting'] = wndChooseFootprint.sedPivoting.value()
                thread_counts['pivoting_msf'] = wndChooseFootprint.sedPivotingMsf.value()
                thread_counts['domain_enumeration'] = wndChooseFootprint.sedDomainEnumeration.value()
                
                thread.start_new_thread(wndMainWindow.startWork, (wndChooseFootprint.sldTestDepth.value(), nmap_timing, network_interface, thread_counts ))
        else:
            quit()
    else:
        quit()

    sys.exit(app.exec_())
        
if __name__ == '__main__':
    main()

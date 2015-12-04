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

    if wndDBConnecting.exec_():
        conf = ConfigParser.ConfigParser()
        conf.read("settings.ini")

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
            cursor.execute("call createFootprint(%s);",  wndChooseFootprint.txtFootprintName.text())
            footprint_id = cursor.fetchone()[0]
            cursor.close()
            
            wndMainWindow.setWindowTitle("autodane : {0}".format(wndChooseFootprint.txtFootprintName.text()))
            
            wndMainWindow.db = db
            wndMainWindow.footprint_id = footprint_id
            
            wndMainWindow.on_btnUpdateSummary_clicked()
            wndMainWindow.on_btnUpdateHosts_clicked()
            wndMainWindow.on_btnUpdateCreds_clicked()
            wndMainWindow.on_btnUpdateTaskList_clicked()
            wndMainWindow.on_btnUpdateTaskLogs_clicked()
            wndMainWindow.updateWebsites()
            
            wndMainWindow.show()
            
            for item in wndChooseFootprint.txtExclude.toPlainText().split("\n"):
                if item != "":
                    cursor = db.cursor()
                    cursor.execute("call addScopeItem(%s, %s, %s)", (footprint_id,  3,  item))
                    cursor.close()
                    
            cursor = db.cursor()
            cursor.execute("select item_value from scope where footprint_id = %s and item_type = 3", (footprint_id))
            os.popen('echo "" > temp/exclude_list')
            for row in cursor.fetchall():
                os.popen("echo {0} >> temp/exclude_list".format(row[0]))
            cursor.close()
            
            #TODO: call these in a thread, so they can take as long as they need to 
            for item in wndChooseFootprint.txtKnownHosts.toPlainText().split("\n"):
                if item != "":
                    cursor = db.cursor()
                    cursor.execute("call addScopeItem(%s, %s, %s)", (footprint_id,  1,  item))
                    cursor.close()
                
            for item in wndChooseFootprint.txtKnownRanges.toPlainText().split("\n"):
                if item != "":
                    octs = item.split(".")
                    if octs[3] == "0/24":
                        #print "add range: {0}".format(item)
                        cursor = db.cursor()
                        cursor.execute("call addScopeItem(%s, %s, %s)", (footprint_id,  2,  item))
                        cursor.close()
                    elif item.split(".")[3] == "0/16":
                        for oct2 in range(0, 256):
                            #print "add range: {0}.{1}.{2}.0/24".format(octs[0],  octs[1], oct2)
                            cursor = db.cursor()
                            cursor.execute("call addScopeItem(%s, %s, %s)", (footprint_id,  2,  "{0}.{1}.{2}.0/24".format(octs[0],  octs[1], oct2)))
                            cursor.close()
                    else:
                        #print "add range: {0}".format(item)
                        cursor = db.cursor()
                        cursor.execute("call addScopeItem(%s, %s, %s)", (footprint_id,  2,  item))
                        cursor.close()
                    #elif item.split(".")[3] == "0/8":
                    #    for oct1 in range(0, 256):
                    #        for oct2 in range(0, 256):
                    #            print "{0}.{1}.{2}.0/24".format(octs[0],  oct1, oct2)
            
            if wndChooseFootprint.cbxDoWork.isChecked():
                #add local ip address
                cursor = db.cursor()
                cursor.execute("insert into task_list (footprint_id, task_descriptions_id, item_identifier) values (%s, 1, 0)", (footprint_id))
                cursor.close()
                
                #add local nameserver ips
                cursor = db.cursor()
                cursor.execute("insert into task_list (footprint_id, task_descriptions_id, item_identifier) values (%s, 5, 0)", (footprint_id))
                cursor.close()

                wndMainWindow.startWork()
        else:
            quit()
    else:
        quit()

    sys.exit(app.exec_())
        
if __name__ == '__main__':
    main()

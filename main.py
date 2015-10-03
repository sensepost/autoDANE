#!/usr/bin/python

from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import QString
from PyQt4.QtGui import QApplication
from source.mainwindow import MainWindow
from source.choosefootprint import ChooseFootprintDialog

import ConfigParser

def main():
    from source import dbfunctions
    import MySQLdb
    import sys
    
    app = QApplication(sys.argv)
    #app.setStyle("cleanlooks")
    #plastique
    #cde
    #motif
    #sgi
    #windows
    #cleanlooks
    #mac
    
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    cursor = db.cursor()
    cursor.execute("select footprint_name from footprints order by footprint_name")
    
    footprints_list = [ "" ]
    for row in cursor.fetchall():
        footprints_list.append(row[0])
        
    cursor.close()
    
    cftwnd = ChooseFootprintDialog()
    cftwnd.setFootprints(footprints_list)
    if cftwnd.exec_():
        footprintName,  doWork,  options = cftwnd.getResults()
        
        footprintID = dbfunctions.createFootprint(db,  footprintName)
        
        wnd = MainWindow()
        wnd.setWindowTitle("autodane : {0}".format(footprintName))
        wnd.setFootprintInfo(db,  footprintID,  footprintName,  doWork,  options)
        wnd.show()
        wnd.start()

        logoPixmap = QtGui.QPixmap(QString.fromUtf8('images/logo.png'))
        logoScaledPixmap = logoPixmap.scaled(wnd.lblSensePostLogo.size(),  QtCore.Qt.KeepAspectRatio)
        wnd.lblSensePostLogo.setPixmap(logoScaledPixmap)
        
        emailPixmap = QtGui.QPixmap(QString.fromUtf8('images/email.png'))
        emailScaledPixmap = emailPixmap.scaled(wnd.lblEmailIcon.size(),  QtCore.Qt.KeepAspectRatio)
        wnd.lblEmailIcon.setPixmap(emailScaledPixmap)
        
        emailScaledPixmap = emailPixmap.scaled(wnd.lblEmailIcon2.size(),  QtCore.Qt.KeepAspectRatio)
        wnd.lblEmailIcon2.setPixmap(emailScaledPixmap)
        
        skypePixmap = QtGui.QPixmap(QString.fromUtf8('images/skype.png'))
        skypeScaledPixmap = skypePixmap.scaled(wnd.lblSkypeLogo.size(),  QtCore.Qt.KeepAspectRatio)
        wnd.lblSkypeLogo.setPixmap(skypeScaledPixmap)
    else:
        quit()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

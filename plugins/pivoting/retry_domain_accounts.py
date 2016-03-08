import os

def run(params):
    sql = """call getDomainCredsToRetry(%s)"""
            
    cursor = params.db.cursor()
    cursor.execute(sql, (params.footprint_id, ))
    row = cursor.fetchone()
    cursor.close()
    #TODO: delimit password, else funny characters might cause the command to fail
    
    if row != None:
        cursor = params.db.cursor()
        cursor.execute("call addTaskListItem(%s, 16, %s, 1, 0)", (params.footprint_id, row[2], ))
        task_id = cursor.fetchone()[0]
        cursor.close()        
        
        host_id = row[0]
        ip_address = row[1]
        domain_creds_id = row[2]
        domain = row[3]
        username = row[4]
        cleartext_password = row[5]

        delimited_pwd = ""
        for c in cleartext_password:
            delimited_pwd = delimited_pwd + "\{}".format(c)
        
        output_file_name = "temp/" + params.getRandomFileName()
        cmd = "hydra -l {0}@{1} -p {2} {3} rdp -t 1 > {4}".format(username, domain, delimited_pwd, ip_address, output_file_name)
        params.log(cmd.split(">")[0])
        params.log("")
        os.popen(cmd)
        params.log(os.popen("cat {0}".format(output_file_name)).read())
        res = os.popen("cat {0} | grep \"1 valid password found\" | wc -l".format(output_file_name)).read()[:-1]
        
        cursorb = params.db.cursor()
        cursorb.execute("call addToDomainCredentialsMap(%s, %s, %s, %s)", (params.footprint_id, host_id, domain_creds_id, int(res), ))
        cursorb.close()
        
        final_output = ""
        while params.log_queue.empty() == False:
            final_output += "{0}\r\n".format(params.log_queue.get(False))
        final_output = final_output[:-2]
        
        spCursor = params.db.cursor()
        spCursor.execute("call updateTaskStatus(%s, %s, %s, %s)",  ( task_id,  0,  1, final_output, ))
        spCursor.close()

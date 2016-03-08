import os
import time

def run(params):
    sql = """call getDomainCredsToVerify(%s)"""
            
    cursor = params.db.cursor()
    cursor.execute(sql, (params.footprint_id, ))
    #TODO: this lists all the dcs that could be used
    #      change the script to check if a host is unaccessible, and use a different one if so
    row = cursor.fetchone()
    cursor.close()
    
    if row != None:
        domain_creds_id = row[0]
        ip_address = row[1]
        domain = row[2]
        username = row[3]
        cleartext_password = row[4]
        task_id = row[6]

        delimited_pwd = ""
        for c in cleartext_password:
            delimited_pwd = delimited_pwd + "\{}".format(c)

        output_file_name = "temp/" + params.getRandomFileName()
        cmd = "hydra -l {0}@{1} -p {2} {3} smb -t 1 > {4}".format(username, domain, delimited_pwd, ip_address, output_file_name)
        params.log(cmd.split(">")[0])
        params.log("")
        os.popen(cmd)
        params.log(os.popen("cat {0}".format(output_file_name)).read())
        res = os.popen("cat {0} | grep \"1 valid password found\" | wc -l".format(output_file_name)).read()[:-1]

        cursorb = params.db.cursor()
        cursorb.execute("call setDomainCredsVerified(%s, %s, %s)", (params.footprint_id, domain_creds_id, (res == "1"), ))
        cursorb.close()
        
        final_output = ""
        while params.log_queue.empty() == False:
            final_output += "{0}\r\n".format(params.log_queue.get(False))
        final_output = final_output[:-2]
        
        spCursor = params.db.cursor()
        spCursor.execute("call updateTaskStatus(%s, %s, %s, %s)",  ( task_id,  0,  1, final_output, ))
        spCursor.close()

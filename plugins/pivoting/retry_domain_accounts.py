import os
import time

def run(params):
    sql = """
        select 
            hd.id, hd.ip_address, dc.id, dc.domain, dc.username, dc.cleartext_password
        from 
            host_data hd 
            join port_data pd on hd.id = pd.host_data_id
            join domain_credentials dc on hd.footprint_id = dc.footprint_id
        where
            hd.footprint_id = %s and
            pd.port_number = 445 and
            (hd.footprint_id, hd.id, dc.id) not in (select footprint_id, host_data_id, domain_credentials_id from domain_credentials_map where footprint_id = %s) and
            dc.verified = 1
        limit 1"""
            
    cursor = params.db.cursor()
    cursor.execute(sql, (params.footprint_id, params.footprint_id))
    
    row = cursor.fetchone()
    cursor.close()
    #TODO: delimit password, else funny characters might cause the command to fail
    
    #try:
    if row != None:
        host_id = row[0]
        ip_address = row[1]
        domain_creds_id = row[2]
        domain = row[3]
        username = row[4]
        cleartext_password = row[5]
        
        #print "trying creds {0}:{1}:{2} on host {3}".format(domain, username, cleartext_password, ip_address)
        params.log("trying creds {0}:{1}:{2} on host {3}".format(domain, username, cleartext_password, ip_address))
        
        #cmd = "hydra -l {0}@{1} -p {2} {3} smb >&1 | grep \"1 valid password found\" | wc -l".format(username, domain, cleartext_password, ip_address)
        cmd = "hydra -l {0}@{1} -p {2} {3} rdp -t 1 | grep \"1 valid password found\" | wc -l".format(username, domain, cleartext_password, ip_address)
        #print row
        res = os.popen(cmd).read()[:-1]
        #print "final result is {0}".format(res)
        
        if res == "1":
            #print "creds worked"
            params.log("creds worked")
        else:
            #print "creds did not work"
            params.log("creds did not work")
        
        cursorb = params.db.cursor()
        #cursorb.execute("call addToLocalCredentialsMap(%s, %s, %s)", (row[0], row[1], (res == "1")))
        cursorb.execute("call addToDomainCredentialsMap(%s, %s, %s, %s)", (params.footprint_id, host_id, domain_creds_id, (res == "1")))
        cursorb.close()
    #except:
        #print "error in retry_local_accounts"
    else:
        #print "no creds to check"
        params.log("no creds to check")
        time.sleep(1)

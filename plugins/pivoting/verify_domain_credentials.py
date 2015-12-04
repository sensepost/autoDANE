import os

def run(params):
    sql = """
        select 
            m.id, hd.ip_address, dc.domain, dc.username, dc.cleartext_password, dc.verified
        from 
            domain_credentials dc 
            join domain_credentials_map m on m.domain_credentials_id = dc.id 
            join host_data hd on hd.id = m.host_data_id
        where m.id = %s"""
            
    cursor = params.db.cursor()
    cursor.execute(sql, (params.item_identifier))
    row = cursor.fetchone()
    cursor.close()
    #TODO: delimit password, else funny characters might cause the command to fail
    
    domain_credentials_map_id = row[0]
    ip_address = row[1]
    domain = row[2]
    username = row[3]
    cleartext_password = row[4]
    
    #TODO: check if this flag is true
    #if it is, the creds have already been validated, and don't need to be checked again
    #valid = row[5]
    
    #print "checking creds {0}:{1}:{2} on {3}".format(domain, username, cleartext_password, ip_address)
    #print ""
    params.log("checking creds {0}:{1}:{2} on {3}".format(domain, username, cleartext_password, ip_address))
    params.log("")
    
    #TODO check this against the relevant domain controller instead of the host where it was found
    cmd = "hydra -l {0}@{1} -p {2} {3} smb -t 1 | grep \"1 valid password found\" | wc -l".format(username, domain, cleartext_password, ip_address)

    res = os.popen(cmd).read()[:-1]
    
    if res == "1":
        #print "creds are valid. "
        params.log("creds are valid. ")
    
        cursorb = params.db.cursor()
        cursorb.execute("call setDomainCredsVerified(%s, %s)", (params.footprint_id, domain_credentials_map_id))
        cursorb.close()
    else:
        #print "creds are invalid"
        params.log("creds are invalid")

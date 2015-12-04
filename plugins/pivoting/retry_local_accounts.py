import os
import time

def run(params):
    sql = """
            select 
                hd.id,
                lc.id,
                hd.ip_address,
                lc.username,
                lc.cleartext_password
            from 
                host_data hd,
                port_data pd,
                local_credentials lc
            where
                hd.id = pd.host_data_id and
                pd.port_number = 445 and
                lc.cleartext_password != '' and
                #exclude credentials that have been tried prviously
                (hd.ip_address, lc.username, lc.cleartext_password) not in (select hd.ip_address, lc.username, lc.cleartext_password from host_data hd join port_data pd on hd.id = pd.host_data_id join local_credentials_map m on hd.id = m.host_data_id join local_credentials lc on lc.id = m.local_credentials_id where hd.footprint_id = 1 and pd.port_number = 445) and
                #exclude hosts that have valid creds with the same username, regardless of the password 
                (hd.ip_address, lc.username) not in (select hd.ip_address, lc.username from host_data hd join port_data pd on hd.id = pd.host_data_id join local_credentials_map m on hd.id = m.host_data_id join local_credentials lc on lc.id = m.local_credentials_id where hd.footprint_id = %s and pd.port_number = 445 and m.valid = 1)"""
            
    cursor = params.db.cursor()
    cursor.execute(sql, (params.footprint_id))
    
    row = cursor.fetchone()
    cursor.close()
    #TODO: delimit password, else funny characters might cause the command to fail

    if row != None:
        cmd = "hydra -l {1} -p {2} {0} smb >&1 | grep \"1 valid password found\" | wc -l".format(row[2], row[3], row[4])
        
        res = os.popen(cmd).read()[:-1]
        
        if res == "1":
            #print "creds worked"
            params.log("creds worked")
        else:
            #print "creds did not work"
            params.log("creds did not work")
        
        cursorb = params.db.cursor()
        cursorb.execute("call addToLocalCredentialsMap(%s, %s, %s)", (row[0], row[1], (res == "1")))
        cursorb.close()
    else:
        #print "no creds to check"
        params.log("no creds to check")
        time.sleep(1)

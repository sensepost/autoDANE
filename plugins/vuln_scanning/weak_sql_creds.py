import os

def run(params):
    cursor = params.db.cursor()
    cursor.execute("select hd.ip_address, pd.id, pd.port_number from host_data hd join port_data pd on hd.id = pd.host_data_id where pd.id = %s", params.item_identifier)
    row = cursor.fetchone()
    
    #print "Checking {0}".format(row[0])
    #print ""
    params.log("Checking {0}".format(row[0]))
    params.log("")
    
    cmd = "nmap -n -p 1433 --script ms-sql-brute --script-args userdb=creds/mssql_users,passdb=creds/mssql_passes {0} | grep \"Login Success\"".format(row[0])
    
    cursor.close()
    
    res = os.popen(cmd).read()
    if len(res) > 2:
        creds = res[2:-1].split("=")[0].strip()
        
        cursor = params.db.cursor()
        cursor.execute("call addVulnerability(%s, %s, %s, %s)",  (params.footprint_id, row[1], 2,  creds))
        cursor.close()
        
        #print "host {0} has weak sql creds: {1}".format(row[0],  creds)
        params.log("host {0} has weak sql creds: {1}".format(row[0],  creds))

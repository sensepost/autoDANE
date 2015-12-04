import os

def run(params):
    cursor = params.db.cursor()
    cursor.execute("select hd.ip_address, pd.id, pd.port_number from host_data hd join port_data pd on hd.id = pd.host_data_id where pd.id = %s", params.item_identifier)
    row = cursor.fetchone()
    
    #print "Checking {0}".format(row[0])
    #print ""
    params.log("Checking {0}".format(row[0]))
    params.log("")
    
    cmd = "nmap {0} -p {1} --script software/tomcat_check/tomcat-scan.nse | grep \"Found combination\" -B 7 | grep \"Found combination\"".format(row[0], row[2])
    
    cursor.close()
    res = os.popen(cmd).read()
    
    if len(res) > 3:
        creds = res[:-1].split(" ")[3]
        #print res
        #print "host {0} has weak tomcat creds: {1}".format(row[0], creds)
        params.log("host {0} has weak tomcat creds: {1}".format(row[0], creds))
        
        cursor = params.db.cursor()
        cursor.execute("call addVulnerability(%s, %s, %s, %s)",  (params.footprint_id, row[1], 3,  creds))
        cursor.close()

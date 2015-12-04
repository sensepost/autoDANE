import os

def run(params):
    cursor = params.db.cursor()
    cursor.execute("select hd.ip_address, pd.id, pd.port_number from host_data hd join port_data pd on hd.id = pd.host_data_id where pd.id = %s", params.item_identifier)
    row = cursor.fetchone()
    
    #print "Checking {0}".format(row[0])
    params.log("Checking {0}".format(row[0]))
    
    #cmd = "python software/ms08-067_check/ms08-067_check.py -s -t {0} >&1 | grep VULNERABLE".format(row[0])
    cmd = "nmap {0} -p 445 --script software/ms08-067_check/ms08-067.nse | grep VULNERABLE".format(row[0])
    cursor.close()
    
    res = os.popen(cmd).read()
    #print res
    params.log(res)
    if len(res) > 1:
        cursor = params.db.cursor()
        cursor.execute("call addVulnerability(%s, %s, %s, %s)",  (params.footprint_id, row[1], 1,  ""))
        #print "host {0} is vulnerable to MS08067".format(row[0])
        params.log("host {0} is vulnerable to MS08067".format(row[0]))
    else:
        #print "host {0} is not vulnerable to MS08067".format(row[0])
        params.log("host {0} is not vulnerable to MS08067".format(row[0]))

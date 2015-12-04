import os

def run(params):
    cmd = 'nmap {0} -sL --excludefile temp/exclude_list | grep "Nmap scan report" | grep \( | cut -d \  -f 5'
    cursor = params.db.cursor()
    cursor.execute("select ip_address from host_data where id = %s", (params.item_identifier))
    row = cursor.fetchone()
    cursor.close()
    
    host_name = os.popen(cmd.format(row[0])).read()
    
    if host_name != "":
        #print "hostname for {0} is {1}".format(row[0], host_name)
        params.log("hostname for {0} is {1}".format(row[0], host_name))
        cursor = params.db.cursor()
        cursor.execute("call addHost(%s, %s, %s)", (params.footprint_id, row[0], host_name))
    else:
        #print "{0} doesn't have a hostname".format(row[0])
        params.log("{0} doesn't have a hostname".format(row[0]))

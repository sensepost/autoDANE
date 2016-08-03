import os
import random
import string

def run(params):
    cursor = params.db.cursor()
    cursor.execute("select item_value from scope where id = %s",  (params.item_identifier, ))
    ip_address = cursor.fetchone()[0]
    cursor.close()
    
    temp_file_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))

    cmd = "nmap {0} --excludefile temp/exclude_list -sL -oG temp/{1} -Pn -vv -T {2}".format(ip_address, temp_file_name, params.nmapTiming)
    params.log(cmd)
    params.log("")
    os.popen(cmd)

    for line in open('temp/' + temp_file_name):
        if line[:5] == "Host:":
            host = line.split(" ")[1]
            hostname = line.split("(")[1].split(")")[0]
            if hostname != "":
                cursor = params.db.cursor()
                cursor.execute("select addHost(%s, %s::varchar, %s::varchar, false)",  (params.footprint_id,  host, hostname, ))
                cursor.close()
    
    params.log(os.popen("cat temp/{0}".format(temp_file_name)).read())

import os
import random
import string

def run(params):
    cursor = params.db.cursor()
    cursor.execute("select ip_address from host_data where id = %s",  (params.item_identifier))
    ip_address = cursor.fetchone()[0]
    cursor.close()
    
    temp_file_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
    
    os.popen("nmap {0} --excludefile temp/exclude_list -n -p 21,22,80,135,443,445,1433,3306,3389,5800,5900,8080-8090,9090-9099 -oG temp/{1} -Pn -vv".format(ip_address, temp_file_name))

    params.log(os.popen("cat temp/{0}".format(temp_file_name)).read())

    hosts = []
    for line in open('temp/' + temp_file_name):
        if line[:1] == "#":
            continue

        if line.find("Status") == -1:
            host = line[6:]
            host = host[:host.find(" ")]
            hosts.append(host)

            items = line[line.find("Ports")+7:]
            for item in items.split(", "):
                data = item.split("/")
                port = data[0]
                status = data[1]
                if status == "open":
                    cursor = params.db.cursor()
                    cursor.execute("call addPort(%s, %s, %s)", (params.footprint_id, params.item_identifier, port))
                    cursor.close()
                    #print "found open port: {0}:{1}".format(host, port)
                    #params.log("found open port: {0}:{1}".format(host, port))
        elif line.find("Status: Down") != -1:
            host = line[6:]
            host = host[:host.find(" ")]
            hosts.append(host)
        else:
            continue

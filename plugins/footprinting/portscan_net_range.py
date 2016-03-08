import os
import random
import string

#TODO: write plugin to do dns queries on the ranges as well

def run(params):
    cursor = params.db.cursor()
    cursor.execute("select net_range from net_ranges where id = %s",  (params.item_identifier, ))
    ip_address = cursor.fetchone()[0]
    cursor.close()
    
    temp_file_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))

    #TODO: add the list of ports to be scanned to the db, and read it from there
    #os.popen("nmap {0} --excludefile temp/exclude_list -n -p 21,22,80,135,443,445,1433,3306,3389,5800,5900,8080-8090,9090-9099 -oG temp/{1} -Pn -vv".format(ip_address, temp_file_name))
    #os.popen("nmap {0} --excludefile temp/exclude_list -n -p 21,22,80,135,443,445,1433,3306,3389,5800,5900,8080 -oG temp/{1} -Pn -vv".format(ip_address, temp_file_name))

    cmd = "nmap {0} --excludefile temp/exclude_list -n -p 21,22,80,135,443,445,1433,3306,3389,5555,5800,5900,8080 -oG temp/{1} -Pn -vv -T {2}".format(ip_address, temp_file_name, params.nmapTiming)
    params.log(cmd)
    params.log("")
    os.popen(cmd)

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
                    cursor.execute("call addHost(%s, %s, '', 0)",  (params.footprint_id,  host, ))
                    cursor.close()
                    
                    cursor = params.db.cursor()
                    cursor.execute("select id from host_data where ip_address = %s and footprint_id = %s", (host, params.footprint_id, ))
                    host_id = cursor.fetchone()[0]
                    cursor.close()
                    
                    cursor = params.db.cursor()
                    cursor.execute("call addPort(%s, %s, %s)", (params.footprint_id, host_id, port, ))
                    cursor.close()
    
    params.log(os.popen("cat temp/{0}".format(temp_file_name)).read())

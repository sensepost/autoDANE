import os
import random
import string

def run(params):
    cursor = params.db.cursor()
    cursor.execute("select item_value from scope where id = %s",  (params.item_identifier, ))
    ip_address = cursor.fetchone()[0]
    cursor.close()
    
    temp_file_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
    
    ports = ""
    cursor = params.db.cursor()
    cursor.execute("select port_number from ports_to_scan where type_id = 2")
    for row in cursor.fetchall():
        ports += str(row[0]) + ","
        
    ports = ports[:-1]
    cursor.close()
    
    cmd = "nmap {0} --excludefile temp/exclude_list -n -p {1} -oG temp/{2} -Pn -vv -T {3}".format(ip_address, ports, temp_file_name, params.nmapTiming)
    os.popen(cmd)
    params.log(cmd)
    params.log("")
    
    params.log(os.popen("cat temp/{0}".format(temp_file_name)).read())
    
    hosts = []
    hostAdded = False
    host_id = 0
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
                    if hostAdded == False:
                        cursor = params.db.cursor()
                        #cursor.execute("call addHost(%s, %s, '', 0)",  (params.footprint_id,  host, ))
                        cursor.execute("select addHost(%s, %s::varchar, ''::varchar, false)",  (params.footprint_id,  host, ))
                        cursor.close()
                        
                        cursor = params.db.cursor()
                        cursor.execute("select id from host_data where ip_address = %s and footprint_id = %s", (host, params.footprint_id, ))
                        host_id = cursor.fetchone()[0]
                        cursor.close()
                        hostAdded = True
                        
                    cursor = params.db.cursor()
                    #cursor.execute("call addPort(%s, %s, %s)", (params.footprint_id, host_id, port, ))
                    cursor.execute("select addPort(%s, %s, %s)", (params.footprint_id, host_id, port, ))
                    cursor.close()

import os
import random
import string
import socket

def run(params):
    cursor = params.db.cursor()
    cursor.execute("select net_range from net_ranges where id = %s",  (params.item_identifier, ))
    net_range = cursor.fetchone()[0]
    cursor.close()
    
    params.log("Check for instances of the MS SQL Server Discovery service in {}".format(net_range))
    params.log("")
    
    net_range = net_range.replace("0/24", "")
    
    for o in range(256):
        try:
            ip = "{}{}".format(net_range, o)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0.5)
            sock.sendto("\x02\x41\x41\x41\x41", (ip, 1434))
            val = sock.recv(4096)
            port = int(val.split(";")[9])
            params.log("  {}:{}".format(ip, port))
            
            cursor = params.db.cursor()
            cursor.execute("select addHost(%s, %s::varchar, ''::varchar, false)",  (params.footprint_id,  ip, ))
            cursor.close()
            
            cursor = params.db.cursor()
            cursor.execute("select id from host_data where ip_address = %s and footprint_id = %s", (ip, params.footprint_id, ))
            host_id = cursor.fetchone()[0]
            cursor.close()
            
            cursor = params.db.cursor()
            cursor.execute("select addPort(%s, %s, %s)", (params.footprint_id, host_id, port, ))
            cursor.close()
            
            cursor = params.db.cursor()
            cursor.execute("select id from port_data where host_data_id = %s and port_number = %s", (host_id, port, ))
            port_id = cursor.fetchone()[0]
            cursor.close()
            
            cursor = params.db.cursor()
            cursor.execute("select executetriggers(%s, %s, %s, %s)", (params.footprint_id, port_id, 12, str(port), ))
            cursor.close()
            
        except:
            continue

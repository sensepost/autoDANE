import os

def run(params):
    #TODO: get interface from the "Advanced Options" tab you're going to add
    ip_address = os.popen('ifconfig eth0 | grep "inet addr" | cut -d \: -f 2 | cut -d \  -f 1').read()[:-1]
    
    params.log("local ip address {0}. adding to db".format(ip_address))
    
    cursor = params.db.cursor()
    cursor.execute("call addHost(%s, %s, '', 0)",  (params.footprint_id,  ip_address, ))
    cursor.close()

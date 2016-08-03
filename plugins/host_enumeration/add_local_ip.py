import os

def run(params):
    #TODO: get interface from the "Advanced Options" tab you're going to add
    ip_address = os.popen('ifconfig ' + str(params.networkInterface) + ' | grep "inet addr" | cut -d \: -f 2 | cut -d \  -f 1').read()[:-1]
    
    params.log("local ip address {0}. adding to db".format(ip_address))
    
    cursor = params.db.cursor()
    cursor.execute("select addHost(%s, %s::varchar, ''::varchar, false)",  (params.footprint_id,  ip_address, ))
    cursor.close()

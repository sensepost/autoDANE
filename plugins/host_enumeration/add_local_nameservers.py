import os

def run(params):

    try:
        cmd = "host `cat /etc/resolv.conf | grep search | cut -d \  -f 2` | cut -d \  -f 4"
        params.log(cmd)
        params.log("")
        for ip_address in os.popen(cmd).read().split("\n"):
            if ip_address != "":
                cursor = params.db.cursor()
                cursor.execute("call addHost(%s, %s, '', 0)",  (params.footprint_id,  ip_address, ))
                cursor.close()
    except:
        pass
        
    try:
        cmd = "cat /etc/resolv.conf | grep nameserver | cut -d \  -f 2"
        params.log(cmd)
        params.log("")
        for ip_address in os.popen(cmd).read().split("\n"):
            if ip_address != "":
                cursor = params.db.cursor()
                cursor.execute("call addHost(%s, %s, '', 0)",  (params.footprint_id,  ip_address, ))
                cursor.close()
    except:
        pass

#    try:
#        cmd = "cat /etc/resolv.conf | grep search | cut -d \  -f 2"
#        params.log(cmd)
#        params.log("")
#        resolver = os.popen(cmd).read()[:-1]
#        params.log(resolver)
#        params.log("")
#        
#        cmd = "host {0} | grep address | cut -d \  -f 4".format(resolver)
#        params.log(cmd)
#        params.log("")
#        resolvers = os.popen(cmd).read()[:-1].split("\n")
#        params.log(resolvers)
#        params.log("")
#        
#        for r in resolvers:
#            cursor = params.db.cursor()
#            cursor.execute("call addHost(%s, %s, '', 1)", (params.footprint_id,  r, ))
#            cursor.close()
#    except:
#        pass

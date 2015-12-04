import os

def run(params):
    try:
        params.log("add_local_nameservers")
        resolver = os.popen('cat /etc/resolv.conf | grep search | cut -d \  -f 2').read()[:-1]
        resolvers = os.popen("host {0} | grep address | cut -d \  -f 4".format(resolver)).read()[:-1].split("\n")
        for r in resolvers:
            cursor = params.db.cursor()
            cursor.execute("call addHost(%s, %s, '', 1)", (params.footprint_id,  r))
            cursor.close()
    except:
        pass

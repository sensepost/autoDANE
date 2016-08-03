import os
import random
import string

def run(params):
    for domain in os.popen('cat /etc/resolv.conf  | grep search | cut -d \  -f 2').read().split("\n"):
        if domain != "":
            print "found domain [{}]".format(domain)
            temp_file_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
            cmd = "for i in `host {} | grep address | grep -v IPv6 | cut -d \  -f 4 | sort -u`; do timeout 2 dig axfr {} $i; done > temp/{}"
            os.popen(cmd.format(domain, domain, temp_file_name))
            #os.popen("dig axfr {} > temp/{}".format(domain, temp_file_name))

            #temp_file_name = "D2YJF4"
            for l in open("temp/{}".format(temp_file_name)):
                l = l[:-1]
                #print "[{}][{}]".format(l, l.find("\t"))
                if l.find("\tA\t") > -1:
                    ip_addr = l[::-1].split("\t")[0][::-1]
                    #print "A\t[{}] [{}]".format(l, ip_addr)
                    
                    cursor = params.db.cursor()
                    cursor.execute("select addHost(%s, %s::varchar, ''::varchar, false)",  (params.footprint_id,  ip_addr, ))
                    cursor.close()
                    
                    #continue
                elif l.find("\tNS\t") > -1:
                    host_name = l[::-1].split("\t")[0][::-1][:-1]
                    ip_addr = os.popen("host {} | grep address | cut -d \  -f 4".format(host_name)).read()[:-1]
                    #print "NS\t[{}] [{}] [{}]".format(l, host_name, ip_addr)
                    
                    cursor = params.db.cursor()
                    cursor.execute("select addHost(%s, %s::varchar, %s::varchar, false)",  (params.footprint_id,  ip_addr, host_name, ))
                    cursor.close()
                    
                    #continue
                elif l.find("CNAME") > -1:
                    host_name = l.split("CNAME")[1].strip()[:-1]
                    ip_addr = os.popen("host {} | grep address | cut -d \  -f 4".format(host_name)).read()[:-1]
                    #print "CNAME\t[{}] [{}] [{}]".format(l, host_name, ip_addr)
                    
                    cursor = params.db.cursor()
                    cursor.execute("select addHost(%s, %s::varchar, %s::varchar, false)",  (params.footprint_id,  ip_addr, host_name, ))
                    cursor.close()
                    
                    #continue
                elif l.find("\tMX\t") > -1:
                    host_name = l.split("MX")[1].strip()[:-1].split(" ")[1]
                    ip_addr = os.popen("host {} | grep address | cut -d \  -f 4".format(host_name)).read()[:-1]
                    #print "MX\t[{}] [{}] [{}]".format(l, host_name, ip_addr)
                    
                    cursor = params.db.cursor()
                    cursor.execute("select addHost(%s, %s::varchar, %s::varchar, false)",  (params.footprint_id,  ip_addr, host_name, ))
                    cursor.close()
                    
                    #continue
                else:
                    #print "?\t{}".format(l)
                    continue
            #for ip_address in os.popen("cat temp/" + temp_file_name + " | grep -Eo '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'").read().split("\n"):
            #    if ip_address != "":
            #        print "    adding ip address {}".format(ip_address)
            #        cursor = params.db.cursor()
            #        cursor.execute("select addHost(%s, %s::varchar, ''::varchar, false)",  (params.footprint_id,  ip_address, ))
            #        cursor.close()
            
            params.log(os.popen("cat temp/{0}".format(temp_file_name)).read())


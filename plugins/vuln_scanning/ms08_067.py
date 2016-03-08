import os

def run(params):
    cursor = params.db.cursor()
    cursor.execute("select hd.ip_address, pd.id, pd.port_number from host_data hd join port_data pd on hd.id = pd.host_data_id where pd.id = %s", (params.item_identifier, ))
    row = cursor.fetchone()
    
    output_file_name = "temp/" + params.getRandomFileName()
    cmd = "nmap {0} -n -p {1} --script software/ms08-067_check/ms08-067.nse -T {2} > {3}".format(row[0], row[2], params.nmapTiming, output_file_name)
    cursor.close()
    
    params.log(cmd.split(">")[0])
    
    os.popen(cmd)
    params.log(os.popen("cat {0}".format(output_file_name)).read())
    
    res = os.popen("""cat {0} | grep -e "MS08-067: LIKELY VULNERABLE" -e "MS08-067: VULNERABLE" """.format(output_file_name)).read()
    
    if len(res) > 1:
        cursor = params.db.cursor()
        cursor.execute("call addVulnerability(%s, %s, %s, %s)",  (params.footprint_id, row[1], 1,  "", ))
        cursor.close()

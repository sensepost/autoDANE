import os

def run(params):
    cursor = params.db.cursor()
    cursor.execute("select hd.ip_address, pd.id, pd.port_number from host_data hd join port_data pd on hd.id = pd.host_data_id where pd.id = %s", (params.item_identifier, ))
    row = cursor.fetchone()
    
    output_file_name = "temp/" + params.getRandomFileName()
    cmd = "nmap -n -p 1433 --script ms-sql-brute --script-args userdb=creds/mssql_users,passdb=creds/mssql_passes {0} -T {1} > {2}".format(row[0], params.nmapTiming, output_file_name)
    cursor.close()

    params.log(cmd.split(">")[0])
    
    os.popen(cmd)
    params.log(os.popen("cat {0}".format(output_file_name)).read())

    res = os.popen("cat {0} | grep \"Login Success\"".format(output_file_name)).read()

    if len(res) > 2:
        creds = res[2:-1].split("=")[0].strip()
        
        cursor = params.db.cursor()
        cursor.execute("call addVulnerability(%s, %s, %s, %s)",  (params.footprint_id, row[1], 2,  creds, ))
        cursor.close()

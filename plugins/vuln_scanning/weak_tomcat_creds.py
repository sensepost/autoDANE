import os

def run(params):
    cursor = params.db.cursor()
    cursor.execute("select hd.ip_address, pd.id, pd.port_number from host_data hd join port_data pd on hd.id = pd.host_data_id where pd.id = %s", (params.item_identifier, ))
    row = cursor.fetchone()
    
    output_file_name = "temp/" + params.getRandomFileName()
    cmd = "nmap {0} -p {1} --script software/tomcat_check/tomcat-scan.nse -T {2} > {3}".format(row[0], row[2], params.nmapTiming, output_file_name)    
    cursor.close()

    params.log(cmd.split(">")[0])
    #params.log("")

    os.popen(cmd)
    params.log(os.popen("cat {0}".format(output_file_name)).read())

    res = os.popen("cat {0} | grep \"Found combination\" -B 7 | grep \"Found combination\"".format(output_file_name)).read()
    
    if len(res) > 3:
        creds = res[:-1].split(" ")[3]
        
        cursor = params.db.cursor()
        cursor.execute("call addVulnerability(%s, %s, %s, %s)",  (params.footprint_id, row[1], 3,  creds, ))
        cursor.close()

import os
import time
import base64


def run(params):
    # sql = """call getDomainCredsToVerify(%s)"""
    sql = """SELECT
        (f).domain_credentials_id,
        (f).ip_address,
        (f).domain,
        (f).username,
        (f).cleartext_password,
        (f).host_data_id,
        (f).task_list_id
FROM (select getdomaincredstoverify(%s) AS f) x;"""

    cursor = params.db.cursor()
    cursor.execute(sql, (params.footprint_id, ))
    # TODO: this lists all the dcs that could be used
    # change the script to check if a host is inaccessible, and use a
    # different one if so
    row = cursor.fetchone()
    cursor.close()

    if row is not None:
        domain_creds_id = row[0]
        ip_address = row[1]
        domain = row[2]
        username = row[3]
        cleartext_password = row[4]
        task_id = row[6]

        delimited_pwd = ""
        for c in cleartext_password:
            delimited_pwd = delimited_pwd + "\{}".format(c)

        output_file_name = "temp/" + params.getRandomFileName()
        cmd = "hydra -l {0}@{1} -p {2} {3} smb -t 1 > {4}".format(username, domain, delimited_pwd, ip_address, output_file_name)
        params.log(cmd.split(">")[0])
        params.log("")
        os.popen(cmd)
        params.log(os.popen("cat {0}".format(output_file_name)).read())
        res = os.popen("cat {0} | grep \"1 valid password found\" | wc -l".format(output_file_name)).read()[:-1]

        cursorb = params.db.cursor()
        cursorb.execute("select setDomainCredsVerified(%s, %s, %s)",
                        (params.footprint_id, domain_creds_id, (res == "1"), ))
        cursorb.close()

        final_output = ""
        while params.log_queue.empty() is False:
            final_output += "{0}\r\n".format(params.log_queue.get(False))
        final_output = final_output[:-2]

        spCursor = params.db.cursor()
        spCursor.execute("select updateTaskStatus(%s, %s, %s, %s)",
                         (task_id,  False,  True, base64.b64encode(final_output), ))
        spCursor.close()

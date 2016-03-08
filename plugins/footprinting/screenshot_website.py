import os

def run(params):
    cursor = params.db.cursor()
    cursor.execute("select hd.id, hd.ip_address, pd.port_number from host_data hd join port_data pd on hd.id = pd.host_data_id where pd.id = %s",  (params.item_identifier, ))
    row = cursor.fetchone()
    cursor.close()
    
    host = row[1]
    port = row[2]
    
    protocol = "http"
    if port in [443, 8443]:
        protocol = "https"
        
    #print "screenshot site at {0}://{1}:{2}/".format(protocol, host, port)
    #params.log("screenshot site at {0}://{1}:{2}/".format(protocol, host, port))

    cmd = 'curl -m 60 -s -k --location {0}://{1}:{2}/'.format(protocol, host, port)
    html = os.popen(cmd).read()
    params.log(cmd)
    
    title = ""
    if html.find("<title") > -1:
        title = html[html.find("<title")+6:]
        title = title[title.find(">")+1:]
        title = title[:title.find("</title>")]
        title = title.replace("\n", "").strip()
    elif html.find("<TITLE") > -1:
        title = html[html.find("<TITLE")+6:]
        title = title[title.find(">")+1:]
        title = title[:title.find("</TITLE>")]
        title = title.replace("\n", "").strip()
    elif html.find("<h1") > -1:
        title = html[html.find("<h1")+2:]
        title = title[title.find(">")+1:]
        title = title[:title.find("</h1>")]
        title = title.replace("\n", "").strip()
    elif html.find("<") == -1:
        title = html
        title = title.replace("\n", "").strip()
    elif html == "":
        title = ""
    else:
        title = ""
    
    params.log("the title is {0}".format(title))
    params.log("")
    
    filename = "temp/{0}.jpg".format(params.getRandomFileName())
    cmd = "timeout 60 wkhtmltoimage --load-error-handling ignore -q {0}://{1}:{2}/ {3}".format(protocol, host, port, filename)
    os.popen(cmd)
    params.log(cmd)
    
    image = None
    try:
        with open(filename, 'r') as f:
            image = f.read()
    except:
        pass
    
    cursor = params.db.cursor()
    cursor.execute("call addWebsite(%s, %s, %s, %s)", (params.item_identifier, title,  html, image, ))
    cursor.close()

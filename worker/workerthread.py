import thread
import time
import sys
import MySQLdb
import ConfigParser
import subprocess
import multiprocessing
import socket
import os
import random
import string

class Params(object):
    db = None
    footprint_id = None
    item_identifier = None
    log_queue = None
    
    msf_user = ""
    msf_pass = ""
    msf_port = "0"
    
    def log(self, value):
        self.log_queue.put(value)
        print value
    
    def getLocalHost(self):
        return os.popen('ifconfig eth0 | grep "inet addr" | cut -d \: -f 2 | cut -d \  -f 1').read()[:-1]
        #return os.popen('ifconfig tun0 | grep "inet addr" | cut -d \: -f 2 | cut -d \  -f 1').read()[:-1]
        
    def getOpenPort(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', 0))
        addr, port = s.getsockname()
        s.close()
        return str(port)
        
    def getRandomFileName(self):
        return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
    
class Task(object):
    filename = ""
    uses_metasploit = False
    is_recursive = False
    
class WorkerThread(object):
    assignedTaskIDs = None
    assignedTasks = None
    position = 0
    
    footprint_id = 0
    
    isAlive = False
    
    metasploitProcess = None
    _msf_user = None
    _msf_pass = None
    _msf_port = None
    
    def init(self, _footprint_id, task_ids):
        self.assignedTaskIDs = []
        self.assignedTasks = {}
        self.position = 1
        self.isAlive = True
        
        self.footprint_id = _footprint_id
        self.assignedTaskIDs = task_ids
        
    def start(self):
        thread.start_new_thread(self.doWork, ())
    
    def stop(self):
        self.isAlive = False
    
    def startMetasploit(self, username, password, port):
        print "starting metasploit ..."
        metasploitProcess = subprocess.Popen('msfconsole'.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        gotCreds = False
        while gotCreds == False:
            metasploitProcess.poll()
            line = metasploitProcess.stdout.readline()

            if line != "":
                time.sleep(5)
                metasploitProcess.stdin.write("load msgrpc User={0} Pass={1} ServerPort={2}\n".format(username,  password,  port))
                time.sleep(2)
                gotCreds = True
        
        #print "metasploit running on 127.0.0.1:{0} with creds {1}:{2}".format(port, username, password)
        print ""
        

    def doWork(self):
        conf = ConfigParser.ConfigParser()
        conf.read("settings.ini")

        db = MySQLdb.connect(host=conf.get('MySQL',  'host'), user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
        db.autocommit(True)
        
        params = Params()
        params.db = db
        params.footprint_id = self.footprint_id
        params.log_queue = multiprocessing.Queue()
        
        uses_metasploit = False
        for id in self.assignedTaskIDs:
            cursor = db.cursor()
            cursor.execute("select file_name, uses_metasploit, is_recursive from task_descriptions where id = %s and enabled = 1", (id))
            row = cursor.fetchone()
            
            if row != None:
                print "loading module :: " + row[0]
                __import__(row[0])
                t = Task()
                t.file_name = row[0]
                t.uses_metasploit = (row[1] == '\x01')
                t.is_recursive = (row[2] == '\x01')
                self.assignedTasks[id] = t
                
                if t.uses_metasploit == True:
                    uses_metasploit = True
                
            cursor.close()
        print ""
        
        if uses_metasploit == True:
            params.msf_user = params.getRandomFileName()
            params.msf_pass = params.getRandomFileName()
            params.msf_port = params.getOpenPort()
            self.startMetasploit(params.msf_user, params.msf_pass, params.msf_port)
        
        while self.isAlive == True:
            runTask = False
            task_id = 0
            item_identifier = 0
            
            task = self.assignedTasks.values()[self.position - 1]
            
            if task.is_recursive:
                runTask = True
            else:
                cursor = db.cursor()
                cursor.execute("select id, item_identifier from task_list where footprint_id = %s and task_descriptions_id = %s and in_progress = 0 and completed = 0",  (self.footprint_id, self.assignedTasks.keys()[self.position - 1]))
                row = cursor.fetchone()
                cursor.close()
                if row != None:
                    runTask = True
                    task_id = row[0]
                    #item_identifier = row[1]
                    params.item_identifier = row[1]
                
                    spCursor = db.cursor()
                    spCursor.execute("call updateTaskStatus(%s, %s, %s, '')",  (task_id,  1,  0))
                    spCursor.close()
                    
            if runTask:
                print "===running module {0}===".format(task.file_name)
                #params.log("===running module {0}===".format(task.file_name))
                
                module = sys.modules[task.file_name]
                
                #p1 = multiprocessing.Process(target=module.run, args=(params, ))
                #p1.start()
                #p1.join()
                try:
                    if task.uses_metasploit == True:
                        p1 = multiprocessing.Process(target=module.run, args=(params, ))
                        p1.start()
                        p1.join()
                    else:
                        module.run(params)

                    del module
                except Exception as e:
                    print e

                msg = ""
                for i in range(0,  len(task.file_name) + 21):
                    msg = msg + "="

                time.sleep(0.25)
                
                final_output = ""
                while params.log_queue.empty() == False:
                    final_output += "{0}\r\n".format(params.log_queue.get(False))
                final_output = final_output[:-2]
                
                #final_output += "{0}\r\n".format(params.log_queue.get(False))
                #print """{0}""".format( final_output )
                
                print msg
                print ""
                
                if task.is_recursive == False:
                    spCursor = db.cursor()
                    spCursor.execute("call updateTaskStatus(%s, %s, %s, %s)",  ( task_id,  0,  1, final_output ))
                    spCursor.close()
            
            self.position += 1
            if self.position > len(self.assignedTasks):
                self.position = 1
                time.sleep(0.25)


    def doWorkold(self):
        conf = ConfigParser.ConfigParser()
        conf.read("settings.ini")

        db = MySQLdb.connect(host=conf.get('MySQL',  'host'), user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
        db.autocommit(True)
        
        params = Params()
        params.db = db
        params.footprint_id = self.footprint_id
        
        uses_metasploit = False
        for id in self.assignedTaskIDs:
            cursor = db.cursor()
            cursor.execute("select file_name, uses_metasploit, is_recursive from task_descriptions where id = %s and enabled = 1", (id))
            row = cursor.fetchone()
            
            if row != None:
                print "loading module :: " + row[0]
                __import__(row[0])
                t = Task()
                t.file_name = row[0]
                t.uses_metasploit = (row[1] == '\x01')
                t.is_recursive = (row[2] == '\x01')
                self.assignedTasks[id] = t
                
                if t.uses_metasploit == True:
                    uses_metasploit = True
                
            cursor.close()
        print ""
        
        if uses_metasploit == True:
            params.msf_user = params.getRandomFileName()
            params.msf_pass = params.getRandomFileName()
            params.msf_port = params.getOpenPort()
            self.startMetasploit(params.msf_user, params.msf_pass, params.msf_port)
        
        while self.isAlive == True:
            task = self.assignedTasks.values()[self.position - 1]
            
            if task.is_recursive:
                print "===running module {0}===".format(task.file_name)
                module = sys.modules[task.file_name]
                
                try:
                    if task.uses_metasploit == True:
                        #module.run(params)
                        p1 = multiprocessing.Process(target=module.run, args=(params, ))
                        p1.start()
                        p1.join()
                    else:
                        module.run(params)
                    
                    del module
                except Exception as e:
                    print e
                    
                msg = ""
                for i in range(0,  len(task.file_name) + 21):
                    msg = msg + "="
                print msg
                print ""
            else:
                cursor = db.cursor()
                cursor.execute("select id, item_identifier from task_list where footprint_id = %s and task_descriptions_id = %s and in_progress = 0 and completed = 0",  (self.footprint_id, self.assignedTasks.keys()[self.position - 1]))
                row = cursor.fetchone()
                if row != None:
                    print "===running module {0}===".format(task.file_name)
                    
                    spCursor = db.cursor()
                    spCursor.execute("call updateTaskStatus(%s, %s, %s, '')",  (row[0],  1,  0))
                    spCursor.close()
                    
                    try:
                        module = sys.modules[task.file_name]
                        params.item_identifier = row[1]
                        
                        if task.uses_metasploit == True:
                            #module.run(params)
                            p1 = multiprocessing.Process(target=module.run, args=(params, ))
                            p1.start()
                            p1.join()
                        else:
                            module.run(params)

                        del module
                        
                    except Exception as e:
                        print e
                        
                    msg = ""
                    for i in range(0,  len(task.file_name) + 21):
                        msg = msg + "="
                    print msg
                    print ""
                    
                    spCursor = db.cursor()
                    spCursor.execute("call updateTaskStatus(%s, %s, %s, '')",  (row[0],  0,  1))
                    spCursor.close()
                cursor.close()
            
            self.position += 1
            if self.position > len(self.assignedTasks):
                self.position = 1
                time.sleep(0.25)

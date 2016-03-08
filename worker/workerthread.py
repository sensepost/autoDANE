import thread
import time
import sys
import MySQLdb
import ConfigParser
import multiprocessing
import socket
import os
import random
import string
import asyncproc
import msfrpc
import netifaces

class Params(object):
    db = None
    footprint_id = None
    task_id = None
    item_identifier = None
    log_queue = None
    return_value_log = None
    
    msf_user = ""
    msf_pass = ""
    msf_port = "0"
    
    nmapTiming = None
    networkInterface = None
        
    retry_task = False
    
    def log(self, value):
        self.log_queue.put(value)
        print value
        
    def setReturnValue(self, value):
        self.return_value_log.put(value)
    
    def getLocalHost(self):
        #return os.popen('ifconfig eth0 | grep "inet addr" | cut -d \: -f 2 | cut -d \  -f 1').read()[:-1]
        #return os.popen('ifconfig tun0 | grep "inet addr" | cut -d \: -f 2 | cut -d \  -f 1').read()[:-1]
        return netifaces.ifaddresses(str(self.networkInterface))[netifaces.AF_INET][0]['addr']
        
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
    _test_depth = 0
    isAlive = False
    
    metasploitProcess = None
    _msf_user = None
    _msf_pass = None
    _msf_port = None
    
    _nmapTiming = None
    _networkInterface = None
    
    def init(self, _footprint_id, task_ids, test_depth, nmapTiming, networkInterface):
        self.assignedTaskIDs = []
        self.assignedTasks = {}
        self.position = 1
        self.isAlive = True
        self._test_depth = test_depth
        self._nmapTiming = nmapTiming
        self._networkInterface = networkInterface
        
        self.footprint_id = _footprint_id
        self.assignedTaskIDs = task_ids
        
    def start(self):
        thread.start_new_thread(self.doWork, ())
        #self.doWork()
    
    def stop(self):
        self.isAlive = False
        try:
            self.metasploitProcess.kill(0)
        except:
            pass
    
    def testMsfConnection(self, username, password, port, log):
        try:
            client = msfrpc.Msfrpc({'port':int(port)})
            client.login(user=username, password=password)
            res = client.call('console.create')
            
            console_id = res['id']
            log.put("success")
        except:
            log.put("fail")
    
    def startMetasploit(self, username, password, port):
        print "starting metasploit ..."
        gotConsole = False
        rpcStarted = False
        rpcRunning = False
        self.metasploitProcess = asyncproc.Process("msfconsole -m software/metasploit/modules/".split())
        startTime = time.time()
        
        while rpcRunning == False:
            if time.time() - startTime >= 60:
                print "timeout.will try again"
                break
            
            poll = self.metasploitProcess.wait(os.WNOHANG)
            if poll != None:
                #break
                time.sleep(1)

            out = self.metasploitProcess.read()
            gotConsole = False
            if out != "":
                #print out.strip()
                #if repr(out) == repr("\x1b[4mmsf\x1b[0m \x1b[0m> "):
                if repr(out).find(repr("\x1b[4mmsf\x1b[0m \x1b[0m> ")) != -1:
                    gotConsole = True

                if rpcStarted == True:
                    if out.find("Successfully loaded plugin: msgrpc") != -1:
                        rpcRunning = True


            if gotConsole == True:
                if rpcStarted == False:
                    time.sleep(1)
                    self.metasploitProcess.write("load msgrpc User={0} Pass={1} ServerPort={2}\n".format(username,  password,  port))
                    rpcStarted = True

        
        if rpcRunning == True:
            print "metasploit running on 127.0.0.1:{0} with creds {1}:{2}".format(port, username, password)
        else:
            print "there was a error starting the metasploit console"
            try:
                self.metasploitProcess.kill(0)
            except:
                pass

    def doWork(self):
        conf = ConfigParser.ConfigParser()
        conf.read("settings.ini")

        db = MySQLdb.connect(host=conf.get('MySQL',  'host'), user=conf.get('MySQL',  'user'), passwd=conf.get('MySQL',  'pass'), db=conf.get('MySQL',  'db'))
        db.autocommit(True)
        
        params = Params()
        params.db = db
        params.db.autocommit(True)
        params.footprint_id = self.footprint_id
        params.log_queue = multiprocessing.Queue()
        params.return_value_log = multiprocessing.Queue()
        params.nmapTiming = self._nmapTiming
        params.networkInterface = self._networkInterface
        
        uses_metasploit = False
        for id in self.assignedTaskIDs:
            cursor = db.cursor()
            cursor.execute("select td.file_name, td.uses_metasploit, td.is_recursive from task_descriptions td join task_categories tc on tc.id = td.task_categories_id where td.id = %s and td.enabled = 1 and tc.position_id <= %s", (id, self._test_depth, ))
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
            msfCanConnect = False
            log = multiprocessing.Queue()
            
            while msfCanConnect == False:
                params.msf_user = params.getRandomFileName()
                params.msf_pass = params.getRandomFileName()
                params.msf_port = params.getOpenPort()
                self.startMetasploit(params.msf_user, params.msf_pass, params.msf_port)
                
                p1 = multiprocessing.Process(target=self.testMsfConnection, args=(params.msf_user, params.msf_pass, params.msf_port, log, ))
                p1.start()
                p1.join()
                
                while log.empty() == False:
                    logval = log.get(False)
                    if logval == "success":
                        msfCanConnect = True
                        print "[+] connected successfully"
                    else:
                        print "[!] could not connect"
                        try:
                            self.metasploitProcess.kill(9)
                        except:
                            pass
                        time.sleep(1)

        
        if len(self.assignedTasks.values()) == 0:
            self.isAlive = False
        
        while self.isAlive == True:
            try:
                runTask = False
                task_id = 0
                #item_identifier = 0
                
                task = self.assignedTasks.values()[self.position - 1]
                
                if task.is_recursive:
                    runTask = True
                else:
                    cursor = db.cursor()
                    cursor.execute("call getPendingTask(%s, %s)",  (self.footprint_id, self.assignedTasks.keys()[self.position - 1], ))
                    row = cursor.fetchone()
                    cursor.close()
                    #cursor = db.cursor()
                    #cursor.execute("select id, item_identifier from task_list where footprint_id = %s and task_descriptions_id = %s and in_progress = 0 and completed = 0",  (self.footprint_id, self.assignedTasks.keys()[self.position - 1]))
                    #row = cursor.fetchone()
                    #cursor.close()
                    #if row != None:
                    if row[0] != 0:
                        runTask = True
                        task_id = row[0]
                        #item_identifier = row[1]
                        params.task_id = task_id
                        params.item_identifier = row[1]
                    
                        #spCursor = db.cursor()
                        #spCursor.execute("call updateTaskStatus(%s, %s, %s, '')",  (task_id,  1,  0))
                        #spCursor.close()
                        
                if runTask:
                    if task.is_recursive == False:
                        print "===running module {0}===".format(task.file_name)
                    try:
                    #if True:
                        #params.log("===running module {0}===".format(task.file_name))
                        
                        module = sys.modules[task.file_name]
                        
                        #p1 = multiprocessing.Process(target=module.run, args=(params, ))
                        #p1.start()
                        #p1.join()
                        try:
                        #if True:
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
                        
                        if task.is_recursive == False:
                            print msg
                            print ""
                        
                        runAgain = False
                        in_progress = 0
                        completed = 1
                        
                        while params.return_value_log.empty() == False:
                            if params.return_value_log.get(False) == "run again":
                                runAgain = True
                        
                        if task.is_recursive == False:
                            if runAgain:
                                in_progress = 0
                                completed = 0
                                
                            spCursor = db.cursor()
                            spCursor.execute("call updateTaskStatus(%s, %s, %s, %s)",  ( task_id,  in_progress,  completed, final_output, ))
                            spCursor.close()
                        
                    except Exception as e:
                        print e
                        spCursor = db.cursor()
                        spCursor.execute("call updateTaskStatus(%s, %s, %s, %s)",  ( task_id,  False,  False, e, ))
                        spCursor.close()
                        time.sleep(5)
                
                self.position += 1
                if self.position > len(self.assignedTasks):
                    self.position = 1
                    time.sleep(0.25)
            except:
                time.sleep(1)

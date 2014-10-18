import time
import paramiko
import urllib2
import SocketServer
import threading
class RequestManager :
    """
    ----------------------------------------------
    ----------------------------------------------
    """
    response = 'data'
    
    url_check_Eready = '/Father'
    url_set_W_WaitOrder = '/OrderAndIWillObey'
    url_set_W_HaveResult = '/FatherIGotYourAnswer'

    E_isReady = False
    W_isReady = False
    W_still_Writing = False
    
    oK = 'OK'
    kO = 'KO'

    HTML_PREFIX = '<!DOCTYPE HTML><html><p>'
    HTML_SUFFIX = '</p></html>'

    EOT = 'DEADBEEF'
    
    BUFFER_SSH_TO_HTTP = 'ls -la'
    BUFFER_HHTP_TO_SHH = ''

    @staticmethod
    def doesSSHReady_E():
        """
        Check if we have an SSH client on localhost (E)
        """
        return RequestManager.E_isReady == True
   
    @staticmethod
    def doesW_WaitingOrder():
        """
        Check if E and W are ready to communicate
        """
        return RequestManager.W_isReady == True and RequestManager.E_isReady == True
    

    @staticmethod
    def htmlTemplate(content):
        """
        Return an HTML page using the argument
        """    
        html = RequestManager.HTML_PREFIX+content.__str__()+RequestManager.HTML_SUFFIX
        return html
    
    @staticmethod
    def convertData(string):
        """
        Convert our data to an HTML data (Respect the protocol)
        """
        return RequestManager.htmlTemplate(string)


    
    @staticmethod
    def getClearData(string):
        """
        Return the clear data without HTML tags
        """
        strr = string.replace(RequestManager.HTML_PREFIX, '')
        strr = strr.replace(RequestManager.HTML_SUFFIX, '')
        return strr


    @staticmethod
    def getResult(req):
        """
        Treat the req and strip the result and return it
        """
        tmp = RequestManager.requestToString(req)
        tab_temp = tmp.split('?')
        keyword = tab_temp[0]+'?'
        tmp = tmp.replace(keyword, '')
        return RequestManager.getClearData(tmp)


    @staticmethod
    def request(url):
        """
        Conncect to url and return the response
        """
        print "Requesting ==> "+url
        result = RequestManager.kO
        try:
            request = urllib2.Request(url)
            connexion = urllib2.urlopen(request)
            result = connexion.readline()
            result = RequestManager.getClearData(result)
        except:
            pass     
        print "Answer ==> "+result
        return result











class W_Slave(threading.Thread): 
    """
    ----------------------------------------------
    Help us to launch W-P html interractions as a Job
    ----------------------------------------------
    """

    def __init__(self, nom, action='Running'):
        threading.Thread.__init__(self) 
        self.nom = nom 
        self.action = action


    def run(self):
        print time.asctime(), ' ::: '+self.action+' '+self.nom.__str__()+' to reach '+W_Bot.BASE_URL+'....'
        try:
            W_Bot.beSlaveForEver()
        except KeyboardInterrupt:
            print "Interrupt"
        print time.asctime()




class W_Master(threading.Thread): 
    """
    ----------------------------------------------
    Help us to open SSH connection on W and execute commands and get their results
    ----------------------------------------------
    """

    def __init__(self, nom, action='Running'):
        threading.Thread.__init__(self) 
        self.nom = nom 
        self.action = action


    def run(self):
        print time.asctime(), ' ::: '+self.action+' '+self.nom.__str__()+'waiting....'
        try:
            W_Bot.beSlaveForEver()
        except KeyboardInterrupt:
            print "Interrupt"
            
        print time.asctime()




class W_Bot:
    """
    ----------------------------------------------
    Help us to lauch W functions
    ----------------------------------------------
    """

    TIME_TO_WAIT = 5
    BASE_URL = ''

    @staticmethod
    def beSlaveForEver():
        """
        This is our principal method which is charged to manage E requestsand open a SSH connection on W
        """
        while True:
            # On verifie si E est pret en SSH
            while not RequestManager.E_isReady:
                W_Bot.sleep()
                print "E is not Ready"
                W_Bot.checkE_Ready()
            # Quand E est pret et que la connexion en SSH de W n'est pas encore ouverte on l'ouvre
            if RequestManager.E_isReady and not RequestManager.W_isReady:
                print "E is ready"
                W_Bot.openSSH()

            # Quand E et W sont prets en SSH on peut commencer la communication
            if RequestManager.doesW_WaitingOrder():
                """
                command = W_Bot.askCommand()
                #E est aussi pret ET a envoye une commande
                if command != RequestManager.kO:                    #On ecrit la commande dans le BUFFER_HTTP_TO_SSH
                    pass
                
                """
    
    @staticmethod
    def openSSH():
        """
        Open an SSH connection on W localhost
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('127.0.0.1', username='doc', 
            password='0irakboss')

        stdin, stdout, stderr = ssh.exec_command(
            "vim Bureau/test2.html")
        stdin.flush()
        data = stdout.read()
        print data
        RequestManager.W_isReady = True



    @staticmethod
    def sleep():
        """
        Just apply a sleep
        """
        time.sleep(W_Bot.TIME_TO_WAIT)



    @staticmethod
    def checkE_Ready():
        """
        check if E has a client on SSH
        """
        url = W_Bot.BASE_URL+RequestManager.url_check_Eready
        if RequestManager.request(url) == RequestManager.oK:
            RequestManager.E_isReady = True;
        else:
            RequestManager.E_isReady = False







    @staticmethod
    def askCommand():
        """
        Ask a command to E
        """
        return RequestManager.request(RequestManager.url_set_W_WaitOrder)




class ServJob(threading.Thread): 
    """
    ----------------------------------------------
    Help us to launch Servers threads on E machine
    ----------------------------------------------
    """

    def __init__(self, nom, port, handler, action='Running'):
        threading.Thread.__init__(self) 
        self.nom = nom 
        self.port = port
        self.handler = handler
        self.action = action


    def run(self):
        print time.asctime(), ' ::: '+self.action+' '+self.nom.__str__()+' at port '+self.port.__str__()+' ......'
        serv = SocketServer.TCPServer(('', self.port), self.handler)
        try:
            serv.serve_forever()
        except KeyboardInterrupt:
            print "Interrupt"
            serv.server_close()
            
        serv.server_close()
        print time.asctime()

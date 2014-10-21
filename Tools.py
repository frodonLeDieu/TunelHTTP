import time
import select
import socket
import base64
import paramiko
import urllib2
import SocketServer
import threading
from multiprocessing import Lock

# Semaphores pour BUFFERS de W
lockH = Lock()  #La semaphore sur la ressource BUFFER_HTTP_TO_SHH
lockS = Lock()  #La semaphore sur la ressource BUFFER_SSH_TO_HTTP
class RequestManager :
    """
    ----------------------------------------------
    ----------------------------------------------
    """
    response = 'data'
    
    url_check_Eready = '/Father'
    url_set_W_WaitOrder = '/YourWillMyOrder'
    url_set_W_HaveResult = '/FatherIGotSomething'
    E_isReady = False
    W_isReady = False
    W_still_Writing = False
    E_can_Read = False
    W_can_Read = False
    W_can_Write = False
    oK = 'OK'
    kO = 'KO'
    HTML_PREFIX = '<!DOCTYPE HTML><html><head><title>A big good site</title></head><body><div class="content"><p>'
    HTML_SUFFIX = '</p></div></html>'
    EOT = 'DEADBEEF'
    MAX_SIZE_GET = 255
    MAX_SIZE_PAGE = 4096 
    BUFFER_SSH_TO_HTTP = ''
    BUFFER_HTTP_TO_SSH = ''

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
        return strr.replace(RequestManager.HTML_SUFFIX, '')


    @staticmethod
    def isResultRequest(req):
        """
        Tell us if the request req is an result request
        """
        tmp = req
        tab_temp = tmp.split('?')
        if len(tab_temp) > 1:
            keyword = tab_temp[0]
            if keyword == RequestManager.url_set_W_HaveResult:
                return True
        return False



    @staticmethod
    def getResult(req):
        """
        Treat the req and strip the result and return it
        """
        tmp = req
        tab_temp = tmp.split('?')
        keyword = tab_temp[0]
        tmp = tmp.replace(keyword, '')
        tmp = tmp.replace('?'+RequestManager.response+'=', '')
        return tmp


    @staticmethod
    def request(url, requester):
        """
        Conncect to url and return the response
        """
        print "[", requester,"] (Requesting) => ",url
        result = RequestManager.kO
        try:
            request = urllib2.Request(url)
            connexion = urllib2.urlopen(request)
            result = connexion.readline()
            result = RequestManager.getClearData(result)
        except:
            pass     
        print "[", requester,"] (Answer) => ",result
        return result


    @staticmethod
    def sendResult(result, requester):
        the_url = W_Bot.BASE_URL+RequestManager.url_set_W_HaveResult
        print "[", requester,"] (Sending Result) to ",the_url
        ret = RequestManager.kO
        #try:
        req = urllib2.Request(the_url, result)
        handle = urllib2.urlopen(req)
        result = handle.read()
        result = RequestManager.getClearData(result)
        #except:
        #pass     
        print "[", requester,"] (Answer) => ",result
        return ret


    @staticmethod
    def receive(socket, size):
        buf = "" # Variable dans laquelle on stocke les donnees
        _hasData = True # Nous permet de savoir si il y de donnees a lire
        while _hasData:
            # On passe le socket en non-bloquant
            socket.setblocking( 0)
            try:
                _data = socket.recv(size)
                if( _data):
                    buf += _data
                else:
                    # Deconnexion du client
                    _hasData = False
            except:
                _hasData = False
        return buf


    @staticmethod
    def formatResult(result):
        """
        Strip our data in part of 255 char max
        """
        i = 0
        tmp = ''
        table = []
        if len(result) > RequestManager.MAX_SIZE_GET:
            for char in result:
                i = i+1
                tmp += char
                if i == RequestManager.MAX_SIZE_GET:
                    table.append(tmp)
                    tmp = ''
                    i = 0
            if tmp != '':
                table.append(tmp)
        else:
            table.append(result)
        return table




class W_Slave(threading.Thread): 
    """
    ----------------------------------------------
    Help us to launch W-P html interractions and ssh things as a Job
    ----------------------------------------------
    """
    def __init__(self, nom, handler, action='Running'):
        threading.Thread.__init__(self) 
        self.nom = nom 
        self.action = action
        self.handler = handler

    def run(self):
        print time.asctime(), ' ::: '+self.action+' '+self.nom.__str__()+' to reach '+W_Bot.BASE_URL+'....'
        self.handler()
        print time.asctime()




class W_Bot:
    """
    ----------------------------------------------
    Help us to lauch W functions
    ----------------------------------------------
    """
    SSH_CLIENT = ''
    TIME_TO_WAIT = 5
    BASE_URL = ''
    PORT = 22

    @staticmethod
    def beSlaveForEver2():
        """
        This is our principal method which is charged to manage E requestsand open a SSH connection on W
        """
        while True:
            # On verifie si E est pret en SSH
            requester = "Slave2" 
            print "[",requester,"] : Checking E disponibility"
            while not RequestManager.E_isReady:
                W_Bot.sleep()
                W_Bot.checkE_Ready(requester)
            # Quand E est pret et que la connexion en SSH de W n'est pas encore ouverte on l'ouvre
            if RequestManager.E_isReady:
                RequestManager.W_isReady = True
            # Quand E et W sont prets en SSH on peut commencer la communication
            if RequestManager.W_isReady and RequestManager.E_isReady:
                print "[",requester,"] : Both are available"
                print "[",requester,"] : Waiting to read BUFFER_SSH_TO_HTTP"
                while not RequestManager.W_can_Write: 
                    time.sleep(0.1)
                if RequestManager.W_can_Write:
                    lockS.acquire()
                    RequestManager.W_can_Write = False
                    result = RequestManager.BUFFER_SSH_TO_HTTP
                    RequestManager.BUFFER_SSH_TO_HTTP = ''
                    lockS.release()
                    print "\n[BUFFER_SSH_TO_HTTP] --> E\n", result
                    RequestManager.sendResult(base64.b64encode(result), requester)
                    """
                    list_result = RequestManager.formatResult(result)
                    for string in list_result:
                        code = base64.b64encode(string)
                        url = W_Bot.BASE_URL+RequestManager.url_set_W_HaveResult+'?'+RequestManager.response+'='+code
                        state = RequestManager.request(url, requester)

                    url = W_Bot.BASE_URL+RequestManager.url_set_W_HaveResult+'?'+RequestManager.response+'='+RequestManager.EOT
                    state = RequestManager.request(url, requester)
                    """

    @staticmethod
    def beSlaveForEver():
        """
        This is our principal method which is charged to manage E requestsand open a SSH connection on W
        """
        while True:
            requester = "Slave1" 
            print "[",requester,"] : Checking E disponibility"
            # On verifie si E est pret en SSH
            while not RequestManager.E_isReady:
                W_Bot.sleep()
                W_Bot.checkE_Ready(requester)
            # Quand E est pret et que la connexion en SSH de W n'est pas encore ouverte on l'ouvre
            if RequestManager.E_isReady:
                #print "E is ready"
                #W_Bot.openSSH()
                #print "SSH OPENED on W"
                RequestManager.W_isReady = True
            # Quand E et W sont prets en SSH on peut commencer la communication
            if RequestManager.doesW_WaitingOrder():
                print "[",requester,"] : Both are available"
                #print "E is ready on SSH, W too"
                data = W_Bot.askData(requester)

                # Redemander le paquet tant qu'on en a pas recu un correct
                while data == RequestManager.kO:
                    W_Bot.sleep()
                    data = W_Bot.askData(requester)
                #E est aussi pret ET a envoye une donnee
                if data != RequestManager.kO:                   
                    #On ecrit notre data sur W_SSH
                    lockH.acquire()
                    RequestManager.W_can_Read = False
                    RequestManager.BUFFER_HTTP_TO_SSH = base64.b64decode(data)
                    print "\n[BUFFER_HTTP_TO_SSH] <-- E\n"
                    print RequestManager.BUFFER_HTTP_TO_SSH
                    RequestManager.W_can_Read = True
                    lockH.release()


    @staticmethod
    def sleep():
        """
        Just apply a sleep
        """
        time.sleep(W_Bot.TIME_TO_WAIT)



    @staticmethod
    def checkE_Ready(requester):
        """
        check if E has a client on SSH
        """
        url = W_Bot.BASE_URL+RequestManager.url_check_Eready
        if RequestManager.request(url, requester) == RequestManager.oK:
            RequestManager.E_isReady = True;
        else:
            RequestManager.E_isReady = False


    @staticmethod
    def askData(requester):
        """
        Ask a data to E
        """
        return RequestManager.request(W_Bot.BASE_URL+RequestManager.url_set_W_WaitOrder, requester)




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
        serv.serve_forever()
        print time.asctime()



class SockListenerJob(ServJob): 
    """
    ----------------------------------------------
    Help us to listen on a socket
    ----------------------------------------------
    """
    def run(self):
        # Create a TCP/IP socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setblocking(0)
        # Bind the socket to the port
        server_address = ('localhost', self.port)
        server.bind(server_address)
        print time.asctime(), ' ::: '+self.action+' '+self.nom.__str__()+' at port '+self.port.__str__()+' ......'
        # Sockets from which we expect to read
        inputs = [ server ]
        outputs = [ ]
        self.handler(inputs, outputs, server)
        print "End at",time.asctime()

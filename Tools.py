import time
import select
import socket
import urllib2
import urllib
import SocketServer
import threading
from random import choice
from multiprocessing import Lock

liste_alea = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','0','1','2','3','4','5','6','7','8','9']
class RequestManager :
    """ Class with static methods and attribute which help manage request """
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
    AVAILABLE = False
    BASE_URL = ''
    PROXY =''
    USER_AGENTS = ['Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11', 'Opera/9.25 (Windows NT 5.1; U; en)', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)', 'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12', 'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9']

    @staticmethod
    def doesSSHReady_E():
        """ Check if we have an SSH client on localhost (E) """
        return RequestManager.E_isReady == True
   
    @staticmethod
    def doesW_WaitingOrder():
        """ Check if E and W are ready to communicate """
        return RequestManager.W_isReady == True and RequestManager.E_isReady == True

    @staticmethod
    def htmlTemplate(content):
        """ Return an HTML page using the argument"""
        html = RequestManager.HTML_PREFIX+content.__str__()+RequestManager.HTML_SUFFIX
        return html
    
    @staticmethod
    def convertData(string):
        """ Convert our data to an HTML data (Respect the protocol) """
        return RequestManager.htmlTemplate(string)
    @staticmethod
    def getClearData(string):
        """ Return the clear data without HTML tags """
        strr = string.replace(RequestManager.HTML_PREFIX, '')
        return strr.replace(RequestManager.HTML_SUFFIX, '')

    @staticmethod
    def applyProxy():
        proxy  = urllib2.ProxyHandler({'http': RequestManager.PROXY})
        opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)

    
    @staticmethod
    def chunkUrl(url):
        global liste_alea
        a = choice(liste_alea)
        b = choice(liste_alea)
        c = choice(liste_alea)
        d = choice(liste_alea)
        e = choice(liste_alea)
        f = choice(liste_alea)
        g = choice(liste_alea)
        h = choice(liste_alea)
        i = choice(liste_alea)
        j = choice(liste_alea)
        k = choice(liste_alea)
        l = choice(liste_alea)
        m = choice(liste_alea)
        n = choice(liste_alea)
        o = choice(liste_alea)
        p = choice(liste_alea)
        tmp = a+b+c+d+e+f+g+h+i+j+m+n+o+p+d+g+a+h+j+i+k+l+m+i+h+d+e+c+i+p+a+j+j+j+j+j+k+l+m+o+p
        return url+tmp
    @staticmethod
    def request(url, requester):
        """ Conncect to url and return the response """
        result = RequestManager.kO
        ua = choice(RequestManager.USER_AGENTS) 
        request = urllib2.Request(RequestManager.chunkUrl(url))
        request.add_header("User-agent", ua)
        request.add_header("Cache-Control", "max-age=0")
        request.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        request.add_header("Connection", "keep-alive")
        if RequestManager.PROXY != '':
            RequestManager.applyProxy()
        connexion = urllib2.urlopen(request)
        result = connexion.readline()
        result = RequestManager.getClearData(result)
        return result


    @staticmethod
    def sendResult(result, requester):
        """ Send our result by POST method """
        the_url = RequestManager.BASE_URL+RequestManager.url_set_W_HaveResult
        the_url = RequestManager.chunkUrl(the_url)
        ret = RequestManager.kO
        ua = choice(RequestManager.USER_AGENTS) 
        parameters = {'Data' : str(result) }
        #result = urllib.urlencode(parameters) 
        result = urllib.urlencode(parameters) 
        size = len(result)    
        headers = {
            'Host' : 'FrodonHome',
            'Connection' : 'keep-alive',
            'User-agent' : ua,
            'Content-type' : 'application/x-www-form-urlencoded;',
            'Accept' : '*/*'
        }
        req = urllib2.Request(the_url, result, headers)
        #print result
        #req = urllib2.Request(the_url, RequestManager.cesar_all(result, 7), headers)
        if RequestManager.PROXY != '':
            RequestManager.applyProxy()
        handle = urllib2.urlopen(req)
        result = handle.read()
        result = RequestManager.getClearData(result)
        return ret


    @staticmethod
    def receive(socket, size):
        """ Read all content of the socket """
        buf = ""
        _hasData = True 
        while _hasData:
            socket.setblocking( 0)
            try:
                _data = socket.recv(size)
                if( _data):
                    buf += _data
                else:
                    _hasData = False
            except:
                _hasData = False
        return buf

    @staticmethod
    def cesar_all(string, decalage):
        res = ''
        for char in string:
            res += RequestManager.cesar(char, decalage)
            return res

    @staticmethod
    def cesar(char, decalage):
        min_list = 'abcdefghijklmnopqrstuvwxyz'
        maj_list = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        if char in min_list:
            return min_list[(min_list.index(char)+decalage)%26]
        if char in maj_list:
            return maj_list[(maj_list.index(char)+decalage)%26]
        return char


class W_Slave(threading.Thread): 
    """ Help us to launch W-P html interractions and ssh things as a Job """
    def __init__(self, nom, handler, action='Running'):
        threading.Thread.__init__(self) 
        self.nom = nom 
        self.action = action
        self.handler = handler
        print time.asctime(), ' ::: '+str(self.action)+' '+self.nom.__str__()

    def run(self):
        self.handler()
        print time.asctime()


class ServJob(W_Slave): 
    """ Help us to launch HTTPServer on E """
    def __init__(self, nom, handler, port, action='Running'):
        W_Slave.__init__(self, nom, handler, action)
        self.port = port


    def run(self):
        serv = SocketServer.TCPServer(('', self.port), self.handler)
        serv.serve_forever()



class SockListenerJob(ServJob): 
    """ Help us to listen on the socket on E """
    def run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setblocking(0)
        server_address = ('localhost', self.port)
        server.bind(server_address)
        inputs = [server ]
        outputs = [ ]
        self.handler(inputs, outputs, server)


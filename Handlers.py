import select
import socket
import sys
import Queue
import time

import SocketServer
import base64
from Tools import RequestManager
import SimpleHTTPServer
from multiprocessing import Lock

# Semaphores pour BUFFERS de E
lockH = Lock()  #La semaphore sur la ressource BUFFER_HTTP_TO_SHH
lockS = Lock()  #La semaphore sur la ressource BUFFER_SSH_TO_HTTP

 
class MyHTTPHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """
    Handle HTTP request 
    Redirect request and manage the responses sent by Our SSH handler
    """
        
    def sendHeaders(self, code, cType, size):
        """
        Sends specifics header to the proxy
        """
        self.send_response(code)
        self.send_header("Content-type", cType)
        self.send_header("Content-length", size.__str__())
        self.end_headers()
    

    def answerToClient(self, html, code, cType):
        """
        Send answer to client (the proxy in fact), build header and content
        """
        if code != 200:
            self.send_error(code,html.encode())
        else:
            self.sendHeaders(code, cType, len(html))
            self.wfile.write(html.encode())

    def do_POST(self):
        req = self.path
        if req == RequestManager.url_set_W_HaveResult:
            print '\n----------------------------------------'
            print 'DATA RECEIVED'
            print '----------------------------------------\n'
            content_len = int(self.headers.getheader('content-length', 0))
            result = self.rfile.read( content_len)
            ############# RECEIVING RESULT FROM W #################   
            #Si on a toujours une connection en SSH on ecrit le resultat dans le BUFFER_HTTP_TO_SSH de E
            if RequestManager.doesSSHReady_E:
                #print "E is ready"
                #HHTP_HANDLER prend le verou H ou essaye
                #print "E take locH for first time"
                lockH.acquire()
                RequestManager.E_can_Read = False
                # Fin de la donnee que W a envoyer
                RequestManager.BUFFER_HTTP_TO_SSH = base64.b64decode(result)
                #Informer E_SSH qu'il peut maintenant lire le contenu de BUFFER_HTTP_TO_SSH
                RequestManager.E_can_Read = True
                print "[BUFFER_HTTP_TO_SSH] <-- W\n", RequestManager.BUFFER_HTTP_TO_SSH
                #print "E releases lockH"
                lockH.release()
                #On repond OK a W
                html = RequestManager.convertData(RequestManager.oK)
                self.answerToClient(html, 200, 'text/html')
            else:
                html = RequestManager.convertData(RequestManager.kO)
                self.answerToClient(html, 200, 'text/html')



    def do_GET(self):
        """
        Our Get implementation which handles all get requests
        """
        print '\n----------------------------------------'
        print 'HTTP_REQUEST'
        print '----------------------------------------\n'
        #print "{} wrote:".format(self.client_address[0])
        #print self.path
        req = self.path
        #Verifie que la requete demande l'etat du ssh chez E et si E est pret en ssh
        ############# RECEIVING "PING" FROM W #################   
        #Le client tente de savoir si E est pret en SSH
        if req == RequestManager.url_check_Eready:
            if RequestManager.doesSSHReady_E():
                res = RequestManager.oK
            else:
                res = RequestManager.kO
            html = RequestManager.convertData(res)
            #print html.__str__()
            self.answerToClient(html, 200, 'text/html')
       
       
       
       #############SENDING COMMANDS TO W #################   
        #On a un client en ssh local sur E et W nous indique qu'il est pret pour a communication et pour recevoir des ordres ;)
        elif req == RequestManager.url_set_W_WaitOrder:
            #Le client ssh sur W est pret
            RequestManager.W_isReady = True
            #Si W et E sont prets en SSH
            if RequestManager.doesW_WaitingOrder():
                #Si on a du contenu dans le BUFFER_SSH_TO_HTTP de E, on l'envoi a notre client par le biais du proxy
                if RequestManager.BUFFER_SSH_TO_HTTP != '':
                    #HHTP_HANDLER prend le verou S ou essaye
                    print "\n[BUFFER_SSH_TO_HTTP] --> W\n"
                    lockS.acquire()
                    data = RequestManager.BUFFER_SSH_TO_HTTP
                    print data
                    html = RequestManager.convertData(base64.b64encode(data))
                    print base64.b64encode(data)
                    self.answerToClient(html, 200, 'text/html')
                    RequestManager.BUFFER_SSH_TO_HTTP = ''
                    lockS.release()
                else:
                    #Aucun contenu dans le buffer
                    print "Nothing to send to W\n"
                    html = RequestManager.convertData(RequestManager.kO)
                    self.answerToClient(html, 200, 'text/html')
            else : 
                #E et/ou W ne sont pas prets
                html = RequestManager.convertData(RequestManager.kO)
                self.answerToClient(html, 200, 'text/html')



        ############# OTHER REQUESTS #################   
        #Pour toute autre requete on repond KO
        else:
            html = RequestManager.convertData(RequestManager.kO)
            self.answerToClient(html, 200, 'text/html')


class MySSHHandler():
    """
    Handle our SSH request and responses
    """
    @staticmethod
    def handle_E(inputs, outputs, server):
        # Listen for incoming connections
        server.listen(1)
        inputt = [server]

        while True:   
            inputready,outputready,exceptready = select.select(inputt,inputt,[])
            for s in inputready:
                if s is server:
                    # handle the server socket
                    print "New client on E_SSH via select"
                    client, address = server.accept()
                    inputt.append(client)
                    RequestManager.E_isReady = True
                else:
                    # Handle all other sockets
                    data = RequestManager.receive(s, RequestManager.MAX_SIZE_PAGE)
                    if data:
                        # On enregistre notre data dans le BUFFER_SHH_TO_HTTP de E pour l'envoie
                        lockS.acquire()
                        RequestManager.BUFFER_SSH_TO_HTTP += data
                        lockS.release()
                        print "-----------------------------"
                        print "SSH LINE OUT"
                        print "-----------------------------"
                        #print data
                        #while not RequestManager.E_can_Read:
                            #time.sleep(0.1)
                        # Si E peut lire BUFFER_HTTP_TO_SSH


            for s in outputready:
                if s is not server:
                    if RequestManager.E_can_Read:
                        print "-----------------------------"
                        print "SSH LINE IN"
                        print "-----------------------------"
                        lockH.acquire()
                        #print  RequestManager.BUFFER_HTTP_TO_SSH
                        s.send(RequestManager.BUFFER_HTTP_TO_SSH)
                        RequestManager.E_can_Read = False
                        RequestManager.BUFFER_HTTP_TO_SSH = ''
                        lockH.release()

    @staticmethod
    def handle_W():
        # Create a TCP/IP socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server.setblocking(0)
        # Bind the socket to the port
        # server_address = ('localhost', W_Bot.PORT)
        while not RequestManager.E_isReady:
            time.sleep( 0.1)

        server.connect(('localhost', 22))
        # Listen for incoming connections
        # server.listen(1)
        # Sockets from which we expect to read
        inputs = [ server ]
        outputs = [ ] 
        while True:   
            if RequestManager.E_isReady:
                readable, writable, exceptional = select.select(inputs, inputs, []) 
                # Handle W output
                for s in readable:
                    if s is server:
                        # On a des donnees en retour
                        data = RequestManager.receive(s, RequestManager.MAX_SIZE_PAGE)
                        if data : 
                            print "-----------------------------"
                            print "SSH LINE OUT"
                            print "-----------------------------"
                            print data
                            lockS.acquire()
                            RequestManager.W_can_Write = False
                            RequestManager.BUFFER_SSH_TO_HTTP += data
                            RequestManager.W_can_Write = True
                            lockS.release()
                            #print "Relache du lockS sur BUFFER_SSH_TO_HTTP"
                            #while not RequestManager.W_can_Read:
                                #time.sleep(0.1)
                            # Si W peut lire BUFFER_HTTP_TO_SSH
                for s in writable:
                    if RequestManager.W_can_Read:
                        #print "W peut peut lire sur BUFFER_HTTP_TO_SSH"
                        #print "Data to send on SSH 22 ", RequestManager.BUFFER_HTTP_TO_SSH
                        lockH.acquire()
                        print "-----------------------------"
                        print "SSH LINE IN"
                        print "-----------------------------"
                        #print str(RequestManager.BUFFER_HTTP_TO_SSH)
                        s.send(RequestManager.BUFFER_HTTP_TO_SSH)
                        RequestManager.BUFFER_HTTP_TO_SSH = ''
                        RequestManager.W_can_Read = False
                        lockH.release()

import select
import socket
import sys
import Queue

import SocketServer
import base64
from Tools import RequestManager
import SimpleHTTPServer
from multiprocessing import Lock

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


    def do_GET(self):
        """
        Our Get implementation which handles all get requests
        """
        print '\n----------------------------------------'
        print 'HTTP_REQUEST'
        print '----------------------------------------\n'
        print "{} wrote:".format(self.client_address[0])
        print self.path
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
            print html.__str__()
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
                    lockS.acquire()
                    html = RequestManager.convertData(RequestManager.BUFFER_SSH_TO_HTTP)
                    self.answerToClient(html, 200, 'text/html')
                    RequestManager.BUFFER_SSH_TO_HTTP = ''
                    lockS.release()
                else:
                    #Aucun contenu dans le buffer
                    html = RequestManager.convertData(RequestManager.kO)
                    self.answerToClient(html, 200, 'text/html')
            else : 
                #E et/ou W ne sont pas prets
                html = RequestManager.convertData(RequestManager.kO)
                self.answerToClient(html, 200, 'text/html')


        ############# RECEIVING RESULT FROM W #################   
        elif RequestManager.isResultRequest(req):
            #Si on a toujours une connection en SSH on ecrit le resultat dans le BUFFER_HTTP_TO_SSH de E
            if RequestManager.doesSSHReady_E:
                #HHTP_HANDLER prend le verou H ou essaye
                lockH.acquire()
                RequestManager.E_can_Read = False
                result = RequestManager.getResult(req)
                RequestManager.BUFFER_HTTP_TO_SSH = result
                RequestManager.BUFFER_HTTP_TO_SSH = base64.b64decode(RequestManager.BUFFER_HTTP_TO_SSH)
                #Informer E_SSH qu'il peut maintenant lire le contenu de BUFFER_HTTP_TO_SSH
                RequestManager.E_can_Read = True
                lockH.release()
                #On repond OK a W
                html = RequestManager.convertData(RequestManager.oK)
                self.answerToClient(html, 200, 'text/html')
            else:
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
           
        while True:  
            message_queues = {}
            readable, writable, exceptional = select.select(inputs, outputs, inputs) 
            # Handle inputs
            for s in readable:
                if s is server:
                    # A "readable" server socket (ours) is ready to accept a connection
                    connection, client_address = s.accept()
                    print "New connection on E_ssh 2222", client_address
                    connection.setblocking(0)
                    inputs.append(connection)
                    #E est donc pret en connection SHH
                    RequestManager.E_isReady = True
                    
                else:
                    # Il s'agit d'un client et non de notre serveur
                    # On lit ce qu'il ecrit
                    data = s.recv(RequestManager.MAX_SIZE)
                    if data:
                        # A readable client socket has data
                        print 'received "%s" from %s' % (data, s.getpeername())
                        lockS.acquire()
                        RequestManager.BUFFER_SSH_TO_HTTP = data
                        lockS.release()
                        print "Sending OK"
                        #message_queues[s].put(data)
                        # Add output channel for response
                        if s not in outputs:
                            outputs.append(s)
                    else:
                        # Interpret empty result as closed connection
                        print >>sys.stderr, 'closing', client_address, 'after reading no data'
                        # Stop listening for input on the connection
                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        s.close()
                        # Remove message queue
                        #del message_queues[s]

            # Handle outputs
            for s in writable:
                if RequestManager.BUFFER_HTTP_TO_SSH != '':
                    lockH.acquire()
                    s.send(RequestManager.BUFFER_HTTP_TO_SSH)
                    lockH.release()


    @staticmethod
    def handle_W():

        # Create a TCP/IP socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server.setblocking(0)
        # Bind the socket to the port
        # server_address = ('localhost', W_Bot.PORT)
        server.connect(('localhost', 22))
        # Listen for incoming connections
        # server.listen(1)
        # Sockets from which we expect to read
        inputs = [ server ]
        outputs = [ ] 
        while True:   
            readable, writable, exceptional = select.select(inputs, outputs, inputs) 
            # Handle W output
            for s in readable:
                if s is server:
                    # On a des donnees en retour
                    print "On lit des dnnees en retour"
                    data = s.recv(RequestManager.MAX_SIZE)
                    lockS.acquire()
                    RequestManager.BUFFER_SSH_TO_HTTP = data
                    lockS.release()

            # Handle W input
            for s in writable:
                print "Envoie de la data sur la socket"
                if RequestManager.BUFFER_HTTP_TO_SSH != '':
                    lockH.acquire()
                    s.send(RequestManager.BUFFER_HTTP_TO_SSH)
                    lockH.release()

    @staticmethod
    def touchTheSocket():

        # Create a TCP/IP socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server.setblocking(0)
        # Bind the socket to the port
        # server_address = ('localhost', W_Bot.PORT)
        server.connect(('localhost', 22))
        # Listen for incoming connections
        # server.listen(1)
        # Sockets from which we expect to read
        inputs = [ server ]
        outputs = [ ] 
        while True:   
            readable, writable, exceptional = select.select(inputs, outputs, inputs) 
            # Handle W output
            for s in readable:
                if s is server:
                    # On a des donnees en retour
                    print "On lit des dnnees en retour"
                    data = s.recv(RequestManager.MAX_SIZE)
                    lockS.acquire()
                    RequestManager.BUFFER_SSH_TO_HTTP = data
                    lockS.release()

            # Handle W input
            for s in writable:
                print "Envoie de la data sur la socket"
                if RequestManager.BUFFER_HTTP_TO_SSH != '':
                    lockH.acquire()
                    s.send(RequestManager.BUFFER_HTTP_TO_SSH)
                    lockH.release()
    @staticmethod
    def touchTheSocket():

        # Create a TCP/IP socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server.setblocking(0)
        # Bind the socket to the port
        # server_address = ('localhost', W_Bot.PORT)
        server.connect(('localhost', 22))
        # Listen for incoming connections
        # server.listen(1)
        # Sockets from which we expect to read
        inputs = [ server ]
        outputs = [ ] 
        while True:   
            readable, writable, exceptional = select.select(inputs, outputs, inputs) 
            # Handle W output
            for s in readable:
                if s is server:
                    # On a des donnees en retour
                    print "On lit des dnnees en retour"
                    data = s.recv(RequestManager.MAX_SIZE)
                    lockS.acquire()
                    RequestManager.BUFFER_SSH_TO_HTTP = data
                    lockS.release()

            # Handle W input
            for s in writable:
                print "Envoie de la data sur la socket"
                if RequestManager.BUFFER_HTTP_TO_SSH != '':
                    lockH.acquire()
                    s.send(RequestManager.BUFFER_HTTP_TO_SSH)
                    lockH.release()

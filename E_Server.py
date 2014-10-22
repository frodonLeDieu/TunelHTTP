import sys
from Tools import RequestManager, ServJob, SockListenerJob
import select
import socket
import sys
import time
import SocketServer
import base64
import SimpleHTTPServer
from multiprocessing import Lock

# Semaphores pour BUFFERS de E
lockH = Lock()  #La semaphore sur la ressource BUFFER_HTTP_TO_SHH
lockS = Lock()  #La semaphore sur la ressource BUFFER_SSH_TO_HTTP

class E_Bot(SimpleHTTPServer.SimpleHTTPRequestHandler):
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
        if RequestManager.E_isReady:
            if req == RequestManager.url_set_W_HaveResult:
                #print '\n----------------------------------------'
                #print 'DATA RECEIVED'
                #print '----------------------------------------\n'
                content_len = int(self.headers.getheader('content-length', 0))
                result = self.rfile.read( content_len)
                ############# RECEIVING RESULT FROM W #################   
                #Si on a toujours une connection en SSH on ecrit le resultat dans le BUFFER_HTTP_TO_SSH de E
                if RequestManager.E_isReady:
                    #print "E is ready"
                    #HHTP_HANDLER prend le verou H ou essaye
                    #print "E take locH for first time"
                    lockH.acquire()
                    RequestManager.E_can_Read = False
                    # Fin de la donnee que W a envoyer
                    RequestManager.BUFFER_HTTP_TO_SSH = base64.b64decode(result)
                    #Informer E_SSH qu'il peut maintenant lire le contenu de BUFFER_HTTP_TO_SSH
                    RequestManager.E_can_Read = True
                    #print "[BUFFER_HTTP_TO_SSH] <-- W\n", RequestManager.BUFFER_HTTP_TO_SSH
                    #print "E releases lockH"
                    lockH.release()
                    #On repond OK a W
                    html = RequestManager.convertData(RequestManager.oK)
                    self.answerToClient(html, 200, 'text/html')
                else:
                    html = RequestManager.convertData(RequestManager.kO)
                    self.answerToClient(html, 200, 'text/html')
            else:
                html = RequestManager.convertData(RequestManager.kO)
                self.answerToClient(html, 200, 'text/html')
        else:
            html = RequestManager.convertData(RequestManager.kO)
            self.answerToClient(html, 200, 'text/html')



    def do_GET(self):
        """
        Our Get implementation which handles all get requests
        """
        #print '\n----------------------------------------'
        #print 'HTTP_REQUEST'
        #print '----------------------------------------\n'
        #print "{} wrote:".format(self.client_address[0])
        #print self.path
        req = self.path
        #Verifie que la requete demande l'etat du ssh chez E et si E est pret en ssh
        ############# RECEIVING "PING" FROM W #################   
        #Le client tente de savoir si E est pret en SSH
        if req == RequestManager.url_check_Eready:
            if RequestManager.E_isReady:
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
                    #print "\n[BUFFER_SSH_TO_HTTP] --> W\n"
                    lockS.acquire()
                    data = RequestManager.BUFFER_SSH_TO_HTTP
                    #print data
                    html = RequestManager.convertData(base64.b64encode(data))
                    #print base64.b64encode(data)
                    self.answerToClient(html, 200, 'text/html')
                    RequestManager.BUFFER_SSH_TO_HTTP = ''
                    lockS.release()
                else:
                    #Aucun contenu dans le buffer
                    #print "Nothing to send to W\n"
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



    @staticmethod
    def sshHandler(inputs, outputs, server):
        """
        Handle our SSH request and responses
        """
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
                        #print "-----------------------------"
                        #print "SSH LINE OUT"
                        #print "-----------------------------"
                        #print data
                        #while not RequestManager.E_can_Read:
                            #time.sleep(0.1)
                        # Si E peut lire BUFFER_HTTP_TO_SSH
                    else:
                        pass
                        # Le client s'est deconnecte
                        RequestManager.E_isReady = False
                        inputt.remove(s)

            for s in outputready:
                if s is not server:
                    if RequestManager.E_can_Read:
                        #print "-----------------------------"
                        #print "SSH LINE IN"
                        #print "-----------------------------"
                        lockH.acquire()
                        #print  RequestManager.BUFFER_HTTP_TO_SSH
                        s.send(RequestManager.BUFFER_HTTP_TO_SSH)
                        RequestManager.E_can_Read = False
                        RequestManager.BUFFER_HTTP_TO_SSH = ''
                        lockH.release()



def usage():
    print'python E_Server port_http port_ssh'
    exit(0)



def main():
    """
    Our main function
    """
    if(len(sys.argv) < 3):
        usage()
    PORT = int(sys.argv[1])
    PORT2 = int(sys.argv[2])
    http = ServJob('HTTPServer', PORT, E_Bot)
    ssh = SockListenerJob('SSHServer', PORT2, E_Bot.sshHandler, 'Listening')
    http.start()
    ssh.start()



if __name__ == '__main__':  
    main()

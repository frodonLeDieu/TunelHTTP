import SocketServer
from Tools import RequestManager
import SimpleHTTPServer

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
        print "Requete ==> "+req.__str__()+"\n"

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
            print "W want a job"
            RequestManager.W_isReady = True
            #Si W et E sont prets en SSH
            if RequestManager.doesW_WaitingOrder():
                #Si on a du contenu dans le BUFFER_SSH_TO_HTTP, on l'envoi a notre client par le biais du proxy
                print "E is ready to send a job to W"
                if RequestManager.BUFFER_SSH_TO_HTTP != '':
                    #HHTP_HANDLER prend le verou S ou essaye
                    print "E found what to send to W! Hourra"
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
        elif req == RequestManager.url_set_W_HaveResult:
            #Si on a toujours une connection en SSH on ecrit le resultat dans le BUFFER_HTTP_TO_SSH
            if RequestManager.doesSSHReady_E:
                #Si W a deja commence a envoyer les resultats (ie que HTTP_HANDLER avait deja pris le verrou), on ne ressaye pas de le prendre
                if not RequestManager.W_still_Writing:
                    #HHTP_HANDLER prend le verou H ou essaye
                    lockH.acquire()
                result = RequestManager.getResult(req)
                
                #W a fini de nous envoyer le resultat de notre commande, on vide le buffer et on relache le verrou
                if result == RequestManager.EOT:
                    RequestManager.W_still_Writing = False
                    RequestManager.BUFFER_HTTP_TO_SSH = ''
                    lockH.release()
                else:
                #Si non cntinuer a ecrire le resultat dan snotre buffer
                    RequestManager.BUFFER_HTTP_TO_SSH += result
                    #On repond OK a W
                html = RequestManager.convertData(RequestManager.oK)
                self.answerToClient(html, 200, 'text/html')
            else:
                html = RequestManager.convertData(RequestManager.kO)
                self.answerToClient(html, 200, 'text/html')



        ############# RECEIVING RESULT FROM W #################   
        #Pour toute autre requete on repond KO
        else:
            html = RequestManager.convertData(RequestManager.kO)
            self.answerToClient(html, 200, 'text/html')


class MySSHHandler(SocketServer.StreamRequestHandler):
    """
    Handle our SSH request and responses
    """

    def handle(self):
        #E est donc pret en connection SHH
        RequestManager.E_isReady = True
        
        while True:
            self.data = self.rfile.readline()
            print '\n----------------------------------------'
            print 'SSH_REQUEST'
            print '----------------------------------------'
            print '{} wrote:'.format(self.client_address[0])
            print self.data
            self.wfile.write("OK")

import sys
import base64
from Tools import RequestManager, W_Slave
import time
import select
import socket
from multiprocessing import Lock

# Semaphores pour BUFFERS de W
lockH = Lock()  #La semaphore sur la ressource BUFFER_HTTP_TO_SHH
lockS = Lock()  #La semaphore sur la ressource BUFFER_SSH_TO_HTTP

class W_Bot:
    """
    ----------------------------------------------
    Help us to lauch W functions
    ----------------------------------------------
    """
    TIME_TO_WAIT = 0.1
    BASE_URL = ''
    PORT = 22

    @staticmethod
    def resultSender():
        """
        Send content of the socket W on HTTP E
        """
        while True:
            RequestManager.AVAILABLE = False
            # On verifie si E est pret en SSH
            requester = "Slave2" 
            #print "[",requester,"] : Checking E disponibility"
            W_Bot.checkE_Ready(requester)
            while not RequestManager.E_isReady:
                W_Bot.sleep()
                W_Bot.checkE_Ready(requester)
            # Quand E est pret et que la connexion en SSH de W n'est pas encore ouverte on l'ouvre
            if RequestManager.E_isReady:
                RequestManager.W_isReady = True
            # Quand E et W sont prets en SSH on peut commencer la communication
            if RequestManager.W_isReady and RequestManager.E_isReady:
                #print "[",requester,"] : Both are available"
                #print "[",requester,"] : Waiting to read BUFFER_SSH_TO_HTTP"
                while not RequestManager.W_can_Write: 
                    time.sleep(0.1)
                    if not RequestManager.E_isReady:
                        RequestManager.AVAILABLE = True
                        break
                if RequestManager.AVAILABLE:
                    print "NOT AVAILABLE"
                    continue
                
                print "Communication is available"
                if RequestManager.W_can_Write:
                    lockS.acquire()
                    RequestManager.W_can_Write = False
                    result = RequestManager.BUFFER_SSH_TO_HTTP
                    RequestManager.BUFFER_SSH_TO_HTTP = ''
                    lockS.release()
                    #print "\n[BUFFER_SSH_TO_HTTP] --> E\n", result
                    RequestManager.sendResult(base64.b64encode(result), requester)


    @staticmethod
    def requestSender():
        """
        Ask data to E
        """
        while True:
            RequestManager.AVAILABLE = False
            requester = "Slave1" 
            #print "[",requester,"] : Checking E disponibility"
            # On verifie si E est pret en SSH
            W_Bot.checkE_Ready(requester)
            while not RequestManager.E_isReady:
                W_Bot.sleep()
                W_Bot.checkE_Ready(requester)
            # Quand E est pret et que la connexion en SSH de W n'est pas encore ouverte on l'ouvre
            if RequestManager.E_isReady:
                RequestManager.W_isReady = True
            # Quand E et W sont prets en SSH on peut commencer la communication
            if RequestManager.doesW_WaitingOrder():
                #print "[",requester,"] : Both are available"
                #print "E is ready on SSH, W too"
                data = W_Bot.askData(requester)
                # Redemander le paquet tant qu'on en a pas recu un correct
                while data == RequestManager.kO:
                    W_Bot.sleep()
                    data = W_Bot.askData(requester)
                    if not RequestManager.E_isReady:
                        RequestManager.AVAILABLE = True
                        break
                if RequestManager.AVAILABLE:
                    print "NOT AVAILABLE"
                    continue

                print "Communication is available"
                #E est aussi pret ET a envoye une donnee
                if data != RequestManager.kO:                   
                    #On ecrit notre data sur W_SSH
                    lockH.acquire()
                    RequestManager.W_can_Read = False
                    RequestManager.BUFFER_HTTP_TO_SSH = base64.b64decode(data)
                    #print "\n[BUFFER_HTTP_TO_SSH] <-- E\n"
                    #print RequestManager.BUFFER_HTTP_TO_SSH
                    RequestManager.W_can_Read = True
                    lockH.release()


    @staticmethod
    def sshHandler():
        # Create a TCP/IP socket
        inputs = []
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server.setblocking(0)
        # Bind the socket to the port
        # server_address = ('localhost', W_Bot.PORT)
        while not RequestManager.E_isReady:
            time.sleep( 0.1)

        while True:  
            W_Bot.checkE_Ready()
            if inputs == [] :
                print "NEW CONNECTION"
                server.connect(('localhost', 22))
                inputs = [ server ]
                outputs = [ ] 


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
                        else:
                            inputs = []
                            print "E is dead"
                            server.close()
                            RequestManager.AVAILABLE = False

                for s in writable:
                    if RequestManager.W_can_Read:
                        #print "W peut peut lire sur BUFFER_HTTP_TO_SSH"
                        #print "Data to send on SSH 22 ", RequestManager.BUFFER_HTTP_TO_SSH
                        lockH.acquire()
                        #print "-----------------------------"
                        #print "SSH LINE IN"
                        #print "-----------------------------"
                        #print str(RequestManager.BUFFER_HTTP_TO_SSH)
                        s.send(RequestManager.BUFFER_HTTP_TO_SSH)
                        RequestManager.BUFFER_HTTP_TO_SSH = ''
                        RequestManager.W_can_Read = False
                        lockH.release()
                        if not RequestManager.E_isReady:
                            inputs = []
                            print "E is dead"
                            server.close()
                            RequestManager.AVAILABLE = False
        else:
            #Fermer la connection
            print "E is dead"
            inputs = [ ]
            server.close()
            RequestManager.AVAILABLE = False



    @staticmethod
    def sleep(sl = TIME_TO_WAIT):
        time.sleep(sl)



    @staticmethod
    def checkE_Ready(requester="Job"):
        """
        check if E has a client on SSH
        """
        url = RequestManager.BASE_URL+RequestManager.url_check_Eready
        if RequestManager.request(url, requester) == RequestManager.oK:
            RequestManager.E_isReady = True;
        else:
            RequestManager.E_isReady = False


    @staticmethod
    def askData(requester):
        """
        Ask a data to E
        """
        return RequestManager.request(RequestManager.BASE_URL+RequestManager.url_set_W_WaitOrder, requester)



def usage():
    print'python W_Client port_ssh port_http url_server_en_http [proxy]'
    exit(0)



def main():
    if(len(sys.argv) < 4):
        usage()
    PORT = int(sys.argv[1])
    PORT2 = int(sys.argv[2])
    BASE_URL = sys.argv[3]
    
    if( len( sys.argv) > 4):
        PROXY = sys.argv[4]
        RequestManager.PROXY = PROXY
        print "Using Proxy located at ", PROXY
        
    W_Bot.PORT = PORT  
    W_Bot.BASE_URL = RequestManager.BASE_URL = BASE_URL+':'+PORT2.__str__()
    http = W_Slave('HTTP Request Master', W_Bot.requestSender, W_Bot.BASE_URL)
    http.start()
    http2 = W_Slave('HTTP Sender Master', W_Bot.resultSender, W_Bot.BASE_URL)
    http2.start()
    ssh = W_Slave('Slave W condamned to communicate', W_Bot.sshHandler, W_Bot.BASE_URL)
    ssh.start()


if __name__ == "__main__":
    main()
    

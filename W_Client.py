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
    """ Help us to lauch W functions """
    TIME_TO_WAIT = 1.2
    BASE_URL = ''
    PORT = 22

    @staticmethod
    def resultSender():
        """ Send content of the socket W on HTTP E """
        requester = "Slave2" 
        while True:
            if not RequestManager.E_isReady:
                W_Bot.checkE_Ready(requester)
                W_Bot.sleep()
                continue
            else:
                RequestManager.W_isReady = True

            if RequestManager.W_isReady and RequestManager.E_isReady:
                if not RequestManager.W_can_Write: 
                    time.sleep(0.1)
                    continue

                if RequestManager.W_can_Write:
                    lockS.acquire()
                    RequestManager.W_can_Write = False
                    result = RequestManager.BUFFER_SSH_TO_HTTP
                    RequestManager.BUFFER_SSH_TO_HTTP = ''
                    lockS.release()
                    RequestManager.sendResult(base64.b64encode(result), requester)


    @staticmethod
    def requestSender():
        """ Ask data to E """
        requester = "Slave1" 
        while True:
            if not RequestManager.E_isReady:
                W_Bot.checkE_Ready(requester)
                W_Bot.sleep()
                continue
            else:
                RequestManager.W_isReady = True

            if RequestManager.doesW_WaitingOrder():
                data = W_Bot.askData(requester)
                if data == RequestManager.kO:
                    time.sleep(0.1)
                    continue
                else:                   
                    lockH.acquire()
                    RequestManager.W_can_Read = False
                    RequestManager.BUFFER_HTTP_TO_SSH = base64.b64decode(data)
                    RequestManager.W_can_Read = True
                    lockH.release()


    @staticmethod
    def sshHandler():
        inputs = []
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:  
            if not RequestManager.E_isReady:
                time.sleep( 0.1)
                continue
            if inputs == [] :
                server.connect(('localhost', 22))
                inputs = [ server ]
                outputs = [ ] 
            if RequestManager.E_isReady:
                readable, writable, exceptional = select.select(inputs, inputs, []) 
                for s in readable:
                    if s is server:
                        data = RequestManager.receive(s, RequestManager.MAX_SIZE_PAGE)
                        if data : 
                            lockS.acquire()
                            RequestManager.W_can_Write = False
                            RequestManager.BUFFER_SSH_TO_HTTP += data
                            RequestManager.W_can_Write = True
                            lockS.release()
                        else:
                            inputs = []
                            #print "E is dead"
                            server.close()
                            RequestManager.AVAILABLE = False

                for s in writable:
                    if RequestManager.W_can_Read:
                        lockH.acquire()
                        s.send(RequestManager.BUFFER_HTTP_TO_SSH)
                        RequestManager.BUFFER_HTTP_TO_SSH = ''
                        RequestManager.W_can_Read = False
                        lockH.release()
                        if not RequestManager.E_isReady:
                            inputs = []
                            #print "E is dead"
                            server.close()
        else:
            #Fermer la connection
            inputs = []
            server.close()



    @staticmethod
    def sleep(sl = TIME_TO_WAIT):
        time.sleep(sl)



    @staticmethod
    def checkE_Ready(requester="Job"):
        """ check if E has a client on SSH """
        url = RequestManager.BASE_URL+RequestManager.url_check_Eready
        if RequestManager.request(url, requester) == RequestManager.oK:
            RequestManager.E_isReady = True;
        else:
            RequestManager.E_isReady = False


    @staticmethod
    def askData(requester):
        """ Ask a data to E """
        return RequestManager.request(RequestManager.BASE_URL+RequestManager.url_set_W_WaitOrder, requester)


def usage():
    print'python W_Client port_http url_server_en_http [http://proxy:port_proxy]'
    exit(0)


def main():
    if(len(sys.argv) < 3):
        usage()
    PORT = int(sys.argv[1])
    BASE_URL = sys.argv[2]

    if(len(sys.argv) > 3):
        RequestManager.PROXY = str(sys.argv[3])

    W_Bot.BASE_URL = RequestManager.BASE_URL = BASE_URL+':'+PORT.__str__()
    
    http = W_Slave('HTTP Request Sender', W_Bot.requestSender)
    http.start()
    http2 = W_Slave('HTTP Result Sender', W_Bot.resultSender)
    http2.start()
    ssh = W_Slave('SSH Handler on port 22', W_Bot.sshHandler)
    ssh.start()


if __name__ == "__main__":
    main()

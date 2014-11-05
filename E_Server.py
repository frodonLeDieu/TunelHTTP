import sys
from Tools import RequestManager, ServJob, SockListenerJob
import select
import urllib
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
        self.server_version="ECS"
        self.sys_version=""
        self.send_response(code)
        self.send_header("Content-type", cType)
        self.send_header("Cache-Control", "no-cache")
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
                content_len = int(self.headers.getheader('content-length', 0))
                result = self.rfile.read( content_len)
                #result2 = urllib.urldecode(result)
                #data = result2.Data
                if RequestManager.E_isReady:
                    lockH.acquire()
                    RequestManager.E_can_Read = False
                    RequestManager.BUFFER_HTTP_TO_SSH = base64.b64decode(result)
                    RequestManager.E_can_Read = True
                    lockH.release()
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
        req = self.path
        if req == RequestManager.url_check_Eready:
            if RequestManager.E_isReady:
                res = RequestManager.oK
            else:
                res = RequestManager.kO
            html = RequestManager.convertData(res)
            self.answerToClient(html, 200, 'text/html')
        elif req == RequestManager.url_set_W_WaitOrder:
            RequestManager.W_isReady = True
            if RequestManager.doesW_WaitingOrder():
                if RequestManager.BUFFER_SSH_TO_HTTP != '':
                    lockS.acquire()
                    data = RequestManager.BUFFER_SSH_TO_HTTP
                    html = RequestManager.convertData(base64.b64encode(data))
                    self.answerToClient(html, 200, 'text/html')
                    RequestManager.BUFFER_SSH_TO_HTTP = ''
                    lockS.release()
                else:
                    html = RequestManager.convertData(RequestManager.kO)
                    self.answerToClient(html, 200, 'text/html')
            else : 
                html = RequestManager.convertData(RequestManager.kO)
                self.answerToClient(html, 200, 'text/html')
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
                    #print "New client on E_SSH via select"
                    client, address = server.accept()
                    inputt.append(client)
                    RequestManager.E_isReady = True
                else:
                    data = RequestManager.receive(s, RequestManager.MAX_SIZE_PAGE)
                    if data:
                        lockS.acquire()
                        RequestManager.BUFFER_SSH_TO_HTTP += data
                        lockS.release()
                    else:
                        pass
                        # Le client s'est deconnecte
                        RequestManager.E_isReady = False
                        inputt.remove(s)

            for s in outputready:
                if s is not server:
                    if RequestManager.E_can_Read:
                        lockH.acquire()
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
    http = ServJob('HTTPServer on port '+PORT.__str__(), E_Bot, PORT)
    ssh = SockListenerJob('SSHServer Listenning on port '+PORT2.__str__(), E_Bot.sshHandler, PORT2)
    http.start()
    ssh.start()


if __name__ == '__main__':  
    main()

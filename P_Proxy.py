import sys
from Tools import RequestManager, ServJob, SockListenerJob
import socket
import sys
import base64
import SimpleHTTPServer

class P_Bot(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """
    Handle HTTP request 
    Redirect request and manage the responses sent by Our SSH handler
    """

    def do_GET( self):
        print "Proxy REQUESTED"
        self.copyfile( urllib.urlopen( self.path), self.wfile)



def usage():
    print'python P_Server port_http'
    exit(0)



def main():
    """
    Our main function
    """
    if(len(sys.argv) < 2):
        usage()
    PORT = int(sys.argv[1])
    http = ServJob('Proxy', PORT, P_Bot)
    http.start()



if __name__ == '__main__':  
    main()


import sys
from Handlers import MyHTTPHandler, MySSHHandler
from Tools import RequestManager, ServJob, SockListenerJob

def usage():
    """
    Our Usage function
    """
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
    

    http = ServJob('HTTPServer', PORT, MyHTTPHandler)
    ssh = SockListenerJob('SSHServer', PORT2, MySSHHandler.handle_E, 'Listening')

    http.start()
    ssh.start()




if __name__ == '__main__':  
    main()


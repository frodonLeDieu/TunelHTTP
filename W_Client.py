import sys
from Tools import RequestManager, W_Bot, W_Slave 


def usage():
    """
    Our Usage function
    """
    print'python W_Client port_ssh port_http url_server_en_http [time_between_each_request]'
    exit(0)


def main():
    """
    our main function
    """
    if(len(sys.argv) < 4):
        usage()

    PORT = int(sys.argv[1])
    PORT2 = int(sys.argv[2])
    BASE_URL = sys.argv[3]
    
    W_Bot.BASE_URL = BASE_URL+':'+PORT2.__str__()

    http = W_Slave('Slave W')
    http.start()
    """
    ssh = ServJob('SSHServer', PORT2, MySSHHandler, 'Listening')
    ssh.start()
"""


if __name__ == "__main__":
    main()
    

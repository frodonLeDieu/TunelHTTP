import time
import socket
cpt = 0

ponderationMax = 1000000000
table = {}
fakeMsg = "Yo Bitch I'm Sorry for you"

undesired_servers = ["python", "Python", "HTTPServer", "simple", "Simple", "SimpleHTTPServer", "Server", "linux", "Linux"]
undesired_caches = ["no-store", "must-revalidate", "max-age=0"]
undesired_ua = ["bash", "python", "Python", "Bash", "java", "Java"]

def proxy_mangle_request(req):
    global cpt
    global table
    global undesired_ua
    global ponderationMax
    """
    pond = lastCall = 0
    params = {}
    undesired_userA = False

    url = req.getPath()
    if url in table:
        lastCall = float(table[url]["lastCall"])
        pond = int(table[url]["ponderation"])


    thisCall = float( time.time())
    difference = thisCall - lastCall

    #All check under there is about the client (W) requests
    #Check Frequence of requests
    if(lastCall != 0 and difference < 0.5):
        pond += 1
    
    #Check of the User agent if not checked yet
    if not url in table:
        v = req.getHeader("User-agent")
        if v != []:
            v = v[0]
            for word in undesired_ua:
                if word in v:
                    undesired_userA = True
        if undesired_userA:
            pond += 1


    params["lastCall"] = thisCall
    params["ponderation"] = pond
    params["responseOnce"] = False
    table[url] = params
    """
    return req



def proxy_mangle_response(res):
    global table
    global undesired_servers
    global undesired_caches
    global ponderationMax
    """
    ponderation = pond = 0
    undesired_cache_mode = False
    undesired_server = False

    c = res.getHeader("Cache-Control")
    v = res.getHeader("Content-Type")
    s = res.getHeader("Server")
    s = s[0]

    #Do this check only if we can associate an existant request pre-saved
    if res.url in table:
        params = table[res.url]
        pond = int(params["ponderation"])
        responseOnce = bool(params["responseOnce"])
        #Make these checks only if its the first time
        if not responseOnce:
            print "Make Checks"
            print res
            #CacheMode-checking!!!
            if (c != []):
                c = c[0]
                for word in undesired_caches:
                    if word in c:
                        undesired_cache_mode = True
                        break
            if undesired_cache_mode:
                ponderation += 4
            #Server-Checking
            for word in undesired_servers:
                if word in s:
                    undesired_cache_mode = True
            if undesired_server:
                ponderation += 10
            responseOnce = True
        


    print "Ponderation On this answer ==> ",(ponderation)
    print "Global ponderation ==> ",(ponderation + pond)


    ponderation += pond
    #Update our table
    table[res.url]["ponderation"] = ponderation
    table[res.url]["responseOnce"] = responseOnce

    #Bannish him
    #if ponderation > ponderationMax:
        #res.body = giveBlabla(res, v)
    """    
    return res
    

def apply_filter(req):
    global fakeMsg
    url = req.getPath()
    ip = getIp(url)
    #print("Request refused")


def giveBlabla(res, v):
    """
    Transform res.body into a fake msg
    """
    if len(v) > 0 and "text/html" in v[0]:
        res.body = fakeMsg
    return res


def getIp(url):
    """
    Return the ip of the url
    """
    first = url.split("/")
    if (first[0] == "http:" or first[0] == "https:"):
        first = first[2]
    else:
        first = first[0]
    if ":" in first:
        first = first.split(":")[0]
    ip = socket.gethostbyname(first)
    return ip

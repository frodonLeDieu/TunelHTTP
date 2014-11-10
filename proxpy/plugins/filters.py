import time
import socket
import sys
cpt = 0

ponderationMax = 40000000000000000000000000000000000000000000000000000000000000000000000
ips_table = {}
table = {}
fakeMsg = "Yo Bitch I'm Sorry for you"

undesired_servers = ["python", "Python", "HTTPServer", "simple", "Simple", "SimpleHTTPServer", "Server", "linux", "Linux"]
undesired_caches = ["no-store", "must-revalidate", "max-age=0"]
undesired_ua = ["bash", "python", "Python", "Bash", "java", "Java"]
firstIpCall = 0

def proxy_mangle_request(req):
    global cpt
    global table
    global ips_table
    global undesired_ua
    global ponderationMax
    global firstIpCall

    ponderation = lastCall = 0
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
    if(lastCall != 0 and difference <= 0.5):
        ponderation += 1
    
    #Check of the User agent if not checked yet
    if not url in table:
        v = req.getHeader("User-agent")
        if v != []:
            v = v[0]
            for word in undesired_ua:
                if word in v:
                    undesired_userA = True
        if undesired_userA:
            ponderation += 4

    #MAJ du table d'url
    params["lastCall"] = thisCall
    pond = params["ponderation"] = ponderation
    params["responseOnce"] = False
    table[url] = params
    ip = getIp(url)

    #MAJ du table d'ip
    params[url] = table[url]
    params["nbCallLast15"] = 1

    if not ip in ips_table:
        firstIpCall = float(time.time())
        ips_table[ip] = params
    else:
        ponderation =  int(ips_table[ip]["ponderation"]) + ponderation
        new = int(ips_table[ip]["nbCallLast15"]) + 1
        params["nbCallLast15"] = new
        if not url in ips_table[ip]:
            ips_table[ip] = params
        else:
            ips_table[ip][url] = table[url]
        ips_table[ip]["nbCallLast15"] = new


    thisIpCall = float(time.time())
    nbCallLast15 = int(ips_table[ip]["nbCallLast15"])

    if firstIpCall != 0 and (thisIpCall - firstIpCall) >= 15:
        print "IP :::::  ", ip
        print "Ponderation On this request ==> ",pond
        print "NbCallLast15 ==> ",nbCallLast15
        firstIpCall = float(time.time())
        ips_table[ip]["nbCallLast15"] = 0
        if nbCallLast15 > 100:
            print "nbCallLast15 > 100"
            ponderation += 50
            print "Global ponderation ==> ",int(ips_table[ip]["ponderation"])

    ips_table[ip]["ponderation"] = ponderation

    return req



def proxy_mangle_response(res):
    global table
    global undesired_servers
    global undesired_caches
    global ponderationMax
    global ips_table
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
        ponderation = int(params["ponderation"])
        responseOnce = bool(params["responseOnce"])
        #Make these checks only if its the first time
        if not responseOnce:
            #CacheMode-checking!!!
            if (c != []):
                c = c[0]
                for word in undesired_caches:
                    if word in c:
                        undesired_cache_mode = True
                        break
            if undesired_cache_mode:
                pond += 4
            #Server-Checking
            for word in undesired_servers:
                if word in s:
                    undesired_cache_mode = True
            if undesired_server:
                pond += 10
            responseOnce = True
        




    ponderation += pond
    #Update our table
    table[res.url]["ponderation"] = ponderation
    table[res.url]["responseOnce"] = responseOnce
    #Update our iptables
    ip = getIp(res.url)
    ips_table[ip][res.url] = table[res.url]
    params[res.url] = table[res.url]

    if ip in ips_table:
        ponderation =  int(ips_table[ip]["ponderation"]) + ponderation
        if res.url in ips_table[ip]:
            ips_table[ip][res.url] = table[res.url]
        ips_table[ip]["ponderation"] = ponderation

    #if ponderation > ponderationMax:
        #print "I DROP THIS PACKET!!!!!!"
        #res.body = giveBlabla(res, v)
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

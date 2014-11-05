
cpt = 0

def proxy_mangle_request(req):
    global cpt
    req.setHeader("User-Agent", "ProxPy Agent")
    cpt = cpt + 1 
    print(cpt)
    return req

def proxy_mangle_response(res):
    v = res.getHeader("Content-Type")
    if len(v) > 0 and "text/html" in v[0]:
        res.body = res.body.replace("Google", "elgooG")
    return res

import urllib
import urllib2


def sendResult(result, url):
    """ Send our result by POST method """
    parameters = {'Data' : result}
    data = urllib.urlencode(parameters) 
    req = urllib2.Request(url, data)

    if True:
        proxy  = urllib2.ProxyHandler({'http': '192.168.12.107:8080'})
        opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)

    handle = urllib2.urlopen(req)
    result = handle.read()
    return result


sendResult("TOTO", "http://www.w3schools.com/php/php_form_validation.asp")


import urllib2

proxy = urllib2.ProxyHandler( {'http': '127.0.0.1'})

#opener = urllib2.build_opener( proxy)
#urllib2.install_opener( opener)
urllib2.urlopen( 'http://www.google.com')

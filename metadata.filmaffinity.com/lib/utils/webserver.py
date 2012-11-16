
import os
import re

import xbmc

xml = xbmc.translatePath( "special://userdata/guisettings.xml" )
data = open( xml ).read()

webserver         = re.search( '<webserver>(.*?)</webserver>',                 data ).group( 1 )
webserverpassword = re.search( '<webserverpassword>(.*?)</webserverpassword>', data ).group( 1 )
webserverport     = re.search( '<webserverport>(.*?)</webserverport>',         data ).group( 1 )
webserverusername = re.search( '<webserverusername>(.*?)</webserverusername>', data ).group( 1 )

xbmcHttp = "http://"

if webserverpassword and webserverusername:
    xbmcHttp += "%s:%s@" % ( webserverusername, webserverpassword )

xbmcHttp += xbmc.getIPAddress() #"localhost" #"107.0.0.1"

if webserverport and webserverport != "80":
    xbmcHttp += ":%s" % webserverport

xbmcHttp += "/xbmcCmds/xbmcHttp"

#print webserver
#print webserverpassword
#print webserverport
#print webserverusername
#print xbmcHttp
""" Display url using the default browser.
    by frost (passion-xbmc.org)
"""

import sys
import webbrowser
from traceback import print_exc

import xbmc
from xbmcaddon import Addon


__addon__ = Addon( sys.argv[ 1 ] )


def notification( header="", message="", sleep=5000, icon=__addon__.getAddonInfo( "icon" ) ):
    """ Will display a notification dialog with the specified header and message,
        in addition you can set the length of time it displays in milliseconds and a icon image.
    """
    xbmc.executebuiltin( "XBMC.Notification(%s,%s,%i,%s)" % ( header, message, sleep, icon ) )


def launchUrl( url ):
    try: webbrowser.open( url )
    except: print_exc()


def Main():
    try:
        url = sys.argv[ 2 ]
        # notify user
        notification( __addon__.getAddonInfo( "name" ), url )
        # launch url
        launchUrl( url )
    except:
        print_exc()



if ( __name__ == "__main__" ):
    #print sys.argv
    Main()

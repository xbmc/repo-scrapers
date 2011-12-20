""" Display url using the default browser.
    by frost (passion-xbmc.org)
"""

import sys
import webbrowser
from traceback import print_exc

import xbmc
from xbmcaddon import Addon


Addon = Addon( sys.argv[ 1 ] )


def notification( header="", message="", sleep=5000, icon=Addon.getAddonInfo( "icon" ) ):
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
        notification( Addon.getAddonInfo( "name" ), url )
        # launch url
        launchUrl( url )
    except:
        print_exc()



if ( __name__ == "__main__" ):
    #print sys.argv
    Main()


# Modules general
import os
import sys

# Modules XBMC
import xbmcvfs

# Modules Custom
from log import logAPI
LOGGER = logAPI()

Image = None
try:
    # Require PIL for FLIP
    from PIL import Image
except:
    LOGGER.error.print_exc()


def flip_fanart( fanart, quality=85 ):
    if Image is not None:
        #NB: the EXIF infos is not preserved :(
        try: quality = int( float( quality ) )
        except:
            quality = 85
            print "flip_fanart::quality: %s" % repr( quality )
            LOGGER.error.print_exc()
        try:
            im = Image.open( fanart )
            im = im.transpose( Image.FLIP_LEFT_RIGHT )
            format = ( im.format or "JPEG" )
            #PIL ignore param exif= in save
            try: im.save( fanart, format, quality=quality, dpi=im.info.get( "dpi", ( 0, 0 ) ), exif=im.info.get( "exif", "" ) )
            except: im.save( fanart, "PNG" )
        except:
            LOGGER.error.print_exc()
    return fanart


def IsTrue( text ):
    return ( text.lower() == "true" )


def path_exists( filename ):
    # first use os.path.exists and if not exists, test for share with xbmcvfs.
    return os.path.exists( filename ) or xbmcvfs.exists( filename )

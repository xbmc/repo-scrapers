"""
XBMC Cached Thumbnails, based on file 'XBMC/xbmc/FileItem.cpp'
by Frost

Example use:
from file_item import Thumbnails
thumbnails = Thumbnails()

print thumbnails.get_cached_artist_thumb( "artist name" )
print thumbnails.get_cached_profile_thumb() # current profile thumb
print thumbnails.get_cached_season_thumb( "F:\serietv\csi\Special" )
print thumbnails.get_cached_actor_thumb( "actor name" )
print thumbnails.get_cached_picture_thumb( "full Path" )
print thumbnails.get_cached_video_thumb( "full Path" )
print thumbnails.get_cached_saga_thumb( "idSet" )
print thumbnails.get_cached_episode_thumb( "full Path", iEpisode=0 ) # iEpisode, currently not used
print thumbnails.get_cached_fanart_thumb( "full Path", "fanart type" ) # fanart type ("music", "artist", "video", "tvshow" )

print thumbnails.get_cached_addon_thumb( "id.of.addon" )

@XBOX
print thumbnails.get_cached_program_thumb( "full Path" )
print thumbnails.get_cached_gamesave_thumb( "E:\games\[game name]\default.xbe" )
print thumbnails.get_cached_script_thumb( "script name" )
print thumbnails.get_cached_plugin_thumbs( "plugin type", "plugin name" )# tuple: default and folder thumbs

"""

import os
import xbmc
import xbmcvfs
from xbmcaddon import Addon


THUMBS_CACHE_PATH = os.path.join( xbmc.translatePath( "special://profile/" ), "Thumbnails" )

def path_exists( filename ):
    # first use os.path.exists and if not exists, test for share with xbmcvfs.
    return os.path.exists( filename ) or xbmcvfs.exists( filename )


class Thumbnails:
    def get_cached_thumb( self, path1, path2, SPLIT=False, SET_EXT=False ):
        # get the locally cached thumb
        filename = xbmc.getCacheThumbName( path1 )
        if SPLIT:
            thumb = os.path.join( filename[ 0 ], filename )
        else:
            thumb = filename
        if SET_EXT:
            thumb = os.path.splitext( thumb )[ 0 ] + os.path.splitext( path1 )[ 1 ]
        return os.path.join( path2, thumb )

    def get_cached_artist_thumb( self, strLabel ):
        return self.get_cached_thumb( "artist" + strLabel, os.path.join( THUMBS_CACHE_PATH, "Music", "Artists" ) )

    def get_cached_profile_thumb( self ):
        return xbmc.translatePath( xbmc.getInfoImage( "System.ProfileThumb" ) )

    def get_cached_season_thumb( self, seasonPath ):
        return self.get_cached_thumb( "season" + seasonPath, os.path.join( THUMBS_CACHE_PATH, "Video" ), True )

    def get_cached_actor_thumb( self, strLabel ):
        return self.get_cached_thumb( "actor" + strLabel, os.path.join( THUMBS_CACHE_PATH, "Video" ), True )

    def get_cached_picture_thumb( self, strPath ):
        if path_exists( os.path.join( THUMBS_CACHE_PATH, "Pictures" ) ):
            # assume old version or xbox
            return self.get_cached_thumb( strPath, os.path.join( THUMBS_CACHE_PATH, "Pictures" ), True )
        else:
            return self.get_cached_thumb( strPath, THUMBS_CACHE_PATH, True, True )

    def get_cached_video_thumb( self, strPath ):
        if strPath.startswith( "stack://" ):
            strPath = strPath[ 8 : ].split( " , " )[ 0 ]
        return self.get_cached_thumb( strPath, os.path.join( THUMBS_CACHE_PATH, "Video" ), True )

    def get_cached_saga_thumb( self, idSet, fanart=False ):
        strPath = "videodb://1/7/%s/" % idSet
        if fanart: return self.get_cached_fanart_thumb( strPath, "video" )
        else: return self.get_cached_thumb( strPath, os.path.join( THUMBS_CACHE_PATH, "Video" ), True )

    def get_cached_episode_thumb( self, strPath, iEpisode=0 ):
        return self.get_cached_thumb( strPath, os.path.join( THUMBS_CACHE_PATH, "Video" ), True )
        #return self.get_cached_thumb( "%sepisode%i" % ( strPath, iEpisode ), os.path.join( THUMBS_CACHE_PATH, "Video" ), True )

    def get_cached_fanart_thumb( self, strPath, fanart="" ):
        if fanart.lower() in [ "music", "artist" ]:
            return self.get_cached_thumb( strPath, os.path.join( THUMBS_CACHE_PATH, "Music", "Fanart" ) )
        if fanart.lower() in [ "video", "tvshow" ]:
            return self.get_cached_thumb( strPath, os.path.join( THUMBS_CACHE_PATH, "Video", "Fanart" ) )
        return ""

    def get_cached_addon_thumb( self, idAddon, type="" ):
        if type.lower() in [ "icon", "fanart" ]:
            strPath = Addon( idAddon ).getAddonInfo( type )
            return self.get_cached_thumb( strPath, THUMBS_CACHE_PATH, True, True )
        return ""

    def get_cached_program_thumb( self, strPath ):
        if path_exists( os.path.join( THUMBS_CACHE_PATH, "Programs" ) ):
            # assume old version or xbox
            return self.get_cached_thumb( strPath, os.path.join( THUMBS_CACHE_PATH, "Programs" ) )
        else:
            return self.get_cached_thumb( strPath, THUMBS_CACHE_PATH, True, True )

    def get_cached_gamesave_thumb( self, strPath ):
        if strPath.lower().endswith( ".xbe" ):
            try:
                return os.path.join( THUMBS_CACHE_PATH, "GameSaves",
                    "%s.tbn" % str( xbmc.executehttpapi( "getXBEid(%s)" % strPath ) ).replace( "<li>", "" )[ 1: ] )
            except:
                pass
        return ""

    def get_cached_script_thumb( self, strLabel ):
        return self.get_cached_program_thumb( "special://home/scripts/%s/default.py" % ( strLabel ) )

    def get_cached_plugin_thumbs( self, strType, strLabel ):
        if strType.lower() in [ "music", "pictures", "programs", "video", "weather" ]:
            return self.get_cached_program_thumb( "special://home/plugins/%s/%s/default.py" % ( strType, strLabel ) ), \
                self.get_cached_program_thumb( "special://home/plugins/%s/%s/" % ( strType, strLabel ) )
        return "", ""



if ( __name__ == "__main__" ):
    thumbnails = Thumbnails()
    #print thumbnails.get_cached_season_thumb( "F:\serietv\ncis\Special" )
    print thumbnails.get_cached_addon_thumb( "script.game.arkanoid", "icon" )
    print thumbnails.get_cached_addon_thumb( "script.game.arkanoid", "fanart" )
    #print thumbnails.get_cached_picture_thumb( "http://passion-xbmc.org/scraper/Gallery/preview/Poster_BigBoss-274161.jpg" )
    #print thumbnails.get_cached_picture_thumb( "http://passion-xbmc.org/scraper/Gallery/main/Poster_BigBoss-274161.jpg" )

    #XBOX
    #print thumbnails.get_cached_script_thumb( "Calculator" )
    #print thumbnails.get_cached_plugin_thumbs( "video", "passion-xbmc nfo creator" )# default and folder thumbs


#dummy xbmcgui, for testing jsonrpc with 'http://127.0.0.1:80/jsonrpc'

def pprint( msg="", debug=1 ):
    if debug: print msg


class ListItem:
    def __init__( self, *args, **kwargs ):
        self.args, self.kwargs = args, kwargs
        pprint( "xbmcgui.ListItem( %r, %r )" % ( self.args, self.kwargs ) )

    def addContextMenuItems( *args, **kwargs ):
        pprint( "ListItem.addContextMenuItems( %r, %r )" % ( args, kwargs ) )

    def getLabel( self ):
        pprint( "ListItem.getLabel( %r, %r )" % ( self.args, self.kwargs ) )

    def getLabel2( self ):
        pprint( "ListItem.getLabel2( %r, %r )" % ( self.args, self.kwargs ) )

    def getProperty( self, *args, **kwargs ):
        pprint( "ListItem.getProperty( %r, %r )" % ( args, kwargs ) )

    def isSelected( self ):
        pprint( "ListItem.isSelected( %r, %r )" % ( self.args, self.kwargs ) )

    def select( self, *args, **kwargs ):
        pprint( "ListItem.select( %r, %r )" % ( args, kwargs ) )

    def setIconImage( self, *args, **kwargs ):
        pprint( "ListItem.setIconImage( %r, %r )" % ( args, kwargs ) )

    def setInfo( self, *args, **kwargs ):
        pprint( "ListItem.setInfo( %r, %r )" % ( args, kwargs ) )

    def setLabel( self, *args, **kwargs ):
        pprint( "ListItem.setLabel( %r, %r )" % ( args, kwargs ) )

    def setLabel2( self, *args, **kwargs ):
        pprint( "ListItem.setLabel2( %r, %r )" % ( args, kwargs ) )

    def setPath( self, *args, **kwargs ):
        pprint( "ListItem.setPath( %r, %r )" % ( args, kwargs ) )

    def setProperty( self, *args, **kwargs ):
        pprint( "ListItem.setProperty( %r, %r )" % ( args, kwargs ) )

    def setThumbnailImage( self, *args, **kwargs ):
        pprint( "ListItem.setThumbnailImage( %r, %r )" % ( args, kwargs ) )


class xbmcgui:
    def __init__( self ):
        self.ListItem = ListItem


import os
import sys

sys.path.insert( 0, "../" )

from jsonrpc import jsonrpcAPI
from log import logAPI
from streamdetails import *

log = logAPI()
xbmcgui = xbmcgui()

# for more see [$SOURCE/xbmc/interfaces/json-rpc/ServiceDescription.h]
sorttitle = { "method": "sorttitle", "order": "ascending" } #"descending"

Video_Fields_MovieSet = [ "title", "playcount", "fanart", "thumbnail" ]

List_Fields_All = [ "title", "artist", "albumartist", "genre", "year", "rating",
    "album", "track", "duration", "comment", "lyrics", "musicbrainztrackid",
    "musicbrainzartistid", "musicbrainzalbumid", "musicbrainzalbumartistid",
    "playcount", "fanart", "director", "trailer", "tagline", "plot",
    "plotoutline", "originaltitle", "lastplayed", "writer", "studio",
    "mpaa", "cast", "country", "imdbnumber", "premiered", "productioncode",
    "runtime", "set", "showlink", "streamdetails", "top250", "votes",
    "firstaired", "season", "episode", "showtitle", "thumbnail", "file", "resume" ]

Video_Fields_Movie = [ "title", "genre", "year", "rating", "director", "trailer",
    "tagline", "plot", "plotoutline", "originaltitle", "lastplayed",
    "playcount", "writer", "studio", "mpaa", "cast", "country",
    "imdbnumber", "premiered", "productioncode", "runtime", "set",
    "showlink", "streamdetails", "top250", "votes",
    "fanart", "thumbnail", "file", "resume" ] # "sorttitle" not supported :( !!! and "lastplayed" not returned


infoSet = None
jsonapi = jsonrpcAPI()
#print jsonapi.VideoLibrary.GetRecentlyAddedMovies( properties=["setid"] )
#raise
# GET MOVIESETS
json = jsonapi.VideoLibrary.GetMovieSets( properties=Video_Fields_MovieSet )

movie_sets = json.get( 'sets', [] )
total = json.get( "limits", {} ).get( "total" ) or len( movie_sets )
#print total

# dico for synchronize main container on VideoLibrary with virtual container of MovieSets
moviesets = {}
if infoSet is not None:
    # get only one user want info
    listitems = []
else:
    # set dymmy listitem, label: container title , label2: total movie sets
    listitems = [ xbmcgui.ListItem( "Container MovieSets", str( total ) ) ]

# get user separator
try: separator = " %s " % ADDON.getSetting( "separator" )
except: separator = " / "
# get user prefer order
try: sorttitle[ "order" ] = ( "ascending", "descending" )[ int( ADDON.getSetting( "order" ) ) ]
except: pass

# enum movie sets
for countset, movieset in enumerate( movie_sets ):
    #print movieset.keys()#[u'title', u'fanart', u'label', u'playcount', u'thumbnail', u'setid']
    #print movieset[ "title" ]
    #print movieset[ "label" ]
    #print movieset[ "fanart" ]
    #print movieset[ "playcount" ]
    #print
    try:
        idSet = movieset[ "setid" ]
        if infoSet is not None and idSet != infoSet:
            continue # get only one user want info
        # get saga icon
        icon = movieset[ "thumbnail" ]
        #icon = ( "", icon )[ os.path.exists( translatePath( icon ) ) ]
        # get saga fanart
        #d, f = os.path.split( movieset[ 'thumbnail' ] )
        #c_fanart = "%sFanart/%s" % ( d[ :-1 ], f )
        Fanart_Image = movieset[ "fanart" ]
        #Fanart_Image = ( "", c_fanart )[ os.path.exists( translatePath( c_fanart ) ) ]
        # fixe me: xbmc not change/reload/refresh image if path is same
        #if Fanart_Image: Fanart_Image = self.get_cached_thumb( Fanart_Image )
        #if icon: icon = self.get_cached_thumb( icon )

        # set movieset listitem
        listitem = xbmcgui.ListItem( movieset[ 'label' ], str( idSet ), icon, icon )
        #listitem.setPath( "ActivateWindow(10025,videodb://1/7/%i/)" % idSet )

        # get movies list of movieset
        # not good, return only Video.Fields.MovieSet. [use Files.GetDirectory for more fields]
        #json = jsonapi.VideoLibrary.GetMovieSetDetails( setid=idSet, properties=Video_Fields_MovieSet )
        json = jsonapi.Files.GetDirectory( directory="videodb://1/7/%i/" % idSet, properties=Video_Fields_Movie, sort=sorttitle, media="video" )
        movies = json.get( 'files', [] )
        total_movies = json.get( "limits", {} ).get( "total" ) or len( movies )
        # set base variables
        watched, unwatched = 0, total_movies
        rating, votes = 0.0, 0
        plotset = ""
        mpaa    = set()
        studios = set()
        genres  = set()
        years   = set()
        fanartsets = set()
        countries  = set()
        stackpath  = []
        stacktrailer = []
        iWidth, iHeight = 0, 0
        aspect = 0.0

        # enum movies
        #print sum( [ movie[ 'rating' ] for movie in movies ] ) / total_movies
        for count, movie in enumerate( movies ):
            #print movie.keys()#[u'rating', u'set', u'filetype', u'file', u'year', u'id', u'streamdetails', u'plot', u'votes', u'title', u'fanart', u'mpaa', u'writer', u'label', u'type', u'thumbnail', u'plotoutline', u'resume', u'director', u'imdbnumber', u'studio', u'showlink', u'genre', u'productioncode', u'country', u'premiered', u'originaltitle', u'cast', u'tagline', u'playcount', u'runtime', u'top250', u'trailer']
            # for more infos
            #print jsonapi.VideoLibrary.GetMovieDetails( movieid=int(movie["id"]), properties=Video_Fields_Movie )
            sdv = movie[ "streamdetails" ].get( "video", [{}] )
            #print sum( d.get( "duration", 0 ) for d in sdv )
            iWidth += sum( w.get( "width", 0 ) for w in sdv )
            iHeight += sum( h.get( "height", 0 ) for h in sdv )
            aspect += sum( a.get( "aspect", 0 ) for a in sdv )
            #continue
            try:
                # update mpaa
                mpaa.add( movie[ "mpaa" ] )
                # set watched count
                #print movie.get( "playcount" )
                if bool( movie[ "playcount" ] ): watched += 1
                # update genres and years
                if movie[ "year" ] > 0:
                    years.add( str( movie[ "year" ] ) )
                genres.update( movie[ "genre" ].split( " / " ) )
                # add country
                if movie.get( "country" ):
                    countries.update( movie[ "country" ].split( " / " ) )
                # add studio
                if movie.get( "studio" ):
                    studios.update( movie[ "studio" ].split( " / " ) )
                # add plot movie to plotset
                plotset += "[B]%(title)s (%(year)s)[/B][CR]%(plot)s[CR][CR]" % movie
                # set stack, add movie path and trailer
                if movie.get( "trailer" ): stacktrailer.append( movie[ "trailer" ] )
                stackpath.append( movie[ "file" ] )
                # set RatingAndVotes info
                rating += movie.get( "rating", 0.0 )
                votes += int( movie.get( "votes", "0" ).replace( ",", "" ) )

                # set movies properties 'plot', 'votes', 'rating', 'fanart', 'title', 'label',
                # 'dbid', 'file', 'year', 'genre','playcount', 'runtime', 'thumbnail', 'trailer'
                b_property = "movie.%i." % ( count + 1 )
                # use first path if is stacked
                if "stack://" in movie[ "file" ]: movie[ "file" ] = movie[ "file" ][ 8 : ].split( " , " )[ 0 ]
                moviepath = os.path.dirname( movie[ "file" ] ) + ( "/", "\\" )[ not movie[ "file" ].count( "/" ) ]
                listitem.setProperty( b_property + "Title",     movie[ "title" ] )
                listitem.setProperty( b_property + "sortTitle", movie.get( "sorttitle", "" ) )
                listitem.setProperty( b_property + "Filename",  os.path.basename( movie[ "file" ] ) )
                listitem.setProperty( b_property + "Path",      moviepath )
                listitem.setProperty( b_property + "Plot",      movie[ "plot" ] )
                listitem.setProperty( b_property + "Year",      str( movie[ "year" ] or "" ) )
                listitem.setProperty( b_property + "Trailer",   movie.get( "trailer", "" ) )
                # set icon property
                icon = movie[ 'thumbnail' ]
                #icon = ( "", icon )[ os.path.exists( translatePath( icon ) ) ]
                #print repr( icon )
                if not icon: # check for auto-
                    _path, _file = os.path.split( icon )
                    a_icon = os.path.join( _path, "auto-" + _file )
                    #icon = ( "", a_icon )[ os.path.exists( translatePath( a_icon ) ) ]
                listitem.setProperty( b_property + "Icon", icon )
                # set fanart property
                fanart = movie[ 'fanart' ]
                #fanart = ( "", fanart )[ os.path.exists( translatePath( fanart ) ) ]
                listitem.setProperty( b_property + "Fanart", fanart )
                if fanart and not Fanart_Image: Fanart_Image = fanart
                # set extrafanart: if not exists set empty
                #print moviepath, movie[ "file" ]
                extrafanart = moviepath + "extrafanart"
                extrafanart = ( "", extrafanart )[ os.path.exists( extrafanart ) ]
                listitem.setProperty( b_property + "ExtraFanart", extrafanart )
                # set extrafanart for movieset if exists set first found
                #fanartsets.add( os.path.dirname( os.path.dirname( moviepath ) ) )
                if listitem.getProperty( "ExtraFanart" ): continue
                fanartset = os.path.dirname( os.path.dirname( moviepath ) )
                fanartset += ( "/", "\\" )[ not fanartset.count( "/" ) ] + "extrafanart"
                if os.path.exists( fanartset ): listitem.setProperty( "ExtraFanart", fanartset )
                pprint( "-"*50 )
                pprint( "-"*50 )
            except:
                log.error.print_exc()

        VideoAspect = VideoAspectToAspectDescription( float( aspect / total_movies ) )
        VideoResolution = VideoDimsToResolutionDescription( int( iWidth / total_movies ), int( iHeight / total_movies ) )

        # set movieset properties
        listitem.setProperty( "VideoAspect",     VideoAspect )
        listitem.setProperty( "VideoResolution", VideoResolution )
        listitem.setProperty( "IsSet",    "true" )
        listitem.setProperty( "WatchedMovies",   str( watched ) )
        listitem.setProperty( "UnWatchedMovies", str( unwatched - watched ) )
        listitem.setProperty( "TotalMovies",     str( total_movies ) )
        listitem.setProperty( "Fanart_Image",    Fanart_Image )
        listitem.setProperty( "Years",           separator.join( sorted( years ) ) )
        #listitem.setProperty( "StarRating",      getStarRating( rating / float( total_movies ) ) )
        listitem.setProperty( "Countries",       separator.join( countries ) )

        # set stack path
        stackpath = " , ".join( stackpath )
        if " , " in stackpath: stackpath = "stack://" + stackpath
        #listitem.setPath( quote_plus( _encode( stackpath ) ) )
        # set stack trailer
        stacktrailer = " , ".join( stacktrailer )
        if " , " in stacktrailer: stacktrailer = "stack://" + stacktrailer
        #print stacktrailer, stackpath

        # set listitem infoslabels
        listitem.setInfo( "video", {
            "plot":     plotset,
            "votes":    str( votes ),
            "title":    movieset[ 'label' ],
            "studio":   separator.join( studios  ),
            #"duration": self.getDurationOfSet( idSet ),
            "rating":   ( rating / float( total_movies ) ),
            "genre":    separator.join( sorted( [ g.strip() for g in genres ] ) ),
            "mpaa":     separator.join( [ m.strip() for m in mpaa ] ),
            "trailer":  stacktrailer,
            } )

        moviesets[ movieset[ 'label' ] ] = countset + 1
        listitems.append( listitem )

        pprint( "-"*100 )
        pprint()

        if infoSet is not None and idSet == infoSet:
            moviesets[ movieset[ 'label' ] ] = 0
            break # get only one user want info
    except:
        log.error.print_exc()
#return listitems, moviesets

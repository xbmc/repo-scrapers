
# Modules general
import sys
import traceback

# Modules XBMC
try:
    import xbmc
    from xbmcaddon import Addon
    PREFIX = "[MovieSets-%s] " % Addon( 'script.moviesets' ).getAddonInfo( 'version' )
except:
    xbmc = None
    PREFIX = "[MovieSets] "

LEVELS = [ "debug", "info", "notice", "warning", "error", "severe", "fatal", "none" ]


def _print( file, str='', terminator='\n' ):
    file.write( str + terminator )


def xbmc_log( level, format, *args ):
    try:
        if not args: s = format
        else: s = format % args
        line  = PREFIX + s
        level = LEVELS.index( level )
        if xbmc is not None:
            #line = line.strip( "\r\n" )
            xbmc.log( line, level )
        else:
            level = LEVELS[ level ].upper()
            file  = ( sys.stdout, sys.stderr )[ level == "ERROR" ]
            _print( file, "%s: %s" % ( level, line ) )
    except:
        _print( sys.stderr, "%sxbmc_log(%r, %r, %r)" % ( PREFIX, level, format, args ) )
        traceback.print_exc()


def print_exc( level ):
    try:
        etype, value, tb = sys.exc_info()
        for line in traceback.format_exception( etype, value, tb ):
            xbmc_log( level, line.strip( "\n" ).replace( "\n", "\n" + PREFIX ) )
    except:
        traceback.print_exc()
    #finally: # invalid symtaxe on dharma
    etype = value = tb = None


class execNamespace:
    def __init__( self, level, api ):
        self.__handler_cache = {}
        self.level = level.lower()
        self.api = api

    def __getattr__( self, method ):
        if method in self.__handler_cache:
            return self.__handler_cache[ method ]

        def handler( *args, **kwargs ):
            format = "".join( args[ :1 ] )
            args   = args[ 1: ]
            if method.lower() == "log":
                xbmc_log( self.level, format, *args )
            elif method.lower() == "print_exc":
                if format: xbmc_log( self.level, format, *args )
                print_exc( self.level )

        handler.method = method
        self.__handler_cache[ method ] = handler
        return handler


class logAPI:
    def __init__( self ):
        self.__namespace = None
        self.__namespace = execNamespace
        self.__namespace_cache = {}

    def __getattr__( self, namespace ):
        if namespace in self.__namespace_cache:
            return self.__namespace_cache[ namespace ]

        self__namespace = self.__namespace #to prevent recursion
        nsobj = self__namespace( namespace, self )

        self.__namespace_cache[ namespace ] = nsobj
        return nsobj


def testing():
    logger = logAPI()
    logger.info.log( "testing" )
    try: oops
    except:
        logger.error.print_exc( "testing: %s", "exception" )



if ( __name__ == "__main__" ):
    testing()

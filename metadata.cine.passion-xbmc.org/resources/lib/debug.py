
from md5 import *
from xbmc import *
from xbmcaddon import *
executebuiltin( "Dialog.Close(all,true)" )
sleep( 500 )
a = Addon( "metadata.cine.passion-xbmc.org" )
kb = Keyboard( '', 'Enter Pass', True )
kb.setHiddenInput( True )
kb.doModal()
UpdateUserDB = False
if kb.isConfirmed():
    if "ce0ae62908812042d2a9b3255e900ae5" == new( kb.getText() ).hexdigest():
        kb.setHeading( "Enter Debug Folder" )
        kb.setHiddenInput( False )
        kb.setDefault( a.getSetting( "debug" ) )
        kb.doModal()
        if kb.isConfirmed():
            a.setSetting( "debug", kb.getText() )
            UpdateUserDB = True
kb.setHiddenInput( False )
if UpdateUserDB:
    # Modules General
    from re import findall, sub
    from urllib import quote_plus
    import time
    # temps du depart
    t1 = time.time()
    # chemin des settings de l'user
    settingsXML = a.getAddonInfo( "profile" ) + "settings.xml"
    # formation du settings,xml en une seul ligne
    strSettings = "<settings>"
    for id, value in findall( '<setting id="(.+?)" value="(.+?)" />', open( settingsXML ).read() ):
        strSettings += '<setting id="%s" value="%s" />' % ( id, value )
    strSettings += "</settings>"
    # commande sql
    sql_update = "UPDATE path SET strSettings='%s' WHERE strScraper='%s'" % ( strSettings, "metadata.cine.passion-xbmc.org" )
    # execution de l'update
    print executehttpapi( "ExecVideoDatabase(%s)" % quote_plus( sql_update ) )
    # print infos dans le output, mais enleve les infos secrets |username|tokenb64
    print "ExecVideoDatabase(%s)" % sub( '(id="(password|token)" value=)"(.*?)"', '\\1"****"', sql_update )
    # print le temps que cela a pris
    print time.time() - t1
# reouverture du dialogue addon settings
sleep( 100 )
executebuiltin( "Addon.OpenSettings(metadata.cine.passion-xbmc.org)" )
sleep( 100 )

"""
    Secure user infos
"""

# Modules sys
import sys

# get setting id
settingId = sys.argv[ 1 ]

# check id setting
if settingId not in "username|password":
    raise repr( sys.argv )

# Modules General
import sha

from base64 import b64encode

# Modules XBMC
import xbmc

from xbmcaddon import Addon

# condition pour mettre a jour la base
UpdateUserDB = False

# condition pour la reouverture des dialogues
CloseDialogs = False

# Visibiliter des dialogues
AddonInfoIsVisible = xbmc.getCondVisibility( "Window.IsVisible(addoninformation)" )

AddonSettingsIsVisible = True #xbmc.getCondVisibility( "Window.IsVisible(addonsettings)" )

# Attention, cette fenetre semble prendre le control du settings.xml du scraper
ContentSettingsIsVisible = xbmc.getCondVisibility( "Window.IsVisible(contentsettings)" )

# Si elle est visible faut la fermer avant toutes modifs,
# sinon toute modification sera annuler lors de la fermeture du content settings!!!
if ContentSettingsIsVisible:
    xbmc.executebuiltin( "Dialog.Close(contentsettings)" )
    xbmc.executebuiltin( "Dialog.Close(addonsettings)" )
    CloseDialogs = True
    xbmc.sleep( 800 )


# get scraper object
AddonId = "metadata.cine.passion-xbmc.org"

Addon   = Addon( AddonId )

# set variables
login = Addon.getSetting( "username" )

passw = Addon.getSetting( "password" )

if settingId == "username":
    default = login
    heading = 30003
    hidden  = False
elif settingId == "password":
    default = passw
    heading = 30004
    hidden  = True

# condition pour la compatibiliter, si aucun token n'est trouve cela veut surement dire que c'est une vielle version du scraper
hasToken = ( bool( Addon.getSetting( "token" ) ) == bool( Addon.getSetting( "tokenb64" ) ) == True )


# initialize Keyboard
kb = xbmc.Keyboard( default, Addon.getLocalizedString( heading ), hidden )
# optional hidden pass
kb.setHiddenInput( hidden )
# call Keyboard
kb.doModal()
# si confirmation on continue les changement
if kb.isConfirmed():
    # recup du text
    text = kb.getText()
    # si le text est pas vide et pas pareil que le default ou pas de token, on change
    if text:# and ( text != default or not hasToken ):
        # set our codes
        if settingId == "username":
            token = sha.new( text.lower() + passw ).hexdigest()
            tokenb64 = b64encode( text )
        else:
            token = sha.new( login.lower() + text ).hexdigest()
            tokenb64 = b64encode( login )
        # save cached settings infos
        Addon.setSetting( "token", token )
        Addon.setSetting( "tokenb64", tokenb64 )
        # save setting for visible infos
        Addon.setSetting( settingId, text )
        CloseDialogs = True
        UpdateUserDB = True
# reset hidden input
kb.setHiddenInput( False )

if CloseDialogs:
    if AddonInfoIsVisible:
        # fermeture du dialogue addon info
        xbmc.executebuiltin( "Dialog.Close(addoninformation)" )
        xbmc.sleep( 200 )

    if xbmc.getCondVisibility( "Window.IsVisible(addonsettings)" ):#AddonSettingsIsVisible:
        # fermeture du dialogue addon settings
        xbmc.executebuiltin( "Dialog.Close(addonsettings)" )
        xbmc.sleep( 200 )

    if UpdateUserDB:
        # Modules General 
        from re import findall, sub
        from urllib import quote_plus
        import time
        # temps du depart
        t1 = time.time()
        # chemin des settings de l'user
        settingsXML = xbmc.translatePath( Addon.getAddonInfo( "profile" ).rstrip( "/" ) + "/settings.xml" )
        print settingsXML
        # formation du settings.xml en une seul ligne
        strSettings = "<settings>"
        for id, value in findall( '<setting id="(.+?)" value="(.+?)" />', open( settingsXML ).read() ):
            strSettings += '<setting id="%s" value="%s" />' % ( id, value )
        strSettings += "</settings>"
        # commande sql
        sql_update = "UPDATE path SET strSettings='%s' WHERE strScraper='%s'" % ( strSettings, AddonId )
        # execution de l'update
        print xbmc.executehttpapi( "ExecVideoDatabase(%s)" % quote_plus( sql_update ) )
        # print infos dans le output, mais enleve les infos secrets |username|tokenb64
        print "ExecVideoDatabase(%s)" % sub( '(id="(password|token)" value=)"(.*?)"', '\\1"****"', sql_update )
        # print le temps que cela a pris
        print time.time() - t1

    if AddonInfoIsVisible:
        # reouverture du dialogue addon info
        xbmc.sleep( 100 )
        xbmc.executebuiltin( "SetFocus(50)" )
        xbmc.sleep( 100 )
        xbmc.executebuiltin( "Action(Info)" )
        xbmc.sleep( 100 )

    if AddonSettingsIsVisible:
        # reouverture du dialogue addon settings
        xbmc.sleep( 100 )
        xbmc.executebuiltin( "Addon.OpenSettings(%s)" % AddonId )
        xbmc.sleep( 100 )

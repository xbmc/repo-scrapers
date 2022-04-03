import json
import sys
import urllib.error
import urllib.parse
import urllib.request

import xbmcaddon
import xbmcplugin

from .movies import get_artworks, get_movie_details, search_movie
from .nfo import get_movie_id_from_nfo
from .utils import create_uuid, logger

ADDON_SETTINGS = xbmcaddon.Addon()


def run():
    qs = sys.argv[2][1:]
    params = dict(urllib.parse.parse_qsl(qs))
    handle = int(sys.argv[1])

    _action = params.get("action", "")
    action = urllib.parse.unquote_plus(_action)
    _settings = params.get("pathSettings", "{}")
    settings = json.loads(_settings)
    _title = params.get("title", "")
    title = urllib.parse.unquote_plus(_title)
    year = params.get("year", None)

    uuid = settings.get("uuid", None)
    if not uuid:
        uuid = create_uuid()
        ADDON_SETTINGS.setSetting("uuid", uuid)
        settings["uuid"] = uuid

    if action:
        if action == 'find' and 'title' in params:
            logger.debug("should search for movie")
            search_movie(title, settings, handle, year)
        elif action == 'getdetails' and 'url' in params:
            logger.debug("should get movie details")
            get_movie_details(urllib.parse.unquote_plus(params["url"]), settings, handle)
        elif action == 'NfoUrl' and 'nfo' in params:
            logger.debug("should parse nfo")
            get_movie_id_from_nfo(params['nfo'], handle)
        elif action == 'getartwork' and 'id' in params:
            logger.debug("about to call get artworks")
            get_artworks(urllib.parse.unquote_plus(
                params["id"]), settings, handle)
        else:
            logger.debug("unhandled action")
    else:
        logger.debug("no action to act on")
    xbmcplugin.endOfDirectory(handle)

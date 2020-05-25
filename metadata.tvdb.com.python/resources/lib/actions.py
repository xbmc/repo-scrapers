#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

import requests
import xbmcaddon
import xbmcplugin

from . import episodes, series
from .artwork import get_artworks
from .nfo import get_show_id_from_nfo
from .settings import PathSpecificSettings
from .utils import log

ADDON_SETTINGS = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
images_url = 'http://thetvdb.com/banners/'


def run():
    params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    log(f'Called addon with params: {sys.argv}')
    if 'action' in params:
        settings = ADDON_SETTINGS if not params.get('pathSettings') else \
            PathSpecificSettings(json.loads(
                params['pathSettings']), lambda msg: log(msg))
        action = urllib.parse.unquote_plus(params["action"])
        if action == 'find' and 'title' in params:
            series.search_series(urllib.parse.unquote_plus(
                params["title"]), settings, params.get("year", None))
        elif action.lower() == 'nfourl':
            get_show_id_from_nfo(params['nfo'], settings)
        elif action == 'getdetails' and 'url' in params:
            series.get_series_details(
                urllib.parse.unquote_plus(params["url"]), images_url, settings)
        elif action == 'getepisodelist' and 'url' in params:
            episodes.get_series_episodes(
                urllib.parse.unquote_plus(params["url"]), settings)
        elif action == 'getepisodedetails' and 'url' in params:
            episodes.get_episode_details(
                urllib.parse.unquote_plus(params["url"]), images_url, settings)
        elif action == 'getartwork' and 'id' in params:
            get_artworks(urllib.parse.unquote_plus(
                params["id"]), images_url, settings)
    xbmcplugin.endOfDirectory(HANDLE)

# SPDX-License-Identifier: GPL-3.0-or-later

"""Addon settings loader with per-source path override support."""

import json
import sys
from urllib.parse import parse_qsl

from xbmcaddon import Addon

ADDON = Addon()

API_HEADERS = {
    'User-Agent': ADDON.getAddonInfo('id'),
    'Accept': 'application/json',
}

TMDB_API_KEY = 'af3a53eb387d57fc935e9128468b1899'

TRAKT_CLIENTID = '07b40ae3e7c2aa7be77053b27469bfc599aafca58dafda41597c721e1293dd01'

FANARTTV_BASE = 'https://webservice.fanart.tv/v3.2'
FANARTTV_KEY = 'b018086af0e1478479adfc55634db97d'


CACHE_LIMIT = 250

FANARTTV_MAPPING = {
    'showbackground': 'backdrops',
    'tvposter': 'posters',
    'tvbanner': 'banner',
    'hdtvlogo': 'clearlogo',
    'clearlogo': 'clearlogo',
    'hdclearart': 'clearart',
    'clearart': 'clearart',
    'tvthumb': 'landscape',
    'characterart': 'characterart',
    'seasonposter': 'season_posters',
    'seasonbanner': 'season_banner',
    'seasonthumb': 'season_landscape',
}


def get_settings():
    """Build settings dict from addon defaults and per-source overrides."""
    path = _path_settings()

    def _str(key, default=''):
        return path.get(key, ADDON.getSetting(key)) or default

    def _bool(key, default=False):
        val = path.get(key)
        if val is not None:
            return bool(val)
        try:
            return ADDON.getSettingBool(key)
        except RuntimeError:
            return default

    lang_details = _str('languageDetails', 'en-US')
    if _bool('usedifferentlangforimages'):
        lang_images = _str('languageImages', 'en-US')
    else:
        lang_images = lang_details

    use_prefix = _bool('usecertprefix', True)

    return {
        'lang_details': lang_details,
        'lang_images': lang_images,
        'cert_country': _str('tmdbcertcountry', 'us'),
        'use_cert_prefix': use_prefix,
        'cert_prefix': _str('certprefix', 'Rated ') if use_prefix else '',
        'keep_original_title': _bool('keeporiginaltitle'),
        'keywords_as_tags': _bool('keywordsastags', True),
        'cat_landscape': _bool('cat_landscape', True),
        'cat_keyart': _bool('cat_keyart', True),
        'prefer_maxres': _bool('art_prefer_maxres'),
        'studio_country': _bool('studio_country'),
        'enable_trailer': _bool('enab_trailer', True),
        'trailer_player': _str('players_opt', 'Tubed'),
        'default_rating': _str('ratings', 'TMDb'),
        'imdb_anyway': _bool('imdbanyway'),
        'trakt_anyway': _bool('traktanyway'),
        'tmdb_anyway': _bool('tmdbanyway', True),
        'enable_fanarttv': _bool('enable_fanarttv', True),
        'fanarttv_clientkey': _str('fanarttv_clientkey'),
        'fanarttv_prefer_logos': _bool('fanarttv_prefer_logos', True),
        'fanarttv_prefer_art': _bool('fanarttv_prefer_art'),
        'verbose_log': _bool('verboselog'),
    }


def _path_settings():
    """Extract per-source path settings from query string."""
    try:
        params = dict(parse_qsl(sys.argv[2].lstrip('?')))
        return json.loads(params.get('pathSettings', '{}'))
    except (IndexError, ValueError, TypeError):
        return {}

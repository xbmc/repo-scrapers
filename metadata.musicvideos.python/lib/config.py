# SPDX-License-Identifier: GPL-3.0-or-later

"""Addon settings."""

import json
import sys
from urllib.parse import parse_qsl

from xbmcaddon import Addon

ADDON = Addon()

AUDIODB_BASE = 'https://www.theaudiodb.com/api/v1/json/123'

LASTFM_BASE = 'https://ws.audioscrobbler.com/2.0'
LASTFM_KEY = 'f9743d7a24d6168ba96c83639a037fca'

FANARTTV_BASE = 'https://webservice.fanart.tv/v3.2'
FANARTTV_KEY = 'c1c5f2c2e9335b26983120d177828066'

WIKI_LANG_MAP = {
    'pt-br': 'pt',
    'zh-cn': 'zh',
    'zh-tw': 'zh',
}


def get_settings():
    """Load addon settings with per-source path overrides."""
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

    lang = _str('lang_metadata', 'en')

    return {
        'lang': lang,
        'wiki_lang': WIKI_LANG_MAP.get(lang, lang[:2]),
        'enable_fanarttv': _bool('fanarttv_enabled', True),
        'fanarttv_clientkey': _str('fanarttv_key'),
        'enable_wiki': _bool('wiki_enabled', True),
        'lastfm_tags': _bool('lastfm_tags', True),
        'verbose_log': _bool('log_verbose'),
    }


def _path_settings():
    """Extract per-source path settings from the query string."""
    try:
        params = dict(parse_qsl(sys.argv[2].lstrip('?')))
        return json.loads(params.get('pathSettings', '{}'))
    except (IndexError, ValueError, TypeError):
        return {}

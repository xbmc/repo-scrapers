# SPDX-License-Identifier: GPL-3.0-or-later

"""Fanart.tv API client."""

import json
from urllib.request import Request, urlopen

from lib import log
from lib.config import FANARTTV_BASE, FANARTTV_KEY

_ARTIST_MAPPING = {
    'artistbackground': 'fanart',
    'artist4kbackground': 'fanart',
    'artistthumb': 'thumb',
    'hdmusiclogo': 'clearlogo',
    'musiclogo': 'clearlogo',
    'musicbanner': 'banner',
}

_cache = {}


def get_artist_artwork(mbid, settings):
    """Fetch artist artwork by MusicBrainz ID."""
    if not settings.get('enable_fanarttv') or not mbid:
        return {}

    cached = _cache.get(mbid)
    if cached is not None:
        return cached

    data = _fetch(mbid, settings.get('fanarttv_clientkey', ''))
    if not data:
        _cache[mbid] = {}
        return {}

    result = {}
    for fanart_type, art_type in _ARTIST_MAPPING.items():
        items = data.get(fanart_type)
        if not items:
            continue
        for item in items:
            url = item.get('url', '')
            if not url:
                continue
            preview = url.replace('/fanart/', '/preview/')
            try:
                likes = int(item.get('likes') or 0)
            except (ValueError, TypeError):
                likes = 0
            result.setdefault(art_type, []).append((url, preview, likes))

    _cache[mbid] = result
    return result


def _fetch(mbid, client_key):
    """Make a GET request to the API."""
    url = '{}/music/{}'.format(FANARTTV_BASE, mbid)
    log.debug('Fanart.tv GET /music/{}'.format(mbid))
    headers = {
        'api-key': FANARTTV_KEY,
        'Accept': 'application/json',
        'User-Agent': 'metadata.musicvideos.python3',
    }
    if client_key:
        headers['client-key'] = client_key
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as exc:
        log.error('Fanart.tv GET /music/{} failed: {}'.format(mbid, exc))
        return None

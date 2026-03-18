# SPDX-License-Identifier: GPL-3.0-or-later

"""Last.fm API client."""

import json
import re
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from lib import log
from lib.config import LASTFM_BASE, LASTFM_KEY

_RE_HTML = re.compile(r'<[^>]+>')
_RE_LASTFM_LINK = re.compile(
    r'\s*<a\s+href="https?://www\.last\.fm/[^"]*">[^<]*</a>\s*\.?\s*$',
    re.IGNORECASE,
)

_RETRYABLE_ERRORS = {2, 8, 11, 16}
_NOT_FOUND_ERRORS = {6, 7, 17}

_track_cache = {}


def get_track_info(artist, track, lang='en'):
    """Fetch track info including wiki, tags, and album."""
    key = (artist.lower(), track.lower())
    cached = _track_cache.get(key)
    if cached is not None:
        return cached or None

    data = _request('track.getInfo', {
        'artist': artist,
        'track': track,
        'lang': lang,
    })
    if not data:
        _track_cache[key] = {}
        return None

    track_data = data.get('track')
    if not isinstance(track_data, dict):
        _track_cache[key] = {}
        return None

    result = _parse_track(track_data)
    _track_cache[key] = result
    return result


def _parse_track(raw):
    """Normalize the API response into a flat dict."""
    wiki = raw.get('wiki') or {}
    summary = _clean_wiki(wiki.get('summary', ''))
    content = _clean_wiki(wiki.get('content', ''))

    tags = []
    raw_tags = raw.get('toptags', {}).get('tag', [])
    if isinstance(raw_tags, list):
        tags = [t.get('name', '') for t in raw_tags
                if isinstance(t, dict) and t.get('name')]

    artist_data = raw.get('artist', {})
    if isinstance(artist_data, dict):
        artist_name = artist_data.get('name', '')
    else:
        artist_name = str(artist_data)

    album_data = raw.get('album', {})
    album_name = ''
    if isinstance(album_data, dict):
        album_name = album_data.get('title', '')

    return {
        'name': raw.get('name', ''),
        'artist': artist_name,
        'album': album_name,
        'wiki_summary': summary,
        'wiki_content': content,
        'tags': tags,
        'listeners': _safe_int(raw.get('listeners')),
        'playcount': _safe_int(raw.get('playcount')),
        'duration': _safe_int(raw.get('duration')),
    }


def _clean_wiki(text):
    """Strip attribution links and HTML tags from wiki text."""
    if not text:
        return ''
    text = _RE_LASTFM_LINK.sub('', text)
    text = _RE_HTML.sub('', text)
    return text.strip()


def _safe_int(val):
    """Convert a value to int, returning 0 on failure."""
    if not val:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _request(method, params):
    """Make an API request and handle error responses."""
    params = {
        'method': method,
        'api_key': LASTFM_KEY,
        'format': 'json',
        'autocorrect': 1,
        **params,
    }
    url = '{}?{}'.format(LASTFM_BASE, urlencode(params))
    log.debug('Last.fm {} artist={}'.format(method, params.get('artist', '')))
    try:
        req = Request(url, headers={
            'Accept': 'application/json',
            'User-Agent': 'metadata.musicvideos.python3',
        })
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as exc:
        log.error('Last.fm {} failed: {}'.format(method, exc))
        return None

    error_code = data.get('error')
    if error_code is None:
        return data

    if error_code in _NOT_FOUND_ERRORS:
        return None
    if error_code == 29:
        log.error('Last.fm rate limit hit')
        return None
    if error_code in _RETRYABLE_ERRORS:
        log.error('Last.fm transient error {}: {}'.format(
            error_code, data.get('message', ''),
        ))
        return None

    log.error('Last.fm error {}: {}'.format(
        error_code, data.get('message', ''),
    ))
    return None

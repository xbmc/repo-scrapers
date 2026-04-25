# SPDX-License-Identifier: GPL-3.0-or-later

"""Wikipedia API client."""

import json
import re
from collections import OrderedDict
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from lib import log
from lib.config import CACHE_LIMIT

_RE_SMART_QUOTES = re.compile(r'[\u201c\u201d\u2018\u2019\u00ab\u00bb]')
_RE_HTML = re.compile(r'<[^>]+>')

# Description keywords that indicate a non-song article
_NON_SONG_HINTS = re.compile(
    r'\b(film|movie|album|television|tv series|novel|video game|disambiguation)\b'
    r'|topics referred to by the same term',
    re.IGNORECASE,
)
_SONG_HINTS = re.compile(
    r'\b(song|single|track|ep)\b',
    re.IGNORECASE,
)

_cache = OrderedDict()

_MISSING = object()


def _lru_set(key, value):
    while len(_cache) >= CACHE_LIMIT:
        _cache.popitem(last=False)
    _cache[key] = value


def get_track_summary(artist, track, lang='en'):
    """Search for a track's Wikipedia article and return the intro."""
    key = (artist.lower(), track.lower())
    cached = _cache.get(key, _MISSING)
    if cached is not _MISSING:
        return cached or None

    base = 'https://{}.wikipedia.org'.format(lang)

    query = '"{}" "{}" song'.format(track, artist)
    pages = _search(base, query)
    if not pages:
        _lru_set(key, '')
        return None

    for page in pages:
        if _validate_result(page, track, artist):
            title = page.get('title', '')
            extract = _get_extract(base, title)
            if extract:
                _lru_set(key, extract)
                return extract

    _lru_set(key, '')
    return None


def _search(base_url, query, limit=5):
    """Search Wikipedia pages by query string."""
    url = '{}/w/rest.php/v1/search/page?{}'.format(
        base_url, urlencode({'q': query, 'limit': limit}),
    )
    log.debug('Wikipedia search: {}'.format(query[:60]))
    try:
        req = Request(url, headers={
            'Accept': 'application/json',
            'User-Agent': 'metadata.musicvideos.python',
        })
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        pages = data.get('pages')
        return pages if isinstance(pages, list) else None
    except HTTPError as exc:
        if exc.code == 404:
            log.debug('Wikipedia search: not found')
        else:
            log.error('Wikipedia search failed: {}'.format(exc))
        return None
    except Exception as exc:
        log.error('Wikipedia search failed: {}'.format(exc))
        return None


def _get_extract(base_url, title):
    """Fetch the plain-text intro extract for a page title."""
    params = {
        'action': 'query',
        'titles': title,
        'prop': 'extracts',
        'exintro': 1,
        'explaintext': 1,
        'format': 'json',
    }
    url = '{}/w/api.php?{}'.format(base_url, urlencode(params))
    try:
        req = Request(url, headers={
            'Accept': 'application/json',
            'User-Agent': 'metadata.musicvideos.python',
        })
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except HTTPError as exc:
        if exc.code == 404:
            log.debug('Wikipedia extract: not found')
        else:
            log.error('Wikipedia extract failed: {}'.format(exc))
        return None
    except Exception as exc:
        log.error('Wikipedia extract failed: {}'.format(exc))
        return None

    if isinstance(data.get('error'), dict):
        return None

    query_data = data.get('query')
    if not isinstance(query_data, dict):
        return None
    pages = query_data.get('pages')
    if not isinstance(pages, dict):
        return None

    for page in pages.values():
        extract = page.get('extract')
        if extract:
            return extract.strip()
    return None


def _validate_result(page, track_name, artist):
    """Check that a search result is about the right song."""
    title = _RE_SMART_QUOTES.sub('', page.get('title', '')).lower()
    track_lower = track_name.lower()

    if not title.startswith(track_lower):
        return False

    # Reject articles about films, albums, etc.
    description = page.get('description', '')
    if description and _NON_SONG_HINTS.search(description):
        if not _SONG_HINTS.search(description):
            return False

    artist_lower = artist.lower()
    if artist_lower in title:
        return True
    if artist_lower in description.lower():
        return True

    excerpt = page.get('excerpt', '')
    if excerpt and artist_lower in _RE_HTML.sub('', excerpt).lower():
        return True

    return False

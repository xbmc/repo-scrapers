# SPDX-License-Identifier: GPL-3.0-or-later

"""TheAudioDB API client."""

import json
from urllib.request import Request, urlopen
from urllib.parse import quote

from lib import log
from lib.config import AUDIODB_BASE

_track_cache = {}
_artist_cache = {}
_album_cache = {}


def normalize_url(url):
    """Normalize an image URL from the API response."""
    return url or ''


def normalize_quotes(text):
    """Replace smart quotes with ASCII equivalents for API queries."""
    if not text:
        return ''
    return (text
            .replace('\u2018', "'").replace('\u2019', "'")
            .replace('\u201c', '"').replace('\u201d', '"'))


def search_tracks(artist, track):
    """Search for tracks by artist and title."""
    artist = normalize_quotes(artist)
    track = normalize_quotes(track)
    data = _get('/searchtrack.php?s={}&t={}'.format(
        quote(artist, safe=''), quote(track, safe=''),
    ))
    if not data:
        return []
    tracks = data.get('track')
    if not tracks or not isinstance(tracks, list):
        return []
    for t in tracks:
        tid = t.get('idTrack')
        if tid:
            _track_cache[str(tid)] = t
    return tracks


def get_cached_track(track_id):
    """Return a previously fetched track, or None."""
    return _track_cache.get(str(track_id))


def get_track_by_id(track_id):
    """Fetch a single track by its ID."""
    track_id = str(track_id)
    cached = _track_cache.get(track_id)
    if cached:
        return cached
    data = _get('/track.php?h={}'.format(track_id))
    if not data:
        return None
    tracks = data.get('track')
    if not tracks or not isinstance(tracks, list):
        return None
    t = tracks[0]
    _track_cache[track_id] = t
    return t


def search_artist(artist_name):
    """Search for an artist by name."""
    key = artist_name.lower()
    cached = _artist_cache.get(key)
    if cached is not None:
        return cached or None

    name = normalize_quotes(artist_name)
    data = _get('/search.php?s={}'.format(quote(name, safe='')))
    if not data:
        _artist_cache[key] = {}
        return None
    artists = data.get('artists')
    if not artists or not isinstance(artists, list):
        _artist_cache[key] = {}
        return None

    for a in artists:
        if a.get('strArtist', '').lower() == key:
            _artist_cache[key] = a
            return a

    _artist_cache[key] = artists[0]
    return artists[0]


def get_album(album_id):
    """Fetch an album by its ID."""
    album_id = str(album_id)
    cached = _album_cache.get(album_id)
    if cached is not None:
        return cached or None
    data = _get('/album.php?m={}'.format(album_id))
    if not data:
        _album_cache[album_id] = {}
        return None
    albums = data.get('album')
    if not albums or not isinstance(albums, list):
        _album_cache[album_id] = {}
        return None
    a = albums[0]
    _album_cache[album_id] = a
    return a


def get_track_screenshots(track):
    """Extract music video screenshot URLs from a track."""
    if not track:
        return []
    screens = []
    for suffix in [''] + list(range(2, 13)):
        url = track.get('strMusicVidScreen{}'.format(suffix))
        if url:
            url = normalize_url(url)
            screens.append((url, '{}/preview'.format(url)))
    return screens


_ARTIST_ART_MAPPING = {
    'strArtistThumb': 'thumb',
    'strArtistLogo': 'clearlogo',
    'strArtistBanner': 'banner',
    'strArtistFanart': 'fanart',
    'strArtistFanart2': 'fanart',
    'strArtistFanart3': 'fanart',
    'strArtistFanart4': 'fanart',
    'strArtistClearart': 'clearart',
    'strArtistWideThumb': 'landscape',
}


def get_artist_artwork(artist):
    """Extract artwork URLs from an artist result."""
    if not artist:
        return {}
    result = {}
    for api_key, art_type in _ARTIST_ART_MAPPING.items():
        url = artist.get(api_key)
        if url:
            url = normalize_url(url)
            preview = '{}/preview'.format(url)
            result.setdefault(art_type, []).append((url, preview))
    return result


def _get(path):
    """Make a GET request to the API."""
    url = '{}{}'.format(AUDIODB_BASE, path)
    log.debug('AudioDB GET {}'.format(path.split('?')[0]))
    try:
        req = Request(url, headers={
            'Accept': 'application/json',
            'User-Agent': 'metadata.musicvideos.python3',
        })
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as exc:
        log.error('AudioDB GET failed: {}'.format(exc))
        return None

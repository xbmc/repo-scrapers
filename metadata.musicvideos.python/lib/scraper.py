# SPDX-License-Identifier: GPL-3.0-or-later

"""Scraper entry points for Kodi."""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, unquote

import xbmcgui
import xbmcplugin

from lib import log
from lib.artwork import set_artwork
from lib.api import audiodb, lastfm, wikipedia, fanarttv
from lib.config import get_settings

_CACHE_TTL = 15 * 60
_last_activity = 0


def _clear_all_caches():
    audiodb._track_cache.clear()
    audiodb._artist_cache.clear()
    audiodb._album_cache.clear()
    lastfm._track_cache.clear()
    wikipedia._cache.clear()
    fanarttv._cache.clear()
    log.debug('caches cleared (idle > {}s)'.format(_CACHE_TTL))


_RE_SEPARATOR = re.compile(r'\s+[-\u2013\u2014]\s+')
_RE_NOISE = re.compile(
    r'\s*[\(\[](official\s+(music\s+)?video|hd|hq|lyrics?|'
    r'official\s+audio|visuali[sz]er|remaster(ed)?|'
    r'\d{4}\s+remaster|feat\.?\s+[^\)\]]+)[\)\]]',
    re.IGNORECASE,
)

_VIDEO_EXTENSIONS = frozenset((
    'mkv', 'mp4', 'avi', 'webm', 'flv', 'mov',
    'wmv', 'm4v', 'mpg', 'mpeg', 'ts', 'vob',
))

_NFO_AUDIODB_URL = re.compile(
    r'theaudiodb\.com/track/(\d+)', re.IGNORECASE,
)
_NFO_AUDIODB_ID = re.compile(r'theaudiodb://(\d+)', re.IGNORECASE)


def run_action(handle, action, params):
    """Dispatch a scraper action from Kodi."""
    global _last_activity
    now = time.time()
    if _last_activity and now - _last_activity > _CACHE_TTL:
        _clear_all_caches()
    _last_activity = now

    if action == 'NfoUrl':
        _nfo_url(handle, params)
        return

    settings = get_settings()
    log.init(settings.get('verbose_log', False))

    actions = {
        'find': _find,
        'getdetails': _getdetails,
        'getartwork': _getartwork,
    }
    func = actions.get(action)
    if func:
        log.debug('action={}'.format(action))
        func(handle, params, settings)
    else:
        log.info('unknown action: {}'.format(action))
        xbmcplugin.endOfDirectory(handle)


def _find(handle, params, _settings):
    """Search for matching tracks by filename."""
    title = params.get('title', '')
    artist, track = _parse_title(title)

    if not artist or not track:
        log.debug('find: could not parse artist/track from "{}"'.format(title))
        xbmcplugin.endOfDirectory(handle)
        return

    log.debug('find: artist="{}" track="{}"'.format(artist, track))
    results = audiodb.search_tracks(artist, track)

    # Last.fm autocorrect retry: fixes punctuation/spelling mismatches
    if not results:
        corrected = lastfm.get_track_info(artist, track)
        if corrected:
            c_artist = corrected.get('artist', '')
            c_track = corrected.get('name', '')
            if (c_artist and c_track
                    and (c_artist.lower() != artist.lower()
                         or c_track.lower() != track.lower())):
                log.debug('find: Last.fm corrected to "{}" - "{}"'.format(
                    c_artist, c_track))
                results = audiodb.search_tracks(c_artist, c_track)

    if results:
        for t in results:
            _add_search_result(handle, t)
    else:
        # No AudioDB match — synthetic result so getdetails can still
        # fetch from Last.fm + Wikipedia
        li = xbmcgui.ListItem(
            '{} - {}'.format(artist, track), offscreen=True,
        )
        vtag = li.getVideoInfoTag()
        vtag.setTitle(track)
        vtag.setArtists([artist])
        vtag.setMediaType('musicvideo')
        url = 'lastfm:{}/{}'.format(quote(artist, safe=''), quote(track, safe=''))
        li.setProperty('relevance', '0.3')
        xbmcplugin.addDirectoryItem(
            handle=handle, url=url, listitem=li, isFolder=True,
        )

    xbmcplugin.endOfDirectory(handle)


def _getdetails(handle, params, settings):
    """Fetch full metadata for a selected track."""
    url = params.get('url', '')
    unique_ids = _parse_unique_ids(params)

    track_data = None
    artist_name = ''
    track_name = ''
    track_id = ''
    mbid_artist = ''

    if url.startswith('lastfm:'):
        # Fallback path: no TheAudioDB match
        parts = url[7:].split('/', 1)
        artist_name = unquote(parts[0]) if parts else ''
        track_name = unquote(parts[1]) if len(parts) > 1 else ''
    else:
        # Normal path: TheAudioDB track ID
        track_id = url.split('/')[0] if url else ''
        if not track_id and unique_ids:
            track_id = unique_ids.get('audiodb', '')

        if track_id:
            track_data = audiodb.get_cached_track(track_id)
            if not track_data:
                track_data = audiodb.get_track_by_id(track_id)

        if track_data:
            artist_name = track_data.get('strArtist', '')
            track_name = track_data.get('strTrack', '')
            mbid_artist = track_data.get('strMusicBrainzArtistID', '')

    if not artist_name and not track_name:
        _fail(handle)
        return

    # Parallel fetch: Last.fm + Wikipedia + Fanart.tv + AudioDB artist + album
    lang = settings.get('lang', 'en')
    wiki_lang = settings.get('wiki_lang', 'en')
    album_id = track_data.get('idAlbum', '') if track_data else ''

    lastfm_data = None
    wiki_text = None
    fanarttv_art = {}
    artist_data = None
    album_data = None

    def _fetch_lastfm():
        return lastfm.get_track_info(artist_name, track_name, lang)

    def _fetch_wiki():
        if not settings.get('enable_wiki', True):
            return None
        return wikipedia.get_track_summary(artist_name, track_name, wiki_lang)

    def _fetch_fanarttv():
        if not mbid_artist:
            return {}
        return fanarttv.get_artist_artwork(mbid_artist, settings)

    def _fetch_artist():
        return audiodb.search_artist(artist_name)

    def _fetch_album():
        if not album_id:
            return None
        return audiodb.get_album(album_id)

    with ThreadPoolExecutor(max_workers=5) as executor:
        fut_lastfm = executor.submit(_fetch_lastfm)
        fut_wiki = executor.submit(_fetch_wiki)
        fut_fanarttv = executor.submit(_fetch_fanarttv)
        fut_artist = executor.submit(_fetch_artist)
        fut_album = executor.submit(_fetch_album)

        lastfm_data = _safe_result(fut_lastfm, 'lastfm')
        wiki_text = _safe_result(fut_wiki, 'wiki')
        fanarttv_art = _safe_result(fut_fanarttv, 'fanarttv') or {}
        artist_data = _safe_result(fut_artist, 'artist')
        album_data = _safe_result(fut_album, 'album')

    artist_art = audiodb.get_artist_artwork(artist_data)

    # If we discovered MBID from artist search, retry Fanart.tv
    if not mbid_artist and artist_data:
        mbid_artist = artist_data.get('strMusicBrainzID', '')
        if mbid_artist and not fanarttv_art:
            fanarttv_art = fanarttv.get_artist_artwork(mbid_artist, settings)

    li = xbmcgui.ListItem(track_name, offscreen=True)
    _populate_musicvideo(
        li, track_data, album_data, lastfm_data, wiki_text,
        artist_name, track_name, track_id, mbid_artist,
        settings,
    )
    set_artwork(
        li.getVideoInfoTag(), track_data, artist_art, fanarttv_art,
    )
    xbmcplugin.setResolvedUrl(handle, True, li)


def _getartwork(handle, params, settings):
    """Fetch artwork — delegates to getdetails."""
    _getdetails(handle, params, settings)


def _nfo_url(handle, params):
    """Extract a track ID from an NFO file."""
    nfo = params.get('nfo', '')

    # Complete NFOs have unique IDs — Kodi handles directly
    if '<uniqueid' in nfo:
        xbmcplugin.endOfDirectory(handle)
        return

    track_id = _parse_nfo(nfo)
    if not track_id:
        xbmcplugin.endOfDirectory(handle)
        return

    li = xbmcgui.ListItem(offscreen=True)
    li.getVideoInfoTag().setUniqueIDs({'audiodb': track_id}, 'audiodb')
    xbmcplugin.addDirectoryItem(
        handle=handle, url=track_id, listitem=li, isFolder=True,
    )
    xbmcplugin.endOfDirectory(handle)


def _parse_title(title):
    """Split 'Artist - Track' from a filename."""
    if not title:
        return '', ''

    if '.' in title:
        base, ext = title.rsplit('.', 1)
        if ext.lower() in _VIDEO_EXTENSIONS:
            title = base

    parts = _RE_SEPARATOR.split(title, maxsplit=1)
    if len(parts) < 2:
        return '', title.strip()

    artist = parts[0].strip()
    track = _RE_NOISE.sub('', parts[1]).strip()
    return artist, track


def _add_search_result(handle, track):
    """Add an AudioDB track as a search result."""
    title = track.get('strTrack', '')
    artist = track.get('strArtist', '')
    album = track.get('strAlbum', '')
    track_id = str(track.get('idTrack', ''))

    label = '{} - {}'.format(artist, title)
    if album:
        label = '{} [{}]'.format(label, album)

    li = xbmcgui.ListItem(label, offscreen=True)
    vtag = li.getVideoInfoTag()
    vtag.setTitle(title)
    vtag.setArtists([artist])
    if album:
        vtag.setAlbum(album)
    vtag.setUniqueIDs({'audiodb': track_id}, 'audiodb')
    vtag.setMediaType('musicvideo')

    li.setProperty('relevance', '0.5')
    xbmcplugin.addDirectoryItem(
        handle=handle, url=track_id, listitem=li, isFolder=True,
    )


def _populate_musicvideo(li, track_data, album_data, lastfm_data, wiki_text,
                          artist_name, track_name, track_id, mbid_artist,
                          settings):
    """Set all metadata fields on the listitem."""
    vtag = li.getVideoInfoTag()

    vtag.setTitle(track_name)
    vtag.setMediaType('musicvideo')
    vtag.setArtists([artist_name])

    album = ''
    if track_data:
        album = track_data.get('strAlbum', '')
    if not album and lastfm_data:
        album = lastfm_data.get('album', '')
    if album:
        vtag.setAlbum(album)

    # Plot: Last.fm → Wikipedia → AudioDB
    plot = ''
    if lastfm_data:
        plot = lastfm_data.get('wiki_summary', '')
    if not plot and wiki_text:
        plot = wiki_text
    if not plot and track_data:
        plot = track_data.get('strDescriptionEN') or ''
    if plot:
        vtag.setPlot(plot)

    # Director + Studio (AudioDB only)
    if track_data:
        director = track_data.get('strMusicVidDirector', '')
        if director:
            vtag.setDirectors([d.strip() for d in director.split(',')])
        studio = track_data.get('strMusicVidCompany', '')
        if studio:
            vtag.setStudios([studio])

    # Genre / Tags: Last.fm tags preferred, AudioDB strGenre fallback
    genre_set = False
    if lastfm_data and lastfm_data.get('tags'):
        tags = lastfm_data['tags']
        if tags:
            vtag.setGenres([tags[0]])
            genre_set = True
            if settings.get('lastfm_tags', True):
                vtag.setTags(tags)
    if not genre_set and track_data:
        audiodb_genre = track_data.get('strGenre', '')
        if audiodb_genre:
            vtag.setGenres([audiodb_genre])

    # Year from album release date
    year = 0
    if album_data:
        try:
            year = int(album_data.get('intYearReleased') or 0)
        except (ValueError, TypeError):
            pass
    if 1900 <= year <= 2100:
        vtag.setYear(year)

    # Both APIs return duration in milliseconds
    duration_ms = 0
    if track_data:
        try:
            duration_ms = int(track_data.get('intDuration') or 0)
        except (ValueError, TypeError):
            pass
    if not duration_ms and lastfm_data:
        duration_ms = lastfm_data.get('duration', 0)
    if duration_ms:
        vtag.setDuration(duration_ms // 1000)

    ids = {}
    if track_id:
        ids['audiodb'] = str(track_id)
    if track_data:
        mb_track = track_data.get('strMusicBrainzID', '')
        if mb_track:
            ids['musicbrainz_track'] = mb_track
    if mbid_artist:
        ids['musicbrainz_artist'] = mbid_artist
    if ids:
        default = 'audiodb' if 'audiodb' in ids else next(iter(ids))
        vtag.setUniqueIDs(ids, default)


def _parse_unique_ids(params):
    """Parse the uniqueIDs JSON string from Kodi params."""
    uid_str = params.get('uniqueIDs', '')
    if uid_str:
        try:
            return json.loads(uid_str)
        except (ValueError, TypeError):
            pass
    return {}


def _parse_nfo(nfo):
    """Extract an AudioDB track ID from NFO text."""
    match = _NFO_AUDIODB_URL.search(nfo)
    if match:
        return match.group(1)
    match = _NFO_AUDIODB_ID.search(nfo)
    if match:
        return match.group(1)
    return ''


def _safe_result(future, name):
    """Collect a future's result, logging and swallowing errors."""
    try:
        return future.result()
    except Exception as exc:
        log.error('{} fetch failed: {}'.format(name, exc))
        return None


def _fail(handle):
    """Signal to Kodi that the scrape failed."""
    xbmcplugin.setResolvedUrl(
        handle, False, xbmcgui.ListItem(offscreen=True),
    )

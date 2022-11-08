import re
from collections import namedtuple

import xbmcgui
import xbmcplugin

from .simple_requests import HTTPError
from .tvdb import Request
from .utils import logger

SHOW_ID_FROM_EPISODE_GUIDE_REGEXPS = (
    r'(thetvdb)\.com[\w=&\?/{}\":,]+\"id\":(\d+)',
    r'(thetvdb)\.com/.*?series/(\d+)',
    r'(thetvdb)\.com[\w=&\?/]*[&\?]+id=(\d+)',
)

SHOW_ID_REGEXPS = (
    r'<uniqueid type=\"(tvdb)\".*>(\d+)</uniqueid>',
    r'(thetvdb)\.com/.*?series/([\w\s\d()-]+)',
    r'(thetvdb)\.com[\w=&\?/]*[&\?]+id=(\d+)',
)

SERIES_URL_REGEX = re.compile(r'https?://[w.]*?thetvdb.com/series/([\w-]+)', re.I)
TVDB_ID_REGEX = re.compile(r'<strong>TheTVDB\.com Series ID</strong>\s+?<span>(\d+?)</span>', re.I)

UrlParseResult = namedtuple('UrlParseResult', ['provider', 'show_id'])


def get_show_id_from_nfo(nfo, settings, plugin_handle):
    """
    Get show info by NFO file contents

    This function is called first instead of find_show
    if a NFO file is found in a TV show folder

    :param nfo: the contents of a NFO file
    """
    logger.debug(f'Parsing NFO file:\n{nfo}')
    if '<episodedetails>' in nfo:
        return  # skip episode NFOs
    parse_result = _parse_nfo_url(nfo)
    if parse_result is not None:
        if parse_result.provider in ('tvdb', 'thetvdb'):
            list_item = xbmcgui.ListItem(offscreen=True)
            list_item.setUniqueIDs({'tvdb': parse_result.show_id}, 'tvdb')
            xbmcplugin.addDirectoryItem(
                handle=plugin_handle,
                url=parse_result.show_id,
                listitem=list_item,
                isFolder=True
            )


def parse_episode_guide_url(episode_guide):
    """Extract show ID from episode guide string"""
    for regexp in SHOW_ID_FROM_EPISODE_GUIDE_REGEXPS:
        show_id_match = re.search(regexp, episode_guide, re.I)
        if show_id_match:
            return UrlParseResult(show_id_match.group(1), show_id_match.group(2))
    return None


def _parse_nfo_url(nfo):
    """Extract show ID from NFO file contents"""
    series_url_match = SERIES_URL_REGEX.search(nfo)
    if series_url_match is not None:
        result = _get_tvdb_id_from_slug(series_url_match.group(0))
        if result is not None:
            return result
    for regexp in SHOW_ID_REGEXPS:
        show_id_match = re.search(regexp, nfo, re.I)
        if show_id_match:
            return UrlParseResult(show_id_match.group(1), show_id_match.group(2))
    return None


def _get_tvdb_id_from_slug(series_url):
    try:
        html = Request.make_web_request(series_url)
    except HTTPError as exc:
        logger.error(f'Error {exc.response.status_code} for URL {series_url}')
        return None
    match = TVDB_ID_REGEX.search(html)
    if match is not None:
        return UrlParseResult('thetvdb', match.group(1))
    return None

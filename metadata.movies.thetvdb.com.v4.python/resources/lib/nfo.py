import re

import xbmcgui
import xbmcplugin

from .simple_requests import HTTPError
from .tvdb import Request
from .utils import logger

MOVIE_URL_REGEX = re.compile(r'https?://thetvdb.com/movies/([\w-]+)', re.I)
TVDB_ID_HTML_REGEX = re.compile(r'<strong>TheTVDB\.com Movie ID</strong>\s+?<span>(\d+?)</span>', re.I)
TVDB_ID_XML_REGEX = re.compile(r'<uniqueid type="tvdb"[^>]*?>(\d+?)</uniqueid>', re.I)


def _get_tvdb_id_from_slug(movie_url):
    try:
        html = Request.make_web_request(movie_url)
    except HTTPError as exc:
        logger.error(str(exc))
        return None
    match = TVDB_ID_HTML_REGEX.search(html)
    if match is not None:
        return match.group(1)
    return None


def get_movie_id_from_nfo(nfo, plugin_handle):
    logger.debug(f'Parsing NFO:\n{nfo}')
    movie_url_match = MOVIE_URL_REGEX.search(nfo)
    tvdb_id = None
    if movie_url_match is not None:
        movie_url = movie_url_match.group(0)
        tvdb_id = _get_tvdb_id_from_slug(movie_url)
        logger.debug(f'Movie matched by TheTVDB URL in NFO: {tvdb_id}')
    if tvdb_id is None:
        tvdb_id_xml_match = TVDB_ID_XML_REGEX.search(nfo)
        if tvdb_id_xml_match is not None:
            tvdb_id = tvdb_id_xml_match.group(1)
            logger.debug(f'Movie matched by uniqueid XML tag in NFO: {tvdb_id}')
    if tvdb_id is None:
        logger.debug('Unable to match the movie by NFO')
        return
    list_item = xbmcgui.ListItem(offscreen=True)
    list_item.setUniqueIDs({'tvdb': tvdb_id}, 'tvdb')
    xbmcplugin.addDirectoryItem(
        handle=plugin_handle,
        url=tvdb_id,
        listitem=list_item,
        isFolder=True
    )

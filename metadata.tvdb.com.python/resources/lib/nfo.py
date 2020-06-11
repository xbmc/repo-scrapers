#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import re
from collections import namedtuple

from . import series
from .utils import log

SHOW_ID_FROM_EPISODE_GUIDE_REGEXPS = (
    r'(thetvdb)\.com[\w=&\?/{}\":,]+\"id\":(\d+)',
    r'(thetvdb)\.com/.*?series/(\d+)',
    r'(thetvdb)\.com[\w=&\?/]+id=(\d+)',
)

SHOW_ID_REGEXPS = (
    r'<uniqueid type=\"(tvdb)\".*>(\d+)</uniqueid>',
    r'<uniqueid type=\"(imdb)\".*>(tt\d+)</uniqueid>',
    r'(thetvdb)\.com/.*?series/([\w\s\d()-]+)',
    r'(thetvdb)\.com[\w=&\?/]+id=(\d+)',
    r'(imdb)\.com/[\w/\-]+/(tt\d+)',
)
UrlParseResult = namedtuple('UrlParseResult', ['provider', 'show_id'])


def get_show_id_from_nfo(nfo: bytes, settings):
    """
    Get show info by NFO file contents

    This function is called first instead of find_show
    if a NFO file is found in a TV show folder

    :param nfo: the contents of a NFO file
    """
    if isinstance(nfo, bytes):
        nfo = nfo.decode('utf-8', 'replace')
    log(f'Parsing NFO file:\n{nfo}')
    parse_result = _parse_nfo_url(nfo)
    if parse_result:
        if parse_result.provider == 'tvdb' or parse_result.provider == 'thetvdb':
            if parse_result.show_id.isdigit():
                series.search_series_by_tvdb_id(
                    parse_result.show_id, settings)
            else:  # id seems to be the show name
                series.search_series(
                    parse_result.show_id, settings)

        elif parse_result.provider == 'imdb':
            series.search_series_by_imdb_id(
                parse_result.show_id, settings)


def parse_episode_guide_url(episode_guide):
    """Extract show ID from episode guide string"""
    for regexp in SHOW_ID_FROM_EPISODE_GUIDE_REGEXPS:
        show_id_match = re.search(regexp, episode_guide, re.I)
        if show_id_match:
            return UrlParseResult(show_id_match.group(1), show_id_match.group(2))
    return None


def _parse_nfo_url(nfo):
    """Extract show ID from NFO file contents"""
    for regexp in SHOW_ID_REGEXPS:
        show_id_match = re.search(regexp, nfo, re.I)
        if show_id_match:
            return UrlParseResult(show_id_match.group(1), show_id_match.group(2))
    return None

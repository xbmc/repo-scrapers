# coding: utf-8
#
# Copyright (C) 2019, Roman Miroshnychenko aka Roman V.M. <roman1972@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Functions to interact with TVmaze API"""

from __future__ import absolute_import
from pprint import pformat
from requests.exceptions import HTTPError
from . import cache
from .utils import get_requests_session, get_cache_directory, logger, safe_get
from .data_utils import process_episode_list

SEARCH_URL = 'http://api.tvmaze.com/search/shows'
SEARCH_BU_EXTERNAL_ID_URL = 'http://api.tvmaze.com/lookup/shows'
SHOW_INFO_URL = 'http://api.tvmaze.com/shows/{}'
EPISODE_LIST_URL = 'http://api.tvmaze.com/shows/{}/episodes'
EPISODE_INFO_URL = 'http://api.tvmaze.com/episodes/{}'

SESSION = get_requests_session()
CACHE_DIR = get_cache_directory()


def _load_info(url, params=None):
    """
    Load info from TVmaze

    :param url: API endpoint URL
    :param params: URL query params
    :return: API response
    :raises requests.exceptions.HTTPError: if any error happens
    """
    logger.debug('Calling URL "{}" with params {}'.format(url, params))
    response = SESSION.get(url, params=params)
    if not response.ok:
        response.raise_for_status()
    json_response = response.json()
    logger.debug('TVmaze response:\n{}'.format(pformat(json_response)))
    return json_response


def search_show(title):
    """
    Search a single TV show

    :param title: TV show title to search
    :return: a list with found TV shows
    """
    try:
        return _load_info(SEARCH_URL, {'q': title})
    except HTTPError as exc:
        logger.error('TVmaze returned an error: {}'.format(exc))
        return ()


def filter_by_year(shows, year):
    """
    Filter a show by year

    :param shows: the list of shows from TVmaze
    :param year: premiere year
    :return: a found show or None
    """
    for show in shows:
        premiered = safe_get(show['show'], 'premiered', '')
        if premiered and premiered.startswith(str(year)):
            return show
    return None


def load_episode_list(show_id):
    """Load episode list from TVmaze API"""
    episode_list_url = EPISODE_LIST_URL.format(show_id)
    try:
        return _load_info(episode_list_url, {'specials': '1'})
    except HTTPError as exc:
        logger.error('TVmaze returned an error: {}'.format(exc))
        return ()


def load_show_info(show_id):
    """
    Get full info for a single show

    :param show_id: TVmaze show ID
    :return: show info or None
    """
    show_info = cache.load_show_info_from_cache(show_id)
    if show_info is None:
        show_info_url = SHOW_INFO_URL.format(show_id)
        params = {'embed[]': ['cast', 'seasons', 'images', 'crew']}
        try:
            show_info = _load_info(show_info_url, params)
        except HTTPError as exc:
            logger.error('TVmaze returned an error: {}'.format(exc))
            return None
        episode_list = load_episode_list(show_id)
        if isinstance(show_info['_embedded']['images'], list):
            show_info['_embedded']['images'].sort(key=lambda img: img['main'],
                                                  reverse=True)
        process_episode_list(show_info, episode_list)
        cache.cache_show_info(show_info)
    return show_info


def load_show_info_by_external_id(provider, show_id):
    """
    Load show info by external ID (TheTVDB or IMDB)

    :param provider: 'imdb' or 'thetvdb'
    :param show_id: show ID in the respective provider
    :return: show info or None
    """
    query = {provider: show_id}
    try:
        return _load_info(SEARCH_BU_EXTERNAL_ID_URL, query)
    except HTTPError as exc:
        logger.error('TVmaze returned an error: {}'.format(exc))
        return None


def load_episode_info(show_id, episode_id):
    """
    Load episode info

    :param show_id:
    :param episode_id:
    :return: episode info or None
    """
    show_info = load_show_info(show_id)
    if show_info is not None:
        try:
            episode_info = show_info['episodes'][int(episode_id)]
        except KeyError:
            url = EPISODE_INFO_URL.format(episode_id)
            try:
                episode_info = _load_info(url)
            except HTTPError as exc:
                logger.error('TVmaze returned an error: {}'.format(exc))
                return None
        return episode_info
    return None

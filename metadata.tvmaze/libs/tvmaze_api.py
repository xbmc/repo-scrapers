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

import logging
from pprint import pformat
from typing import Text, Optional, Union, List, Dict, Any

import simple_requests as requests

from . import cache_service as cache
from .imdb_rating import get_imdb_rating

InfoType = Dict[str, Any]  # pylint: disable=invalid-name

SEARCH_URL = 'http://api.tvmaze.com/search/shows'
SEARCH_BY_EXTERNAL_ID_URL = 'http://api.tvmaze.com/lookup/shows'
SHOW_INFO_URL = 'http://api.tvmaze.com/shows/{}'
EPISODE_LIST_URL = 'http://api.tvmaze.com/shows/{}/episodes'
EPISODE_INFO_URL = 'http://api.tvmaze.com/episodes/{}'
ALTERNATE_LISTS_URL = 'http://api.tvmaze.com/shows/{}/alternatelists'
ALTERNATE_EPISODES_URL = 'http://api.tvmaze.com/alternatelists/{}/alternateepisodes'

HEADERS = (
    ('User-Agent', 'Kodi scraper for tvmaze.com by Roman V.M.'),
    ('Accept', 'application/json'),
)


def _load_info(url: str,
               params: Optional[Dict[Text, Union[Text, List[Text]]]] = None) -> Union[dict, list]:
    """
    Load info from TVmaze

    :param url: API endpoint URL
    :param params: URL query params
    :return: API response
    :raises requests.exceptions.HTTPError: if any error happens
    """
    logging.debug('Calling URL "%s" with params %s', url, params)
    response = requests.get(url, params=params, headers=dict(HEADERS))
    if not response.ok:
        response.raise_for_status()
    json_response = response.json()
    logging.debug('TVmaze response:\n%s', pformat(json_response))
    return json_response


def search_show(title: str) -> List[InfoType]:
    """
    Search a single TV show

    :param title: TV show title to search
    :return: a list with found TV shows
    """
    try:
        return _load_info(SEARCH_URL, {'q': title})
    except requests.HTTPError as exc:
        logging.error('TVmaze returned an error: %s', exc)
        return []


def load_show_info(show_id: str) -> Optional[InfoType]:
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
        except requests.HTTPError as exc:
            logging.error('TVmaze returned an error: %s', exc)
            return None
        if isinstance(show_info['_embedded']['images'], list):
            show_info['_embedded']['images'].sort(key=lambda img: img['main'],
                                                  reverse=True)
        external_ids = show_info.get('externals') or {}
        imdb_id = external_ids.get('imdb')
        if imdb_id is not None:
            show_info['imdb_rating'] = get_imdb_rating(imdb_id)
        else:
            show_info['imdb_rating'] = None
        cache.cache_show_info(show_info)
    return show_info


def load_show_info_by_external_id(provider: str, show_id: str) -> Optional[InfoType]:
    """
    Load show info by external ID (TheTVDB or IMDB)

    :param provider: 'imdb' or 'thetvdb'
    :param show_id: show ID in the respective provider
    :return: show info or None
    """
    query = {provider: show_id}
    try:
        return _load_info(SEARCH_BY_EXTERNAL_ID_URL, query)
    except requests.HTTPError as exc:
        logging.error('TVmaze returned an error: %s', exc)
        return None


def _get_alternate_episode_list_id(show_id: str, episode_order: str) -> Optional[int]:
    alternate_order_id = None
    url = ALTERNATE_LISTS_URL.format(show_id)
    try:
        alternate_lists = _load_info(url)
    except requests.HTTPError as exc:
        logging.error('TVmaze returned an error: %s', exc)
    else:
        for episode_list in alternate_lists:
            if episode_list.get(episode_order):
                alternate_order_id = episode_list['id']
                break
    return alternate_order_id


def load_alternate_episode_list(show_id: str, episode_order: str) -> Optional[List[InfoType]]:
    alternate_episodes = None
    alternate_order_id = _get_alternate_episode_list_id(show_id, episode_order)
    if alternate_order_id is not None:
        url = ALTERNATE_EPISODES_URL.format(alternate_order_id)
        try:
            raw_alternate_episodes = _load_info(url, {'embed': 'episodes'})
        except requests.HTTPError as exc:
            logging.error('TVmaze returned an error: %s', exc)
        else:
            alternate_episodes = []
            for episode in raw_alternate_episodes:
                episode_info = episode['_embedded']['episodes'][0]
                episode_info['season'] = episode['season']
                episode_info['number'] = episode['number']
                alternate_episodes.append(episode_info)
    if alternate_episodes:
        alternate_episodes.sort(key=lambda ep: (ep['season'], ep['number']))
    return alternate_episodes


def load_episode_list(show_id: str, episode_order: str) -> Optional[List[InfoType]]:
    """Load episode list from TVmaze API"""
    episode_list = None
    if episode_order != 'default':
        episode_list = load_alternate_episode_list(show_id, episode_order)
    if not episode_list:
        episode_list_url = EPISODE_LIST_URL.format(show_id)
        try:
            episode_list = _load_info(episode_list_url, {'specials': '1'})
        except requests.HTTPError as exc:
            logging.error('TVmaze returned an error: %s', exc)
    return episode_list


def load_episode_info(episode_id: Union[str, int]) -> Optional[InfoType]:
    url = EPISODE_INFO_URL.format(episode_id)
    try:
        return _load_info(url)
    except requests.HTTPError as exc:
        logging.error('TVmaze returned an error: %s', exc)
        return None

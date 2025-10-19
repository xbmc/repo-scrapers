# Copyright (C) 2019, Roman Miroshnychenko aka Roman V.M.
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

"""Functions to process data"""
import json
import logging
import re
from collections import defaultdict
from typing import Optional, Dict, List, Any, Sequence, NamedTuple
from xml.etree import ElementTree as Etree

from xbmcgui import ListItem

from . import tvmaze_api, cache_service as cache
from .info_tag_property_setters import (
    BASIC_SHOW_MEDIA_PROPERTY_SETTERS,
    SHOW_MEDIA_PROPERTY_SETTERS,
    BASIC_EPISODE_MEDIA_PROPERTY_SETTERS,
    EPISODE_MEDIA_PROPERTY_SETTERS,
    extract_artwork_url,
)
from .kodi_utils import ADDON, Settings

InfoType = Dict[str, Any]  # pylint: disable=invalid-name

SHOW_ID_REGEXPS = (
    r'(tvmaze)\.com/shows/(\d+)/[\w\-]',
    r'(thetvdb)\.com/.*?series/(\d+)',
    r'(thetvdb)\.com[\w=&\?/]+id=(\d+)',
    r'(imdb)\.com/[\w/\-]+/(tt\d+)',
)
SUPPORTED_ARTWORK_TYPES = ('poster', 'banner')
MAX_ARTWORK_NUMBER = 10

SUPPORTED_EXTERNAL_IDS = ('tvdb', 'thetvdb', 'imdb')

EPISODE_ORDER_MAP = {
    0: 'default',
    1: 'dvd_release',
    2: 'verbatim_order',
    3: 'country_premiere',
    4: 'streaming_premiere',
    5: 'broadcast_premiere',
    6: 'language_premiere',
}


class ShowIdInfo(NamedTuple):
    provider: str
    show_id: str


class XmlParseResult(NamedTuple):
    title: str
    year: str
    uniqueids: Dict[str, str]


def _filter_by_year(shows: List[InfoType], year: str) -> Optional[InfoType]:
    """
    Filter a show by year

    :param shows: the list of shows from TVmaze
    :param year: premiere year
    :return: a found show or None
    """
    for show in shows:
        premiered = show.get('premiered') or ''
        if premiered and premiered.startswith(str(year)):
            return show
    return None


def search_show(title: str, year: str) -> Sequence[InfoType]:
    logging.debug('Searching for TV show %s (%s)', title, year)
    raw_search_results = tvmaze_api.search_show(title)
    search_results = [res['show'] for res in raw_search_results]
    if len(search_results) > 1 and year:
        search_result = _filter_by_year(search_results, year)
        if search_results is not None:
            return (search_result,)
    return search_results


def add_basic_show_info(list_item: ListItem, show_info: InfoType) -> None:
    info_tag = list_item.getVideoInfoTag()
    for info_tag_method, setter_class, tvmaze_property in BASIC_SHOW_MEDIA_PROPERTY_SETTERS:
        setter = setter_class(show_info, info_tag_method, tvmaze_property)
        if setter.should_set():
            setter.set_info_tag_property(info_tag)


def _get_show_id_from_url(nfo: str) -> Optional[ShowIdInfo]:
    """Extract show ID from NFO file contents"""
    for regexp in SHOW_ID_REGEXPS:
        show_id_match = re.search(regexp, nfo, re.I)
        if show_id_match is not None:
            provider = show_id_match.group(1)
            show_id = show_id_match.group(2)
            logging.debug('Matched show ID %s by regexp "%s"', show_id, regexp)
            return ShowIdInfo(provider, show_id)
    logging.debug('Unable to find show ID in an NFO file')
    return None


def get_tvmaze_show_id_from_url_nfo(nfo: str) -> Optional[int]:
    show_id_info = _get_show_id_from_url(nfo)
    if show_id_info is None:
        return None
    if show_id_info.provider == 'tvmaze':
        return int(show_id_info.show_id)
    show_info = tvmaze_api.load_show_info_by_external_id(
        show_id_info.provider,
        show_id_info.show_id
    )
    if show_info is not None:
        return show_info.get('id')
    return None


def _parse_xml_nfo_contents(nfo: str) -> XmlParseResult:
    root = Etree.fromstring(nfo)
    title = ''
    title_tag = root.find('title')
    if title_tag is not None:
        title = title_tag.text
    year = ''
    year_tag = root.find('year')
    if year_tag is not None:
        year = year_tag.text
    if not year:
        premiered_tag = root.find('premiered')
        if premiered_tag is not None:
            year = premiered_tag.text[:4]
    uniqueids = {}
    for uniqueid_tag in root.findall('uniqueid'):
        provider = uniqueid_tag.attrib.get('type')
        if provider is not None:
            if provider == 'tvdb':
                provider = 'thetvdb'
            uniqueids[provider] = uniqueid_tag.text
    return XmlParseResult(title, year, uniqueids)


def get_tvmaze_show_id_from_xml_nfo(nfo: str) -> Optional[int]:
    xml_parse_result = _parse_xml_nfo_contents(nfo)
    if 'tvmaze' in xml_parse_result.uniqueids:
        return int(xml_parse_result.uniqueids['tvmaze'])
    if 'imdb' in xml_parse_result.uniqueids:
        show_info = tvmaze_api.load_show_info_by_external_id(
            'imdb',
            xml_parse_result.uniqueids['imdb']
        )
        if show_info:
            return show_info['id']
    if 'thetvdb' in xml_parse_result.uniqueids:
        show_info = tvmaze_api.load_show_info_by_external_id(
            'thetvdb',
            xml_parse_result.uniqueids['thetvdb']
        )
        if show_info:
            return show_info['id']
    if xml_parse_result.title:
        search_results = search_show(xml_parse_result.title, xml_parse_result.year)
        if search_results and len(search_results) == 1:
            return search_results[0]['id']
    return None


def get_tvmaze_episode_id_from_xml_nfo(nfo: str) -> Optional[int]:
    parse_result = _parse_xml_nfo_contents(nfo)
    if 'tvmaze' in parse_result.uniqueids:
        return int(parse_result.uniqueids['tvmaze'])
    return None


def _process_episode_list(episode_list: List[InfoType]) -> Dict[str, InfoType]:
    """Convert embedded episode list to a dict"""
    processed_episodes = {}
    specials_list = []
    for episode in episode_list:
        # xbmc/video/VideoInfoScanner.cpp ~ line 1010
        # "episode 0 with non-zero season is valid! (e.g. prequel episode)"
        if episode['number'] is not None or episode.get('type') == 'significant_special':
            # In some orders episodes with the same ID may occur more than once,
            # so we need a unique key.
            key = f'{episode["id"]}_{episode["season"]}_{episode["number"]}'
            processed_episodes[key] = episode
        else:
            specials_list.append(episode)
    specials_list.sort(key=lambda ep: ep['airdate'])
    for ep_number, special in enumerate(specials_list, 1):
        special['season'] = 0
        special['number'] = ep_number
        key = f'{special["id"]}_{special["season"]}_{special["number"]}'
        processed_episodes[key] = special
    return processed_episodes


def get_episodes_map(show_id: str, episode_order: str) -> Optional[Dict[str, InfoType]]:
    processed_episodes = cache.load_episodes_map_from_cache(show_id)
    if not processed_episodes:
        episode_list = tvmaze_api.load_episode_list(show_id, episode_order)
        if episode_list:
            processed_episodes = _process_episode_list(episode_list)
            cache.cache_episodes_map(show_id, processed_episodes)
    return processed_episodes or {}


def get_episode_info(show_id: str,
                     episode_id: str,
                     season: str,
                     episode: str,
                     episode_order: str) -> Optional[InfoType]:
    """
    Load episode info

    :param show_id:
    :param episode_id:
    :param season:
    :param episode:
    :param episode_order:
    :return: episode info or None
    """
    episode_info = None
    episodes_map = get_episodes_map(show_id, episode_order)
    if episodes_map is not None:
        try:
            key = f'{episode_id}_{season}_{episode}'
            episode_info = episodes_map[key]
        except KeyError as exc:
            logging.error('Unable to retrieve episode info: %s', exc)
    if episode_info is None:
        episode_info = tvmaze_api.load_episode_info(episode_id)
    return episode_info


def add_full_show_info(list_item: ListItem, show_info: InfoType) -> None:
    """Add main show info to a list item"""
    info_tag = list_item.getVideoInfoTag()
    for info_tag_method, setter_class, tvmaze_property in SHOW_MEDIA_PROPERTY_SETTERS:
        setter = setter_class(show_info, info_tag_method, tvmaze_property)
        if setter.should_set():
            setter.set_info_tag_property(info_tag)
    set_show_artwork(show_info, list_item)


def add_basic_episode_info(list_item: ListItem, episode_info: InfoType) -> None:
    """Add basic episode info to a list item"""
    info_tag = list_item.getVideoInfoTag()
    for info_tag_method, setter_class, tvmaze_property in BASIC_EPISODE_MEDIA_PROPERTY_SETTERS:
        setter = setter_class(episode_info, info_tag_method, tvmaze_property)
        if setter.should_set():
            setter.set_info_tag_property(info_tag)


def add_full_episode_info(list_item: ListItem, episode_info: InfoType) -> None:
    """Add episode info to a list item"""
    info_tag = list_item.getVideoInfoTag()
    for info_tag_method, setter_class, tvmaze_property in EPISODE_MEDIA_PROPERTY_SETTERS:
        setter = setter_class(episode_info, info_tag_method, tvmaze_property)
        if setter.should_set():
            setter.set_info_tag_property(info_tag)


def get_tvmaze_show_id_from_json_episodeguide(episodeguide: str) -> Optional[str]:
    try:
        uniqueids = json.loads(episodeguide)
    except ValueError:
        return None
    show_id = uniqueids.get('tvmaze')
    if show_id is not None:
        return show_id
    for external_id_type in SUPPORTED_EXTERNAL_IDS:
        external_id = uniqueids.get(external_id_type)
        if external_id is None:
            continue
        if external_id == 'tvdb':
            external_id = 'thetvdb'
        show_info = tvmaze_api.load_show_info_by_external_id(external_id_type, external_id)
        if show_info:
            return str(show_info['id'])
    return None


def get_tvmaze_show_id_from_url_episodeguide(episodeguide: str) -> Optional[str]:
    show_id = None
    show_id_info = _get_show_id_from_url(episodeguide)
    if show_id_info is None:
        return None
    if show_id_info.provider == 'tvmaze':
        show_info = tvmaze_api.load_show_info(show_id_info.show_id)
    else:
        show_info = tvmaze_api.load_show_info_by_external_id(
            show_id_info.provider,
            show_id_info.show_id
        )
    if show_info:
        show_id = str(show_info['id'])
    return show_id


def _extract_artwork(show_info: InfoType) -> Dict[str, List[Dict[str, Any]]]:
    artwork = defaultdict(list)
    poster_info = show_info.get('image') or {}
    if poster_info:
        artwork['poster'].append({'resolutions': poster_info})
    for item in show_info['_embedded']['images']:
        artwork[item['type']].append(item)
    return artwork


def set_show_artwork(show_info: InfoType, list_item: ListItem) -> None:
    """Set available images for a show"""
    info_tag = list_item.getVideoInfoTag()
    fanart_list = []
    artwork = _extract_artwork(show_info)
    for artwork_type, artwork_list in artwork.items():
        for item in artwork_list[:MAX_ARTWORK_NUMBER]:
            resolutions = item.get('resolutions') or {}
            url = extract_artwork_url(resolutions)
            if artwork_type in SUPPORTED_ARTWORK_TYPES and url:
                info_tag.addAvailableArtwork(url, artwork_type)
            elif artwork_type == 'background' and url:
                fanart_list.append({'image': url})
    if fanart_list:
        set_available_fanart_method = getattr(info_tag, 'setAvailableFanart', None)
        if set_available_fanart_method is None:
            set_available_fanart_method = list_item.setAvailableFanart
        set_available_fanart_method(fanart_list)


def get_episode_order() -> str:
    episode_order_enum = Settings().get_value_int('episode_order')
    episode_order = EPISODE_ORDER_MAP.get(episode_order_enum, 'default')
    return episode_order

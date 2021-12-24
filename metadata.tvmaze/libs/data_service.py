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

"""Functions to process data"""

from __future__ import absolute_import, unicode_literals

import re
from collections import namedtuple, defaultdict

import six

from . import tvmaze_api, cache_service as cache
from .utils import logger

try:
    from typing import Optional, Text, Dict, List, Any, Tuple  # pylint: disable=unused-import
    from xbmcgui import ListItem  # pylint: disable=unused-import
    InfoType = Dict[Text, Any]  # pylint: disable=invalid-name
except ImportError:
    pass

TAG_RE = re.compile(r'<[^>]+>')
SHOW_ID_REGEXPS = (
    re.compile(r'(tvmaze)\.com/shows/(\d+)/[\w\-]', re.I),
    re.compile(r'(thetvdb)\.com/.*?series/(\d+)', re.I),
    re.compile(r'(thetvdb)\.com[\w=&\?/]+id=(\d+)', re.I),
    re.compile(r'(imdb)\.com/[\w/\-]+/(tt\d+)', re.I),
    re.compile(r'<uniqueid.+?type="(tvdb|imdb)".*?>([t\d]+?)</uniqueid>', re.I | re.DOTALL),
)
TITLE_RE = re.compile(r'<title>([^<]+?)</title>', re.I)
YEAR_RE = re.compile(r'<year>(\d+?)</year>', re.I)
PREMIERED_RE = re.compile(r'<premiered>([^<]+?)</premiered>', re.I)
SUPPORTED_ARTWORK_TYPES = ('poster', 'banner')
IMAGE_SIZES = ('large', 'original', 'medium')
MAX_ARTWORK_NUMBER = 10
CLEAN_PLOT_REPLACEMENTS = (
    ('<b>', '[B]'),
    ('</b>', '[/B]'),
    ('<i>', '[I]'),
    ('</i>', '[/I]'),
    ('</p><p>', '[CR]'),
)

UrlParseResult = namedtuple('UrlParseResult', ['provider', 'show_id'])


def _process_episode_list(episode_list):
    # type: (List[InfoType]) -> Dict[Text, InfoType]
    """Convert embedded episode list to a dict"""
    processed_episodes = {}
    specials_list = []
    for episode in episode_list:
        # xbmc/video/VideoInfoScanner.cpp ~ line 1010
        # "episode 0 with non-zero season is valid! (e.g. prequel episode)"
        if episode['number'] is not None or episode.get('type') == 'significant_special':
            # In some orders episodes with the same ID may occur more than once,
            # so we need a unique key.
            key = '{}_{}_{}'.format(episode['id'], episode['season'], episode['number'])
            processed_episodes[key] = episode
        else:
            specials_list.append(episode)
    specials_list.sort(key=lambda ep: ep['airdate'])
    for ep_number, special in enumerate(specials_list, 1):
        special['season'] = 0
        special['number'] = ep_number
        key = '{}_{}_{}'.format(special['id'], special['season'], special['number'])
        processed_episodes[key] = special
    return processed_episodes


def get_episodes_map(show_id, episode_order):
    # type: (Text, Text) -> Optional[Dict[Text, InfoType]]
    processed_episodes = cache.load_episodes_map_from_cache(show_id)
    if not processed_episodes:
        episode_list = tvmaze_api.load_episode_list(show_id, episode_order)
        if episode_list:
            processed_episodes = _process_episode_list(episode_list)
            cache.cache_episodes_map(show_id, processed_episodes)
    return processed_episodes or {}


def get_episode_info(show_id, episode_id, season, episode, episode_order):
    # type: (Text, Text, Text, Text, Text) -> Optional[InfoType]
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
            key = '{}_{}_{}'.format(episode_id, season, episode)
            episode_info = episodes_map[key]
        except KeyError as exc:
            logger.error('Unable to retrieve episode info: {}'.format(exc))
    if episode_info is None:
        episode_info = tvmaze_api.load_episode_info(episode_id)
    return episode_info


def _clean_plot(plot):
    # type: (Text) -> Text
    """Replace HTML tags with Kodi skin tags"""
    for repl in CLEAN_PLOT_REPLACEMENTS:
        plot = plot.replace(repl[0], repl[1])
    plot = TAG_RE.sub('', plot)
    return plot


def _set_cast(show_info, list_item):
    # type: (InfoType, ListItem) -> ListItem
    """Extract cast from show info dict"""
    cast = []
    for index, item in enumerate(show_info['_embedded']['cast'], 1):
        data = {
            'name': item['person']['name'],
            'role': item['character']['name'],
            'order': index,
        }
        thumb = None
        if item['character'].get('image') is not None:
            thumb = _extract_artwork_url(item['character']['image'])
        if not thumb and item['person'].get('image') is not None:
            thumb = _extract_artwork_url(item['person']['image'])
        if thumb:
            data['thumbnail'] = thumb
        cast.append(data)
    list_item.setCast(cast)
    return list_item


def _get_credits(show_info):
    # type: (InfoType) -> List[Text]
    """Extract show creator(s) from show info"""
    credits_ = []
    for item in show_info['_embedded']['crew']:
        if item['type'].lower() == 'creator':
            credits_.append(item['person']['name'])
    return credits_


def _set_unique_ids(show_info, list_item):
    # type: (InfoType, ListItem) -> ListItem
    """Extract unique ID in various online databases"""
    unique_ids = {'tvmaze': str(show_info['id'])}
    for key, value in six.iteritems(show_info.get('externals') or {}):
        if key == 'thetvdb':
            key = 'tvdb'
        unique_ids[key] = str(value)
    list_item.setUniqueIDs(unique_ids, 'tvmaze')
    return list_item


def _set_rating(show_info, list_item, default_rating):
    # type: (InfoType, ListItem, Text) -> ListItem
    """Set show rating"""
    imdb_rating = show_info.get('imdb_rating')
    is_imdb_default = default_rating == 'IMDB' and imdb_rating is not None
    if show_info['rating'] is not None and show_info['rating']['average'] is not None:
        rating = float(show_info['rating']['average'])
        list_item.setRating('tvmaze', rating, defaultt=not is_imdb_default)
    if imdb_rating is not None:
        list_item.setRating('imdb', imdb_rating['rating'], imdb_rating['votes'],
                            defaultt=is_imdb_default)
    return list_item


def _extract_artwork_url(resolutions):
    # type: (Dict[Text, Text]) -> Text
    """Extract image URL from the list of available resolutions"""
    url = ''
    for image_size in IMAGE_SIZES:
        url = resolutions.get(image_size) or ''
        if not isinstance(url, six.text_type):
            url = url.get('url') or ''
            if url:
                break
    return url


def _add_season_info(show_info, list_item):
    # type: (InfoType, ListItem) -> ListItem
    """Add info for show seasons"""
    for season in show_info['_embedded']['seasons']:
        list_item.addSeason(season['number'], season.get('name') or '')
        image = season.get('image')
        if image is not None:
            url = _extract_artwork_url(image)
            if url:
                list_item.addAvailableArtwork(url, 'poster', season=season['number'])
    return list_item


def _extract_artwork(show_info):
    # type: (InfoType) -> Dict[Text, List[Dict[Text, Any]]]
    artwork = defaultdict(list)
    for item in show_info['_embedded']['images']:
        artwork[item['type']].append(item)
    return artwork


def set_show_artwork(show_info, list_item):
    # type: (InfoType, ListItem) -> ListItem
    """Set available images for a show"""
    fanart_list = []
    artwork = _extract_artwork(show_info)
    for artwork_type, artwork_list in six.iteritems(artwork):
        artwork_list.sort(key=lambda art: art.get('main'), reverse=True)
        for item in artwork_list[:MAX_ARTWORK_NUMBER]:
            resolutions = item.get('resolutions') or {}
            url = _extract_artwork_url(resolutions)
            if artwork_type in SUPPORTED_ARTWORK_TYPES and url:
                list_item.addAvailableArtwork(url, artwork_type)
            elif artwork_type == 'background' and url:
                fanart_list.append({'image': url})
    if fanart_list:
        list_item.setAvailableFanart(fanart_list)
    return list_item


def add_main_show_info(list_item, show_info, full_info=True, default_rating='TVmaze'):
    # type: (ListItem, InfoType, bool, Text) -> ListItem
    """Add main show info to a list item"""
    plot = _clean_plot(show_info.get('summary') or '')
    video = {
        'plot': plot,
        'plotoutline': plot,
        'genre': show_info.get('genres') or '',
        'title': show_info['name'],
        'tvshowtitle': show_info['name'],
        'status': show_info.get('status') or '',
        'mediatype': 'tvshow',
        # This property is passed as "url" parameter to getepisodelist call
        'episodeguide': str(show_info['id']),
    }
    if show_info['network'] is not None:
        video['studio'] = show_info['network']['name']
        video['country'] = show_info['network']['country']['name']
    elif show_info['webChannel'] is not None:
        video['studio'] = show_info['webChannel']['name']
        # Global Web Channels do not have a country specified
        if show_info['webChannel']['country'] is not None:
            video['country'] = show_info['webChannel']['country']['name']
    if show_info['premiered'] is not None:
        video['year'] = int(show_info['premiered'][:4])
        video['premiered'] = show_info['premiered']
    if full_info:
        video['credits'] = _get_credits(show_info)
        list_item = set_show_artwork(show_info, list_item)
        list_item = _add_season_info(show_info, list_item)
        list_item = _set_cast(show_info, list_item)
    else:
        image = show_info.get('image') or {}
        image_url = _extract_artwork_url(image)
        if image_url:
            list_item.addAvailableArtwork(image_url, 'poster')
    list_item.setInfo('video', video)
    list_item = _set_rating(show_info, list_item, default_rating)
    # This is needed for getting artwork
    list_item = _set_unique_ids(show_info, list_item)
    return list_item


def add_episode_info(list_item, episode_info, full_info=True):
    # type: (ListItem, InfoType, bool) -> ListItem
    """Add episode info to a list item"""
    video = {
        'title': episode_info['name'],
        'season': episode_info['season'],
        'episode': episode_info['number'],
        'mediatype': 'episode',
    }
    if episode_info['airdate'] is not None:
        video['aired'] = episode_info['airdate']
    if full_info:
        summary = episode_info.get('summary')
        if summary is not None:
            video['plot'] = video['plotoutline'] = _clean_plot(summary)
        if episode_info['runtime'] is not None:
            video['duration'] = episode_info['runtime'] * 60
        if episode_info['airdate'] is not None:
            video['premiered'] = episode_info['airdate']
    list_item.setInfo('video', video)
    image = episode_info.get('image') or {}
    image_url = _extract_artwork_url(image)
    if image_url:
        list_item.addAvailableArtwork(image_url, 'thumb')
    list_item.setUniqueIDs({'tvmaze': str(episode_info['id'])}, 'tvmaze')
    return list_item


def parse_nfo_url(nfo):
    # type: (Text) -> Optional[UrlParseResult]
    """Extract show ID from NFO file contents"""
    for regexp in SHOW_ID_REGEXPS:
        show_id_match = regexp.search(nfo)
        if show_id_match is not None:
            provider = show_id_match.group(1)
            show_id = show_id_match.group(2)
            if provider == 'tvdb':
                provider = 'thetvdb'
            logger.debug('Matched show ID {} by regexp {}'.format(show_id, regexp))
            return UrlParseResult(provider, show_id)
    logger.debug('Unable to find show ID in an NFO file')
    return None


def parse_nfo_title_and_year(nfo):
    # type: (Text) -> [Optional[Text], Optional[Text]]
    title_match = TITLE_RE.search(nfo)
    if title_match is None:
        logger.debug('Unable to find show title in an NFO file')
        return None, None
    title = title_match.group(1)
    year = None
    year_match = YEAR_RE.search(nfo)
    if year_match is not None:
        year = year_match.group(1)
    if year is None:
        premiered_match = PREMIERED_RE.search(nfo)
        if premiered_match is not None:
            premiered = premiered_match.group(1)
            year = premiered[:4]
    logger.debug('Matched title "{}" and year {}'.format(title, year))
    return title, year


def _filter_by_year(shows, year):
    # type: (List[InfoType], Text) -> Optional[InfoType]
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


def search_show(title, year):
    # type: (Text, Text) -> List[InfoType]
    logger.debug('Searching for TV show {} ({})'.format(title, year))
    raw_search_results = tvmaze_api.search_show(title)
    search_results = [res['show'] for res in raw_search_results]
    if len(search_results) > 1 and year:
        search_result = _filter_by_year(search_results, year)
        search_results = (search_result,) if search_result else ()
    return search_results

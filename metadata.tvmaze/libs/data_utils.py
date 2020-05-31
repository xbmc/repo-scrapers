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

from __future__ import absolute_import

import re
from collections import OrderedDict, namedtuple

import six

from .utils import safe_get

try:
    from typing import Optional, Text, Dict, List, Any  # pylint: disable=unused-import
    from xbmcgui import ListItem  # pylint: disable=unused-import
    InfoType = Dict[Text, Any]  # pylint: disable=invalid-name
except ImportError:
    pass

TAG_RE = re.compile(r'<[^>]+>')
SHOW_ID_REGEXPS = (
    r'(tvmaze)\.com/shows/(\d+)/[\w\-]',
    r'(thetvdb)\.com/.*?series/(\d+)',
    r'(thetvdb)\.com[\w=&\?/]+id=(\d+)',
    r'(imdb)\.com/[\w/\-]+/(tt\d+)',
)
SUPPORTED_ARTWORK_TYPES = {'poster', 'banner'}
IMAGE_SIZES = ('large', 'original', 'medium')
CLEAN_PLOT_REPLACEMENTS = (
    ('<b>', '[B]'),
    ('</b>', '[/B]'),
    ('<i>', '[I]'),
    ('</i>', '[/I]'),
    ('</p><p>', '[CR]'),
)

UrlParseResult = namedtuple('UrlParseResult', ['provider', 'show_id'])


def process_episode_list(show_info, episode_list):
    # type: (InfoType, List[InfoType]) -> None
    """Convert embedded episode list to a dict"""
    episodes = OrderedDict()
    specials_list = []
    for episode in episode_list:
        if episode['number']:
            episodes[episode['id']] = episode
        else:
            specials_list.append(episode)
    specials_list.sort(key=lambda ep: ep['airdate'])
    for ep_number, special in enumerate(specials_list, 1):
        special['season'] = 0
        special['number'] = ep_number
        episodes[special['id']] = special
    show_info['episodes'] = episodes


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
        if safe_get(item['character'], 'image') is not None:
            thumb = _extract_artwork_url(item['character']['image'])
        if not thumb and safe_get(item['person'], 'image') is not None:
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
    for key, value in six.iteritems(safe_get(show_info, 'externals', {})):
        if key == 'thetvdb':
            key = key[3:]
        unique_ids[key] = str(value)
    list_item.setUniqueIDs(unique_ids, 'tvmaze')
    return list_item


def _set_rating(show_info, list_item):
    # type: (InfoType, ListItem) -> ListItem
    """Set show rating"""
    if show_info['rating'] is not None and show_info['rating']['average'] is not None:
        rating = float(show_info['rating']['average'])
        list_item.setRating('tvmaze', rating, defaultt=True)
    return list_item


def _extract_artwork_url(resolutions):
    # type: (Dict[Text, Text]) -> Text
    """Extract image URL from the list of available resolutions"""
    url = ''
    for image_size in IMAGE_SIZES:
        url = safe_get(resolutions, image_size, '')
        if not isinstance(url, six.text_type):
            url = safe_get(url, 'url', '')
            if url:
                break
    return url


def _add_season_info(show_info, list_item):
    # type: (InfoType, ListItem) -> ListItem
    """Add info for show seasons"""
    for season in show_info['_embedded']['seasons']:
        list_item.addSeason(season['number'], safe_get(season, 'name', ''))
        image = safe_get(season, 'image')
        if image is not None:
            url = _extract_artwork_url(image)
            if url:
                list_item.addAvailableArtwork(url, 'poster', season=season['number'])
    return list_item


def set_show_artwork(show_info, list_item):
    # type: (InfoType, ListItem) -> ListItem
    """Set available images for a show"""
    fanart_list = []
    for item in show_info['_embedded']['images']:
        resolutions = safe_get(item, 'resolutions', {})
        url = _extract_artwork_url(resolutions)
        if item['type'] in SUPPORTED_ARTWORK_TYPES and url:
            list_item.addAvailableArtwork(url, item['type'])
        elif item['type'] == 'background' and url:
            fanart_list.append({'image': url})
    if fanart_list:
        list_item.setAvailableFanart(fanart_list)
    return list_item


def add_main_show_info(list_item, show_info, full_info=True):
    # type: (ListItem, InfoType, bool) -> ListItem
    """Add main show info to a list item"""
    plot = _clean_plot(safe_get(show_info, 'summary', ''))
    video = {
        'plot': plot,
        'plotoutline': plot,
        'genre': safe_get(show_info, 'genres', ''),
        'title': show_info['name'],
        'tvshowtitle': show_info['name'],
        'status': safe_get(show_info, 'status', ''),
        'mediatype': 'tvshow',
        # This property is passed as "url" parameter to getepisodelist call
        'episodeguide': str(show_info['id']),
    }
    if show_info['network'] is not None:
        country = show_info['network']['country']
        video['studio'] = '{0} ({1})'.format(show_info['network']['name'], country['code'])
        video['country'] = country['name']
    elif show_info['webChannel'] is not None:
        video['studio'] = show_info['webChannel']['name']
        # Global Web Channels do not have a country specified
        if show_info['webChannel']['country'] is not None:
            country = show_info['webChannel']['country']
            video['country'] = country['name']
            video['studio'] += ' ({})'.format(country['code'])
    if show_info['premiered'] is not None:
        video['year'] = int(show_info['premiered'][:4])
        video['premiered'] = show_info['premiered']
    if full_info:
        video['credits'] = _get_credits(show_info)
        list_item = set_show_artwork(show_info, list_item)
        list_item = _add_season_info(show_info, list_item)
        list_item = _set_cast(show_info, list_item)
    else:
        image = safe_get(show_info, 'image', {})
        image_url = _extract_artwork_url(image)
        if image_url:
            list_item.addAvailableArtwork(image_url, 'poster')
    list_item.setInfo('video', video)
    list_item = _set_rating(show_info, list_item)
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
        summary = safe_get(episode_info, 'summary')
        if summary is not None:
            video['plot'] = video['plotoutline'] = _clean_plot(summary)
        if episode_info['runtime'] is not None:
            video['duration'] = episode_info['runtime'] * 60
        if episode_info['airdate'] is not None:
            video['premiered'] = episode_info['airdate']
    list_item.setInfo('video', video)
    image = safe_get(episode_info, 'image', {})
    image_url = _extract_artwork_url(image)
    if image_url:
        list_item.addAvailableArtwork(image_url, 'thumb')
    list_item.setUniqueIDs({'tvmaze': str(episode_info['id'])}, 'tvmaze')
    return list_item


def parse_nfo_url(nfo):
    # type: (Text) -> Optional[UrlParseResult]
    """Extract show ID from NFO file contents"""
    for regexp in SHOW_ID_REGEXPS:
        show_id_match = re.search(regexp, nfo, re.I)
        if show_id_match:
            return UrlParseResult(show_id_match.group(1), show_id_match.group(2))
    return None

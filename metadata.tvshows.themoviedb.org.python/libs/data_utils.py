# -*- coding: UTF-8 -*-
#
# Copyright (C) 2020, Team Kodi
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
# pylint: disable=missing-docstring
#
# This is based on the metadata.tvmaze scrapper by Roman Miroshnychenko aka Roman V.M.

"""Functions to process data"""

from __future__ import absolute_import, unicode_literals

import re
import json
from collections import OrderedDict, namedtuple
from .utils import safe_get, logger
from . import settings, api_utils

try:
    from typing import Optional, Text, Dict, List, Any  # pylint: disable=unused-import
    from xbmcgui import ListItem  # pylint: disable=unused-import
    InfoType = Dict[Text, Any]  # pylint: disable=invalid-name
except ImportError:
    pass

TMDB_PARAMS = {'api_key': settings.TMDB_CLOWNCAR, 'language': settings.LANG}
BASE_URL = 'https://api.themoviedb.org/3/{}'
FIND_URL = BASE_URL.format('find/{}')
TAG_RE = re.compile(r'<[^>]+>')

# Regular expressions are listed in order of priority.
# "TMDB" provider is preferred than other providers (IMDB and TheTVDB),
# because external providers IDs need to be converted to TMDB_ID.
SHOW_ID_REGEXPS = (
    r'(themoviedb)\.org/tv/(\d+).*/episode_group/(.*)',   # TMDB_http_link
    r'(themoviedb)\.org/tv/(\d+)',                        # TMDB_http_link
    r'(themoviedb)\.org/./tv/(\d+)',                      # TMDB_http_link
    r'(tmdb)\.org/./tv/(\d+)',                            # TMDB_http_link
    r'(imdb)\.com/.+/(tt\d+)',                            # IMDB_http_link
    r'(thetvdb)\.com.+&id=(\d+)',                         # TheTVDB_http_link
    r'(thetvdb)\.com/series/(\d+)',                       # TheTVDB_http_link
    r'(thetvdb)\.com/api/.*series/(\d+)',                 # TheTVDB_http_link
    r'(thetvdb)\.com/.*?"id":(\d+)',                      # TheTVDB_http_link
    r'<uniqueid.+?type="(tvdb|imdb)".*?>([t\d]+?)</uniqueid>'
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
VALIDEXTIDS = ['tmdb_id', 'imdb_id', 'tvdb_id']

UrlParseResult = namedtuple(
    'UrlParseResult', ['provider', 'show_id', 'ep_grouping'])


def _clean_plot(plot):
    # type: (Text) -> Text
    """Replace HTML tags with Kodi skin tags"""
    for repl in CLEAN_PLOT_REPLACEMENTS:
        plot = plot.replace(repl[0], repl[1])
    plot = TAG_RE.sub('', plot)
    return plot


def _set_cast(cast_info, list_item):
    # type: (InfoType, ListItem) -> ListItem
    """Save cast info to list item"""
    cast = []
    for item in cast_info:
        data = {
            'name': item['name'],
            'role': item.get('character', item.get('character_name', '')),
            'order': item['order'],
        }
        thumb = None
        if safe_get(item, 'profile_path') is not None:
            thumb = settings.IMAGEROOTURL + item['profile_path']
        if thumb:
            data['thumbnail'] = thumb
        cast.append(data)
    list_item.setCast(cast)
    return list_item


def _get_credits(show_info):
    # type: (InfoType) -> List[Text]
    """Extract show creator(s) and writer(s) from show info"""
    credits = []
    for item in show_info.get('created_by', []):
        credits.append(item['name'])
    for item in show_info.get('credits', {}).get('crew', []):
        isWriter = item.get('job', '').lower() == 'writer' or item.get(
            'department', '').lower() == 'writing'
        if isWriter and item.get('name') not in credits:
            credits.append(item['name'])
    return credits


def _get_directors(episode_info):
    # type: (InfoType) -> List[Text]
    """Extract episode writer(s) from episode info"""
    directors_ = []
    for item in episode_info.get('credits', {}).get('crew', []):
        if item.get('job') == 'Director':
            directors_.append(item['name'])
    return directors_


def _set_unique_ids(ext_ids, list_item):
    # type: (InfoType, ListItem) -> ListItem
    """Extract unique ID in various online databases"""
    unique_ids = {}
    for key, value in ext_ids.items():
        if key in VALIDEXTIDS and value:
            key = key[:-3]
            unique_ids[key] = str(value)
    list_item.setUniqueIDs(unique_ids, 'tmdb')
    return list_item


def _set_rating(the_info, list_item, episode=False):
    # type: (InfoType, ListItem, bool) -> ListItem
    """Set show/episode rating"""
    first = True
    for rating_type in settings.RATING_TYPES:
        logger.debug('adding rating type of %s' % rating_type)
        rating = float(the_info.get('ratings', {}).get(
            rating_type, {}).get('rating', '0'))
        votes = int(the_info.get('ratings', {}).get(
            rating_type, {}).get('votes', '0'))
        logger.debug("adding rating of %s and votes of %s" %
                     (str(rating), str(votes)))
        if rating > 0:
            list_item.setRating(rating_type, rating,
                                votes=votes, defaultt=first)
            first = False
    return list_item


def _add_season_info(show_info, list_item):
    # type: (InfoType, ListItem) -> ListItem
    """Add info for show seasons"""
    for season in show_info['seasons']:
        logger.debug('adding information for season %s to list item' %
                     season['season_number'])
        list_item.addSeason(season['season_number'],
                            safe_get(season, 'name', ''))
        for image_type, image_list in season.get('images', {}).items():
            if image_type == 'posters':
                destination = 'poster'
            else:
                destination = image_type
            for image in image_list:
                if image.get('type') == 'fanarttv':
                    theurl = image['file_path']
                    previewurl = theurl.replace(
                        '.fanart.tv/fanart/', '.fanart.tv/preview/')
                else:
                    theurl = settings.IMAGEROOTURL + image['file_path']
                    previewurl = settings.PREVIEWROOTURL + image['file_path']
                list_item.addAvailableArtwork(
                    theurl, art_type=destination, preview=previewurl, season=season['season_number'])
    return list_item


def get_image_urls(image):
    # type: (Dict) -> Tuple[Text, Text]
    """Get image URLs from image information"""
    if image.get('file_path', '').endswith('.svg'):
        return None, None
    if image.get('type') == 'fanarttv':
        theurl = image['file_path']
        previewurl = theurl.replace(
            '.fanart.tv/fanart/', '.fanart.tv/preview/')
    else:
        theurl = settings.IMAGEROOTURL + image['file_path']
        previewurl = settings.PREVIEWROOTURL + image['file_path']
    return theurl, previewurl


def set_show_artwork(show_info, list_item):
    # type: (InfoType, ListItem) -> ListItem
    """Set available images for a show"""
    for image_type, image_list in show_info.get('images', {}).items():
        if image_type == 'backdrops':
            fanart_list = []
            for image in image_list:
                theurl, previewurl = get_image_urls(image)
                if image.get('iso_639_1') != None and settings.CATLANDSCAPE and theurl:
                    list_item.addAvailableArtwork(
                        theurl, art_type="landscape", preview=previewurl)
                elif theurl:
                    fanart_list.append({'image': theurl})
            if fanart_list:
                list_item.setAvailableFanart(fanart_list)
        else:
            if image_type == 'posters':
                destination = 'poster'
            elif image_type == 'logos':
                destination = 'clearlogo'
            else:
                destination = image_type
            for image in image_list:
                theurl, previewurl = get_image_urls(image)
                if theurl:
                    list_item.addAvailableArtwork(
                        theurl, art_type=destination, preview=previewurl)
    return list_item


def add_main_show_info(list_item, show_info, full_info=True):
    # type: (ListItem, InfoType, bool) -> ListItem
    """Add main show info to a list item"""
    plot = _clean_plot(safe_get(show_info, 'overview', ''))
    original_name = show_info.get('original_name')
    if settings.KEEPTITLE and original_name:
        showname = original_name
    else:
        showname = show_info['name']
    video = {
        'plot': plot,
        'plotoutline': plot,
        'title': showname,
        'originaltitle': original_name,
        'tvshowtitle': showname,
        'mediatype': 'tvshow',
        # This property is passed as "url" parameter to getepisodelist call
        'episodeguide': str(show_info['id']),
    }
    if show_info.get('first_air_date'):
        video['year'] = int(show_info['first_air_date'][:4])
        video['premiered'] = show_info['first_air_date']
    if full_info:
        video['status'] = safe_get(show_info, 'status', '')
        genre_list = safe_get(show_info, 'genres', {})
        genres = []
        for genre in genre_list:
            genres.append(genre['name'])
        video['genre'] = genres
        networks = show_info.get('networks', [])
        if networks:
            network = networks[0]
            country = network.get('origin_country', '')
        else:
            network = None
            country = None
        if network and country and settings.STUDIOCOUNTRY:
            video['studio'] = '{0} ({1})'.format(network['name'], country)
        elif network:
            video['studio'] = network['name']
        if country:
            video['country'] = country
        content_ratings = show_info.get(
            'content_ratings', {}).get('results', {})
        if content_ratings:
            mpaa = ''
            mpaa_backup = ''
            for content_rating in content_ratings:
                iso = content_rating.get('iso_3166_1', '').lower()
                if iso == 'us':
                    mpaa_backup = content_rating.get('rating')
                if iso == settings.CERT_COUNTRY.lower():
                    mpaa = content_rating.get('rating', '')
            if not mpaa:
                mpaa = mpaa_backup
            if mpaa:
                video['Mpaa'] = settings.CERT_PREFIX + mpaa
        video['credits'] = video['writer'] = _get_credits(show_info)
        if settings.ENABTRAILER:
            trailer = _parse_trailer(show_info.get(
                'videos', {}).get('results', {}))
            if trailer:
                video['trailer'] = trailer
        list_item = set_show_artwork(show_info, list_item)
        list_item = _add_season_info(show_info, list_item)
        list_item = _set_cast(show_info['credits']['cast'], list_item)
        list_item = _set_rating(show_info, list_item)
        ext_ids = {'tmdb_id': show_info['id']}
        ext_ids.update(show_info.get('external_ids', {}))
        list_item = _set_unique_ids(ext_ids, list_item)
    else:
        image = safe_get(show_info, 'poster_path', '')
        if image:
            theurl = settings.IMAGEROOTURL + image
            previewurl = settings.PREVIEWROOTURL + image
            list_item.addAvailableArtwork(
                theurl, art_type='poster', preview=previewurl)
    logger.debug('adding tv show information for %s to list item' %
                 video['tvshowtitle'])
    list_item.setInfo('video', video)
    # This is needed for getting artwork
    list_item = _set_unique_ids(show_info, list_item)
    return list_item


def add_episode_info(list_item, episode_info, full_info=True):
    # type: (ListItem, InfoType, bool) -> ListItem
    """Add episode info to a list item"""
    video = {
        'title': episode_info.get('name', 'Episode ' + str(episode_info['episode_number'])),
        'season': episode_info['season_number'],
        'episode': episode_info['episode_number'],
        'mediatype': 'episode',
    }
    if safe_get(episode_info, 'air_date') is not None:
        video['aired'] = episode_info['air_date']
    if full_info:
        summary = safe_get(episode_info, 'overview')
        if summary is not None:
            video['plot'] = video['plotoutline'] = _clean_plot(summary)
        if safe_get(episode_info, 'air_date') is not None:
            video['premiered'] = episode_info['air_date']
        duration = episode_info.get('runtime')
        if duration:
            video['duration'] = int(duration) * 60
        list_item = _set_cast(
            episode_info['season_cast'] + episode_info['credits']['guest_stars'], list_item)
        ext_ids = {'tmdb_id': episode_info['id']}
        ext_ids.update(episode_info.get('external_ids', {}))
        list_item = _set_unique_ids(ext_ids, list_item)
        list_item = _set_rating(episode_info, list_item, episode=True)
        for image in episode_info.get('images', {}).get('stills', []):
            img_path = image.get('file_path')
            if img_path:
                theurl = settings.IMAGEROOTURL + img_path
                previewurl = settings.PREVIEWROOTURL + img_path
                list_item.addAvailableArtwork(
                    theurl, art_type='thumb', preview=previewurl)
        video['credits'] = video['writer'] = _get_credits(episode_info)
        video['director'] = _get_directors(episode_info)
    logger.debug('adding episode information for S%sE%s - %s to list item' %
                 (video['season'], video['episode'], video['title']))
    list_item.setInfo('video', video)
    return list_item


def parse_nfo_url(nfo):
    # type: (Text) -> Optional[UrlParseResult]
    """Extract show ID and named seasons from NFO file contents"""
    # work around for xbmcgui.ListItem.addSeason overwriting named seasons from NFO files
    ns_regex = r'<namedseason number="(.*)">(.*)</namedseason>'
    ns_match = re.findall(ns_regex, nfo, re.I)
    sid_match = None
    ep_grouping = None
    for regexp in SHOW_ID_REGEXPS:
        logger.debug('trying regex to match service from parsing nfo:')
        logger.debug(regexp)
        show_id_match = re.search(regexp, nfo, re.I)
        if show_id_match:
            logger.debug('match group 1: ' + show_id_match.group(1))
            logger.debug('match group 2: ' + show_id_match.group(2))
            if show_id_match.group(1) == "themoviedb" or show_id_match.group(1) == "tmdb":
                try:
                    ep_grouping = show_id_match.group(3)
                except IndexError:
                    pass
                tmdb_id = show_id_match.group(2)
            else:
                tmdb_id = _convert_ext_id(
                    show_id_match.group(1), show_id_match.group(2))
            if tmdb_id:
                logger.debug('match group 3: ' + str(ep_grouping))
                sid_match = UrlParseResult('themoviedb', tmdb_id, ep_grouping)
                break
    return sid_match, ns_match


def _convert_ext_id(ext_provider, ext_id):
    providers_dict = {'imdb': 'imdb_id',
                      'thetvdb': 'tvdb_id',
                      'tvdb': 'tvdb_id'}
    show_url = FIND_URL.format(ext_id)
    params = TMDB_PARAMS.copy()
    params['external_source'] = providers_dict[ext_provider]
    show_info = api_utils.load_info(show_url, params=params)
    if show_info:
        tv_results = show_info.get('tv_results')
        if tv_results:
            return tv_results[0].get('id')
    return None


def parse_media_id(title):
    title = title.lower()
    if title.startswith('tt') and title[2:].isdigit():
        # IMDB ID works alone because it is clear
        return {'type': 'imdb_id', 'title': title}
    # IMDB ID with prefix to match
    elif title.startswith('imdb/tt') and title[7:].isdigit():
        # IMDB ID works alone because it is clear
        return {'type': 'imdb_id', 'title': title[5:]}
    elif title.startswith('tmdb/') and title[5:].isdigit():  # TMDB ID
        return {'type': 'tmdb_id', 'title': title[5:]}
    elif title.startswith('tvdb/') and title[5:].isdigit():  # TVDB ID
        return {'type': 'tvdb_id', 'title': title[5:]}
    return None


def _parse_trailer(results):
    if results:
        if settings.PLAYERSOPT == 'tubed':
            addon_player = 'plugin://plugin.video.tubed/?mode=play&video_id='
        elif settings.PLAYERSOPT == 'youtube':
            addon_player = 'plugin://plugin.video.youtube/?action=play_video&videoid='
        backup_keys = []
        for video_lang in [settings.LANG[0:2], 'en']:
            for result in results:
                if result.get('site') == 'YouTube' and result.get('iso_639_1') == video_lang:
                    key = result.get('key')
                    if result.get('type') == 'Trailer':
                        if _check_youtube(key):
                            # video is available and is defined as "Trailer" by TMDB. Perfect link!
                            return addon_player+key
                    else:
                        # video is available, but NOT defined as "Trailer" by TMDB. Saving it as backup in case it doesn't find any perfect link.
                        backup_keys.append(key)
            for keybackup in backup_keys:
                if _check_youtube(keybackup):
                    return addon_player+keybackup
    return None


def _check_youtube(key):
    chk_link = "https://www.youtube.com/watch?v="+key
    check = api_utils.load_info(chk_link, resp_type='not_json')
    if not check or "Video unavailable" in check:       # video not available
        return False
    return True

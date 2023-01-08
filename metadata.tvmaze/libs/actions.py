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

"""Plugin route actions"""

import json
import sys
from typing import Optional
from urllib import parse as urllib_parse

import xbmcgui
import xbmcplugin

from . import tvmaze_api, data_service
from .utils import logger, get_episode_order, ADDON

HANDLE = int(sys.argv[1])


def find_show(title: str, year: Optional[str] = None) -> None:
    """Find a show by title"""
    search_results = data_service.search_show(title, year)
    for search_result in search_results:
        show_name = search_result['name']
        if search_result.get('premiered'):
            show_name += f' ({search_result["premiered"][:4]})'
        list_item = xbmcgui.ListItem(show_name, offscreen=True)
        list_item = data_service.add_main_show_info(list_item, search_result, False)
        # Below "url" is some unique ID string (may be an actual URL to a show page)
        # that is used to get information about a specific TV show.
        xbmcplugin.addDirectoryItem(
            HANDLE,
            url=str(search_result['id']),
            listitem=list_item,
            isFolder=True
        )


def parse_nfo_file(nfo: str, full_nfo: bool):
    """
    Analyze NFO file contents

    This function is called either instead of find_show
    if a tvshow.nfo file is found in the TV show folder or for each episode
    if episode NFOs are present along with episode files.

    :param nfo: the contents of an NFO file
    :param full_nfo: use the info from an NFO and not to try to get the info by the scraper
    """
    is_tvshow_nfo = True
    logger.debug(f'Trying to parse NFO file:\n{nfo}')
    info = None
    if '<episodedetails>' in nfo:
        if full_nfo:
            return
        is_tvshow_nfo = False
        info = data_service.parse_episode_xml_nfo(nfo)
        if info is None:
            # We cannot resolve an episode by alternative IDs or by title/year from TVmaze API
            return
    if info is None and '<tvshow>' in nfo:
        if full_nfo:
            return
        info = data_service.parse_tvshow_xml_nfo(nfo)
    if info is None:
        info = data_service.parse_url_nfo(nfo)
    if info is not None:
        list_item = xbmcgui.ListItem(offscreen=True)
        id_string = str(info['id'])
        uniqueids = {'tvmaze': id_string}
        list_item.setUniqueIDs(uniqueids, 'tvmaze')
        if is_tvshow_nfo:
            episodeguide = json.dumps(uniqueids)
            list_item.setInfo('video', {'episodeguide': episodeguide})
        # "url" is some string that unique identifies a show.
        # It may be an actual URL of a TV show page.
        xbmcplugin.addDirectoryItem(
            HANDLE,
            url=id_string,
            listitem=list_item,
            isFolder=True
        )


def get_details(show_id: str, default_rating: str) -> None:
    """Get details about a specific show"""
    logger.debug(f'Getting details for show id {show_id}')
    show_info = tvmaze_api.load_show_info(show_id)
    if show_info is not None:
        list_item = xbmcgui.ListItem(show_info['name'], offscreen=True)
        list_item = data_service.add_main_show_info(list_item, show_info,
                                                    default_rating=default_rating)
        xbmcplugin.setResolvedUrl(HANDLE, True, list_item)
    else:
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem(offscreen=True))


def get_episode_list(episodeguide: str, episode_order: str) -> None:  # pylint: disable=missing-docstring
    logger.debug(f'Getting episode list for episodeguide {episodeguide}, order: {episode_order}')
    show_id = None
    if episodeguide.startswith('{'):
        show_id = data_service.parse_json_episogeguide(episodeguide)
        if show_id is None:
            logger.error(f'Unable to determine TVmaze show ID from episodeguide: {episodeguide}')
            return
    if show_id is None and not episodeguide.isdigit():
        logger.warning(f'Invalid episodeguide format: {episodeguide} (probably URL).')
        show_id = data_service.parse_url_episodeguide(episodeguide)
    if show_id is None and episodeguide.isdigit():
        logger.warning(f'Invalid episodeguide format: {episodeguide} (a numeric string). '
                       f'Please consider re-scanning the show to update episodeguide record.')
        show_id = episodeguide
    if show_id is not None:
        episodes_map = data_service.get_episodes_map(show_id, episode_order)
        for episode in episodes_map.values():
            list_item = xbmcgui.ListItem(episode['name'], offscreen=True)
            data_service.add_episode_info(list_item, episode, full_info=False)
            encoded_ids = urllib_parse.urlencode({
                'show_id': show_id,
                'episode_id': str(episode['id']),
                'season': str(episode['season']),
                'episode': str(episode['number']),
            })
            # Below "url" is some unique ID string (it may be an actual URL to an episode page)
            # that allows to retrieve information about a specific episode.
            url = urllib_parse.quote(encoded_ids)
            xbmcplugin.addDirectoryItem(
                HANDLE,
                url=url,
                listitem=list_item,
                isFolder=True
            )


def get_episode_details(encoded_ids: str, episode_order: str) -> None:  # pylint: disable=missing-docstring
    encoded_ids = urllib_parse.unquote(encoded_ids)
    decoded_ids = dict(urllib_parse.parse_qsl(encoded_ids))
    logger.debug(f'Getting episode details for {decoded_ids}')
    episode_info = data_service.get_episode_info(decoded_ids['show_id'],
                                                 decoded_ids['episode_id'],
                                                 decoded_ids['season'],
                                                 decoded_ids['episode'],
                                                 episode_order)
    if episode_info:
        list_item = xbmcgui.ListItem(episode_info['name'], offscreen=True)
        list_item = data_service.add_episode_info(list_item, episode_info, full_info=True)
        xbmcplugin.setResolvedUrl(HANDLE, True, list_item)
    else:
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem(offscreen=True))


def get_artwork(show_id: str) -> None:
    """
    Get available artwork for a show

    :param show_id: default unique ID set by setUniqueIDs() method
    """
    logger.debug(f'Getting artwork for show ID {show_id}')
    if show_id:
        show_info = tvmaze_api.load_show_info(show_id)
        if show_info is not None:
            list_item = xbmcgui.ListItem(show_info['name'], offscreen=True)
            list_item = data_service.set_show_artwork(show_info, list_item)
            xbmcplugin.setResolvedUrl(HANDLE, True, list_item)
        else:
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem(offscreen=True))


def router(paramstring: str) -> None:
    """
    Route addon calls

    :param paramstring: url-encoded query string
    :raises RuntimeError: on unknown call action
    """
    params = dict(urllib_parse.parse_qsl(paramstring))
    logger.debug(f'Called addon with params: {sys.argv}')
    path_settings = json.loads(params.get('pathSettings') or '{}')
    logger.debug(f'Path settings: {path_settings}')
    episode_order = get_episode_order(path_settings)
    default_rating = path_settings.get('default_rating')
    if default_rating is None:
        default_rating = ADDON.getSetting('default_rating')
    full_nfo = path_settings.get('full_nfo')
    if full_nfo is None:
        full_nfo = ADDON.getSettingBool('full_nfo')
    if params['action'] == 'find':
        find_show(params['title'], params.get('year'))
    elif params['action'].lower() == 'nfourl':
        parse_nfo_file(params['nfo'], full_nfo)
    elif params['action'] == 'getdetails':
        get_details(params['url'], default_rating)
    elif params['action'] == 'getepisodelist':
        get_episode_list(params['url'], episode_order)
    elif params['action'] == 'getepisodedetails':
        get_episode_details(params['url'], episode_order)
    elif params['action'] == 'getartwork':
        get_artwork(params.get('id'))
    else:
        raise RuntimeError(f'Invalid addon call: {sys.argv}')
    xbmcplugin.endOfDirectory(HANDLE)

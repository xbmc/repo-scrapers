# -*- coding: UTF-8 -*-
#

"""Plugin route actions"""

from __future__ import absolute_import, unicode_literals

import sys
import json
import urllib.parse
import xbmcgui
import xbmcplugin
from . import tsdb, data_utils, cache
from .utils import logger
try:
    from typing import Optional, Text, Union, ByteString  # pylint: disable=unused-import
except ImportError:
    pass

HANDLE = int(sys.argv[1])  # type: int


def find_show(title):
    # type: (Union[Text, bytes]) -> None
    """Find a show by title"""
    if not isinstance(title, str):
        title = title.decode('utf-8')
    logger.debug('Searching for sports event {}'.format(title))
    search_results = tsdb.search_show(title)
    for search_result in search_results:
        show_name = search_result.get('strLeague')
        list_item = xbmcgui.ListItem(show_name, offscreen=True)
        list_item = data_utils.add_main_show_info(
            list_item, search_result, full_info=False)
        # Below "url" is some unique ID string (may be an actual URL to a show page)
        # that is used to get information about a specific league.
        xbmcplugin.addDirectoryItem(
            HANDLE,
            url=str(search_result['idLeague']),
            listitem=list_item,
            isFolder=True
        )


def get_show_id_from_nfo(nfo):
    # type: (Text) -> None
    """
    Get show ID by NFO file contents

    This function is called first instead of find_show
    if a NFO file is found in a TV show folder.

    :param nfo: the contents of a NFO file
    """
    if isinstance(nfo, bytes):
        nfo = nfo.decode('utf-8', 'replace')
    logger.debug('Parsing NFO file:\n{}'.format(nfo))
    parse_result = data_utils.parse_nfo_url(nfo)
    if parse_result:
        if parse_result.provider == 'thesportsdb':
            show_info = tsdb.load_show_info(parse_result.show_id)
        else:
            show_info = None
        if show_info is not None:
            list_item = xbmcgui.ListItem(
                show_info['strLeague'], offscreen=True)
            # "url" is some string that unique identifies a league.
            # It may be an actual URL of a TV show page.
            xbmcplugin.addDirectoryItem(
                HANDLE,
                url=str(show_info['idLeague']),
                listitem=list_item,
                isFolder=True
            )


def get_details(show_id):
    # type: (Text) -> None
    """Get details about a specific league"""
    logger.debug('Getting details for league id {}'.format(show_id))
    show_info = tsdb.load_show_info(show_id)
    if show_info is not None:
        list_item = xbmcgui.ListItem(show_info['strLeague'], offscreen=True)
        list_item = data_utils.add_main_show_info(
            list_item, show_info, full_info=True)
        xbmcplugin.setResolvedUrl(HANDLE, True, list_item)
    else:
        xbmcplugin.setResolvedUrl(
            HANDLE, False, xbmcgui.ListItem(offscreen=True))


def get_episode_list(show_ids):
    # type: (Text) -> None
    """Get games in a league"""
    # Kodi has a bug: when a show directory contains an XML NFO file with
    # episodeguide URL, that URL is always passed here regardless of
    # the actual parsing result in get_show_from_nfo()
    # so much of this weird logic is to deal with that
    try:
        all_ids = json.loads(show_ids)
        show_id = all_ids.get('tsdb')
    except (ValueError, AttributeError):
        show_id = str(show_ids)
        if show_id.isdigit():
            logger.error(
                'using deprecated episodeguide format, this league should be refreshed or rescraped')
    if not show_id:
        raise RuntimeError(
            'No The SportsDB league id found in episode guide, this league should be refreshed or rescraped')
    elif not show_id.isdigit():
        parsed = False
        parse_result = data_utils.parse_nfo_url(show_id)
        if parse_result:
            if parse_result.provider == 'thesportsdb':
                show_info = tsdb.load_show_info(parse_result.show_id)
                parsed = True
        if not parsed:
            raise RuntimeError(
                'No SportsDB league id found in episode guide, this league should be refreshed or rescraped')
    logger.debug('Getting event list for sports show id {}'.format(show_id))
    show_info = tsdb.load_show_info(show_id)
    if show_info is not None:
        idLeague = show_info.get('idLeague', 0)
        seasons = show_info.get('seasons')
        if not seasons:
            seasons = show_info['seasons'] = data_utils._add_season_info(
                show_info, None)
        event_list = []
        for season in seasons:
            events = tsdb.load_season_episodes(
                idLeague, season.get('season_name', ''))
            if events:
                ep_num = 1
                for event in events:
                    event['strEpisode'] = str(ep_num)
                    event['strLeague'] = show_info.get('strLeague', '')
                    event_list.append(event)
                    encoded_ids = urllib.parse.urlencode(
                        {'show_id': idLeague, 'episode_id': event.get('idEvent', 0)})
                    list_item = xbmcgui.ListItem(
                        event.get('strEvent', ''), offscreen=True)
                    list_item = data_utils.add_episode_info(
                        list_item, event, full_info=False)
                    # Below "url" is some unique ID string (may be an actual URL to an episode page)
                    # that allows to retrieve information about a specific episode.
                    url = urllib.parse.quote(encoded_ids)
                    xbmcplugin.addDirectoryItem(
                        HANDLE,
                        url=url,
                        listitem=list_item,
                        isFolder=True
                    )
                    ep_num = ep_num + 1
        show_info['event_list'] = event_list
        cache.cache_show_info(show_info)


def get_episode_details(encoded_ids):  # pylint: disable=missing-docstring
    # type: (Text) -> None
    """Get details about a specific game"""
    encoded_ids = urllib.parse.unquote(encoded_ids)
    decoded_ids = dict(urllib.parse.parse_qsl(encoded_ids))
    logger.debug('Getting event details for {}'.format(decoded_ids))
    episode_info = tsdb.load_episode_info(
        decoded_ids['show_id'], decoded_ids['episode_id']
    )
    if episode_info:
        list_item = xbmcgui.ListItem(
            episode_info.get('strEvent', ''), offscreen=True)
        list_item = data_utils.add_episode_info(
            list_item, episode_info, full_info=True)
        xbmcplugin.setResolvedUrl(HANDLE, True, list_item)
    else:
        xbmcplugin.setResolvedUrl(
            HANDLE, False, xbmcgui.ListItem(offscreen=True))


def get_artwork(show_id):
    # type: (Text) -> None
    """
    Get available artwork for a show

    :param show_id: default unique ID set by setUniqueIDs() method
    """
    if not show_id:
        return
    logger.debug('Getting artwork for show ID {}'.format(show_id))
    show_info = tsdb.load_show_info(show_id)
    if show_info is not None:
        list_item = xbmcgui.ListItem(
            show_info.get('strLeague', ''), offscreen=True)
        list_item = data_utils.set_show_artwork(show_info, list_item)
        xbmcplugin.setResolvedUrl(HANDLE, True, list_item)
    else:
        xbmcplugin.setResolvedUrl(
            HANDLE, False, xbmcgui.ListItem(offscreen=True))


def router(paramstring):
    # type: (Text) -> None
    """
    Route addon calls

    :param paramstring: url-encoded query string
    :raises RuntimeError: on unknown call action
    """
    params = dict(urllib.parse.parse_qsl(paramstring))
    logger.debug('Called addon with params: {}'.format(sys.argv))
    if params['action'] == 'find':
        logger.debug('performing find action')
        find_show(params['title'])
    elif params['action'].lower() == 'nfourl':
        logger.debug('performing nfourl action')
        get_show_id_from_nfo(params['nfo'])
    elif params['action'] == 'getdetails':
        logger.debug('performing getdetails action')
        get_details(params['url'])
    elif params['action'] == 'getepisodelist':
        logger.debug('performing getepisodelist action')
        get_episode_list(params['url'])
    elif params['action'] == 'getepisodedetails':
        logger.debug('performing getepisodedetails action')
        get_episode_details(params['url'])
    elif params['action'] == 'getartwork':
        logger.debug('performing getartwork action')
        get_artwork(params.get('id'))
    else:
        raise RuntimeError('Invalid addon call: {}'.format(sys.argv))
    xbmcplugin.endOfDirectory(HANDLE)

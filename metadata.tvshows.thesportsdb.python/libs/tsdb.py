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

"""Functions to interact with TMDb API"""

from __future__ import absolute_import, unicode_literals

import unicodedata
from math import floor
from pprint import pformat
from . import cache, api_utils, settings
from .utils import logger
try:
    from typing import Text, Optional, Union, List, Dict, Any  # pylint: disable=unused-import
    InfoType = Dict[Text, Any]  # pylint: disable=invalid-name
except ImportError:
    pass

base_url = 'https://www.thesportsdb.com/api/v1/json/863583675235/{}'
SEARCH_URL = base_url.format('all_leagues.php')
SHOW_URL = base_url.format('lookupleague.php')
SEASON_URL = base_url.format('search_all_seasons.php')
EVENTLIST_URL = base_url.format('eventsseason.php')
EPISODE_URL = base_url.format('lookupevent.php')
ROSTER_URL = base_url.format('searchplayers.php')
TEAMLIST_URL = base_url.format('search_all_teams.php')
HEADERS = (
    ('User-Agent', 'Kodi sports events scraper by pkscout; contact pkscout@kodi.tv'),
    ('Accept', 'application/json'),
)

api_utils.set_headers(dict(HEADERS))


def search_show(title):
    # type: (Text) -> Optional[List]
    """
    Search for a single sports league

    :param title: Sports League title to search
    :return: a dict with the matching sports league
    """
    params = {}
    results = []
    logger.debug('using title of %s to find league' % title)
    resp = api_utils.load_info(
        SEARCH_URL, params=params, verboselog=settings.VERBOSELOG)
    if resp is not None:
        for league in resp.get('leagues'):
            if league.get('strLeague') == title:
                params['id'] = league.get('idLeague')
                resp_d = api_utils.load_info(
                    SHOW_URL, params=params, verboselog=settings.VERBOSELOG)
                if resp_d is not None:
                    results = resp_d.get('leagues')
                break
    return results


def load_show_info(show_id):
    # type: (Text) -> Optional[InfoType]
    """Save rosters info to list item"""
    """
    Get full info for a single league

    :param show_id: thesportsDB League ID
    :return: show info or None
    """
    show_info = cache.load_show_info_from_cache(show_id)
    if show_info is None:
        logger.debug('no cache file found, loading from scratch')
        params = {}
        params['id'] = show_id
        resp = api_utils.load_info(
            SHOW_URL, params=params, verboselog=settings.VERBOSELOG)
        if resp is None:
            return None
        show_info = resp.get('leagues', [])[0]
        logger.debug('saving show info to the cache')
        if settings.VERBOSELOG:
            logger.debug(format(pformat(show_info)))
        cache.cache_show_info(show_info)
    else:
        logger.debug('using cached show info')
    return show_info


def load_episode_info(show_id, episode_id):
    # type: (Text, Text) -> Optional[InfoType]
    """
    Load episode info

    :param show_id:
    :param episode_id:
    :return: episode info or None
    """
    show_info = load_show_info(show_id)
    found_event = False
    if show_info is not None:
        for event in show_info.get('event_list'):
            if event.get('idEvent') == episode_id:
                episode_info = event
                found_event = True
                break
        if not found_event:
            return None
        params = {'id': episode_id}
        resp = api_utils.load_info(
            EPISODE_URL, params=params, verboselog=settings.VERBOSELOG)
        if resp is None:
            return None
        ep_return = resp.get('events', [])[0]
        ep_return['strEpisode'] = episode_info.get('strEpisode', '0')
        return ep_return
    return None


def load_roster_info(team_id, team_name):
    # type: (Text, Text) -> Optional[InfoType]
    """
    Load roster info

    :param team_id:
    :param team_name:
    :return: team roster or None
    """
    players = None
    resp = cache.load_show_info_from_cache(team_id)
    if not resp:
        params = {'t': team_name.replace(' ', '_')}
        resp = api_utils.load_info(
            ROSTER_URL, params=params, verboselog=settings.VERBOSELOG)
    if resp:
        players = resp.get('player')
        info = {'idTeam': team_id, 'player': players}
        cache.cache_show_info(info, info_type='roster')
    return players


def load_team_list(league_name):
    # type: (Text) -> Optional[InfoType]
    """
    Load team list for league

    :param league_name:
    :return: team list or None
    """
    teams = None
    params = {'l': league_name.replace(' ', '_')}
    resp = api_utils.load_info(
        TEAMLIST_URL, params=params, verboselog=settings.VERBOSELOG)
    if resp:
        teams = resp.get('teams')
    return teams


def load_season_info(show_id):
    # type: (Text) -> Optional[InfoType]
    """
    Load season info

    :param show_id:
    :return: season list or None
    """
    params = {'id': show_id}
    resp = api_utils.load_info(
        SEASON_URL, params=params, verboselog=settings.VERBOSELOG)
    if resp:
        return resp.get('seasons')
    return None


def load_season_episodes(idLeague, season_name):
   # type: (int, Text) -> Optional[InfoType]
    """
    Load episode list for given season

    :param idLeague:
    :param season_name:
    :return: episode list or None
    """
    params = {}
    params['id'] = idLeague
    params['s'] = season_name
    resp = api_utils.load_info(
        EVENTLIST_URL, params=params, verboselog=settings.VERBOSELOG)
    if resp:
        return resp.get('events')
    return None

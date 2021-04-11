#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys

import xbmcgui
import xbmcplugin

from . import tvdb
from .artwork import add_artworks
from .ratings import ratings
from .utils import log

HANDLE = int(sys.argv[1])


def search_series(title, settings, year=None) -> None:
    # add the found shows to the list
    log(f'Searching for TV show "{title}"')

    search_results = tvdb.search_series_api(title, settings)

    log(f'Search results {search_results}')

    possible_matches = _match_by_year(
        search_results, year, title) if year else _filter_exact_matches(search_results, title)

    search_results = possible_matches if len(
        possible_matches) > 0 else search_results

    if search_results is None:
        return
    for show in search_results:
        nameAndYear = f"{show['seriesName']}" if not show[
            'firstAired'] else f"{show['seriesName']} ({show['firstAired']})"

        liz = xbmcgui.ListItem(nameAndYear, offscreen=True)
        xbmcplugin.addDirectoryItem(
            handle=HANDLE,
            url=str(show['id']),
            listitem=liz,
            isFolder=True
        )


def _match_by_year(search_results: list, year: int, title: str) -> list:
    if search_results is None:
        return []

    exact_matches_with_year = _filter_exact_matches(
        search_results, f"{title} ({year})")

    if len(exact_matches_with_year) > 0:
        return exact_matches_with_year

    exact_year_match = tvdb.filter_by_year(
        _filter_exact_matches(search_results, title), year)

    if len(exact_year_match) > 0:
        return exact_year_match

    nearest_year = _nearest(
        [int(item['firstAired'][:4]) for item in search_results if 'firstAired' in item and item['firstAired']], int(year))
    exact_match_nearest_year = tvdb.filter_by_year(
        _filter_exact_matches(search_results, title), nearest_year)

    if len(exact_match_nearest_year) > 0:
        return exact_match_nearest_year

    # if all else fails, just match by title
    return _filter_exact_matches(
        search_results, title)


def search_series_by_imdb_id(imdb_id, settings) -> None:
    # add the found shows to the list
    log(f'Searching for TV show with imdb id "{imdb_id}"')

    search_results = tvdb.search_series_api('', settings, imdb_id)

    if search_results is None:
        return
    for show in search_results:
        liz = xbmcgui.ListItem(show['seriesName'], offscreen=True)
        xbmcplugin.addDirectoryItem(
            handle=HANDLE,
            url=str(show['id']),
            listitem=liz,
            isFolder=True
        )


def search_series_by_tvdb_id(tvdb_id, settings) -> None:
    # add the found shows to the list
    log(f'Searching for TV show with tvdb id "{tvdb_id}"')

    show = tvdb.get_series_details_api(tvdb_id, settings)

    if not show:
        xbmcplugin.setResolvedUrl(
            HANDLE, False, xbmcgui.ListItem(offscreen=True))
        return

    liz = xbmcgui.ListItem(show.seriesName, offscreen=True)
    xbmcplugin.addDirectoryItem(
        handle=HANDLE,
        url=str(show.id),
        listitem=liz,
        isFolder=True
    )


def _nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))


def _filter_exact_matches(series_list: list, title: str) -> list:
    ret = []
    if series_list is not None:
        for show in series_list:
            if show['seriesName'].casefold() == title.casefold():
                ret.append(show)
    return ret


def get_series_details(id, images_url: str, settings):
    # get the details of the found series
    log(f'Find info of tvshow with id {id}')
    show = tvdb.get_series_details_api(id, settings)
    if not show:
        xbmcplugin.setResolvedUrl(
            HANDLE, False, xbmcgui.ListItem(offscreen=True))
        return
    liz = xbmcgui.ListItem(show.seriesName, offscreen=True)
    liz.setInfo('video',
                {'title': show.seriesName,
                 'tvshowtitle': show.seriesName,
                 'plot': show.overview,
                 'plotoutline': show.overview,
                 'duration': int(show.runtime) * 60 if show.runtime else 0,
                 'mpaa': show.rating,
                 'genre': show.genre,
                 'studio': show.network,
                 'premiered': show.firstAired,
                 'status': show.status,
                 'episodeguide': show.id,
                 'mediatype': 'tvshow'
                 })

    ratings(liz, show, False, settings)

    if show.imdbId:
        liz.setUniqueIDs({'tvdb': show.id, 'imdb': show.imdbId}, 'tvdb')
    else:
        liz.setUniqueIDs({'tvdb': show.id}, 'tvdb')

    liz.setCast(_get_cast(show, images_url))
    add_artworks(show, liz, images_url)
    xbmcplugin.setResolvedUrl(handle=HANDLE, succeeded=True, listitem=liz)


def _get_cast(show, images_url: str):
    actors = []
    for actor in sorted(show.actors, key=lambda actor: actor['sortOrder']):
        if actor['image']:
            actors.append(
                {'name': actor['name'], 'role': actor['role'], 'thumbnail': images_url+actor['image']})
        else:
            actors.append({'name': actor['name'], 'role': actor['role']})
    return actors

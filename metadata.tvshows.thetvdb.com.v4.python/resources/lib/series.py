from pprint import pformat

import xbmcgui
import xbmcplugin
import json

from . import tvdb
from .artwork import add_artworks
from .tvdb import get_language
from .utils import logger

SUPPORTED_REMOTE_IDS = {
    'IMDB': 'imdb',
    'TheMovieDB.com': 'tmdb',
}

ARTWORK_URL_PREFIX = 'https://artworks.thetvdb.com'


def search_series(title, settings, handle, year=None) -> None:
    # add the found shows to the list
    logger.debug(f'Searching for TV show "{title}", year="{year}"')

    tvdb_client = tvdb.Client(settings)
    if year is None:
        search_results = tvdb_client.search(title, type="series", limit=10)
    else:
        search_results = tvdb_client.search(title, year=year, type="series", limit=10)
        if not search_results:
            logger.debug(f"No results found for '{title}' where year='{year}'. Falling back to search without year criteria.")
            search_results = tvdb_client.search(title, type="series", limit=10)

    logger.debug(f'Search results {search_results}')

    if not search_results:
        return

    language = get_language(settings)
    items = []
    for show in search_results:
        show_name = None
        translations = show.get('translations') or {}
        if translations:
            show_name = translations.get(language)
            if not show_name:
                show_name = translations.get('eng')
        if not show_name:
            show_name = show['name']
        year = show.get('year')
        if year:
            show_name += f' ({year})'

        liz = xbmcgui.ListItem(show_name, offscreen=True)
        url = str(show['tvdb_id'])
        is_folder = True
        items.append((url, liz, is_folder))

    xbmcplugin.addDirectoryItems(
        handle,
        items,
        len(items)
    )


def get_series_details(id, settings, handle):
    # get the details of the found series
    logger.debug(f'Find info of tvshow with id {id}')
    tvdb_client = tvdb.Client(settings)
    show = tvdb_client.get_series_details_api(id, settings)
    if not show:
        xbmcplugin.setResolvedUrl(
            handle, False, xbmcgui.ListItem(offscreen=True))
        return

    showId = {'tvdb': str(show["id"])}
    for remoteId in show.get('remoteIds'):
        if remoteId.get('sourceName') == "IMDB":
            showId['imdb'] = remoteId.get('id')
        if remoteId.get('sourceName') == "TheMovieDB.com":
            showId['tmdb'] = remoteId.get('id')
    
    details = {'title': show["name"],
                'tvshowtitle': show["name"],
                'plot': show["overview"],
                'plotoutline': show["overview"],
                'episodeguide': json.dumps(showId),
                'mediatype': 'tvshow',
                }
    name = show["name"]
    year_str = show.get("firstAired") or ''
    if year_str:
        year = int(year_str.split("-")[0])
        logger.debug(f"series year_str: {year_str}")
        details["premiered"] = year_str
        details['year'] = year
        name = f'{name} ({year})'
    studio = get_studio(show)
    if studio:
        details["studio"] = studio
    genres = get_genres(show)
    details["genre"] = genres
    country = show.get("originalCountry", None)
    if country:
        details["country"] = country
    status = show.get('status')
    if status:
        details['status'] = status['name']
    liz = xbmcgui.ListItem(name, offscreen=True)
    logger.debug(f"series details: {pformat(details)}")
    liz.setInfo('video', details)
    liz = set_cast(liz, show)
    unique_ids = get_unique_ids(show)
    liz.setUniqueIDs(unique_ids, 'tvdb')
    language = tvdb.get_language(settings)
    add_artworks(show, liz, language)
    xbmcplugin.setResolvedUrl(
        handle=handle, 
        succeeded=True, 
        listitem=liz)


def set_cast(liz, show):
    cast = []
    characters = show.get('characters') or ()
    for char in characters:
        if char["peopleType"] == "Actor":
            data = {
                'name': char['personName'],
                'role': char['name'],
            }
            thumbnail = char.get('image') or char.get('personImgURL')
            if thumbnail:
                if not thumbnail.startswith(ARTWORK_URL_PREFIX):
                    thumbnail = ARTWORK_URL_PREFIX + thumbnail
                data['thumbnail'] = thumbnail
            cast.append(data)
    liz.setCast(cast)
    return liz


def get_genres(show):
    return [genre["name"] for genre in show.get("genres", ())]


def get_studio(show):
    companies = show.get("companies", ())
    if not companies:
        return None
    studio = None
    if len(companies) == 1:
        return companies[0]['name']
    for company in companies:
        if company["primaryCompanyType"] == 1:
            studio = company["name"]
    return studio


def get_tags(show):
    tags = []
    tag_options = show.get("tagOptions", ())
    if tag_options:
        for tag in tag_options:
            tags.append(tag["name"])
    return tags


def get_unique_ids(show):
    unique_ids = {'tvdb': show['id']}
    remote_ids = show.get('remoteIds')
    if remote_ids:
        for remote_id_info in remote_ids:
            source_name = remote_id_info.get('sourceName')
            if source_name in SUPPORTED_REMOTE_IDS:
                unique_ids[SUPPORTED_REMOTE_IDS[source_name]] = remote_id_info['id']
    return unique_ids

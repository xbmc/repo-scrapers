from collections import defaultdict

import xbmcgui
import xbmcplugin

from . import tvdb
from .nfo import parse_episode_guide_url
from .utils import logger
from .series import get_unique_ids, ARTWORK_URL_PREFIX


# add the episodes of a series to the list


def get_series_episodes(id, settings, handle):
    logger.debug(f'Find episodes of tvshow with id {id}')
    if not id.isdigit():
        # Kodi has a bug: when a show directory contains an XML NFO file with
        # episodeguide URL, that URL is always passed here regardless of
        # the actual parsing result in get_show_id_from_nfo()
        parse_result = parse_episode_guide_url(id)
        if not parse_result:
            return

        if parse_result.provider == 'thetvdb':
            id = parse_result.show_id
            logger.debug(f'Changed show id to {id}')

    client = tvdb.Client(settings)
    episodes = client.get_series_episodes_api(id, settings)

    if not episodes:
        xbmcplugin.setResolvedUrl(
            handle, False, xbmcgui.ListItem(offscreen=True))
        return
    for ep in episodes:
        liz = xbmcgui.ListItem(ep['name'], offscreen=True)
        details = {
            'title': ep['name'],
            'season': ep['seasonNumber'],
            'episode': ep['number'],
        }
        date_string = ep.get("aired")
        if date_string:
            year = int(date_string.split("-")[0])
            details['premiered'] = details['date'] = date_string
            details['year'] = year
        logger.debug("details in episodes.py")
        logger.debug(details)
        liz.setInfo('video', details)
        xbmcplugin.addDirectoryItem(
            handle=handle, 
            url=str(ep['id']),
            listitem=liz, 
            isFolder=True
            )

# get the details of the found episode


def get_episode_details(id, settings, handle):
    logger.debug(f'Find info of episode with id {id}')
    client = tvdb.Client(settings)
    ep = client.get_episode_details_api(id, settings)
    if not ep:
        xbmcplugin.setResolvedUrl(
            handle, False, xbmcgui.ListItem(offscreen=True))
        return
    liz = xbmcgui.ListItem(ep["name"], offscreen=True)
    cast = get_episode_cast(ep)
    rating = get_rating(ep)
    tags = get_tags(ep)
    duration_minutes = ep.get('runtime') or 0

    details = {
        'title': ep["name"],
        'plot': ep["overview"],
        'plotoutline': ep["overview"],
        'premiered': ep["aired"],
        'aired': ep["aired"],
        'mediatype': 'episode',
        'director': cast["directors"],
        'writer': cast["writers"],
        'mpaa': rating,
        'duration': duration_minutes * 60,
    }

    if tags:
        details["tag"] = tags

    logger.debug("details in get episode details")
    logger.debug(details)
    logger.debug(ep)
    liz.setInfo('video', details)

    unique_ids = get_unique_ids(ep)
    liz.setUniqueIDs(unique_ids, 'tvdb')
    guest_stars = cast['guest_stars']
    if guest_stars:
        liz.setCast(guest_stars)
    if ep.get("image"):
        liz.addAvailableArtwork(ep["image"], 'thumb')
    xbmcplugin.setResolvedUrl(
        handle=handle, 
        succeeded=True,
        listitem=liz)


def get_episode_cast(ep):
    cast = defaultdict(list)
    characters = ep.get('characters')
    if characters:
        for char in characters:
            if char['peopleType'] == 'Writer':
                cast['writers'].append(char['personName'])
            elif char['peopleType'] == 'Director':
                cast['writers'].append(char['personName'])
            elif char['peopleType'] == 'Guest Star':
                person_info = {'name': char.get('personName') or ''}
                thumbnail = char.get('image') or char.get('personImgURL') or ''
                if thumbnail and not thumbnail.startswith(ARTWORK_URL_PREFIX):
                    thumbnail = ARTWORK_URL_PREFIX + thumbnail
                if thumbnail:
                    person_info['thumbnail'] = thumbnail
                cast['guest_stars'].append(person_info)
    return cast


def get_rating(ep):
    ratings = ep.get("contentRatings", [])
    rating = ''
    if len(ratings) == 1:
        rating = ratings[0]['country'] + ': ' + ratings[0]["name"]
    if not rating:
        for r in ratings:
            if r["country"] == "usa":
                rating = 'USA: ' + r["name"]
    return rating


def get_tags(ep):
    tags = []
    tag_options = ep.get("tagOptions", [])
    if tag_options:
        for tag in tag_options:
            tags.append(tag["name"])
    return tags

import enum
import re

import xbmcgui
import xbmcplugin

from . import tvdb
from .constants import COUNTRIES_MAP
from .utils import logger, get_language, get_rating_country_code


ARTWORK_URL_PREFIX = "https://artworks.thetvdb.com"

SUPPORTED_REMOTE_IDS = {
    'IMDB': 'imdb',
    'TheMovieDB.com': 'tmdb',
}

MAX_IMAGES_NUMBER = 10

# Some skins use those names to display rating icons
RATING_COUNTRY_MAP = {
    'gbr': 'UK',
    'nld': 'NL',
}


class ArtworkType(enum.IntEnum):
    POSTER = 14
    BACKGROUND = 15
    BANNER = 16
    ICON = 18
    CLEARART = 24
    CLEARLOGO = 25


def search_movie(title, settings, handle, year=None) -> None:
    # add the found shows to the list

    tvdb_client = tvdb.Client(settings)
    kwargs = {'limit': 10}
    if year is not None:
        kwargs['year'] = year
    search_results = tvdb_client.search(title, type="movie", **kwargs)
    if not search_results:
        return
    language = get_language(settings)
    items = []
    for movie in search_results:
        name = None
        translations = movie.get('translations') or {}
        if translations:
            name = translations.get(language)
            if not name:
                translations.get('eng')
        if not name:
            name = movie['name']
        if movie.get('year'):
            name += f' ({movie["year"]})'
        liz = xbmcgui.ListItem(name, offscreen=True)
        url = str(movie['tvdb_id'])
        is_folder = True
        items.append((url, liz, is_folder))
    xbmcplugin.addDirectoryItems(
        handle,
        items,
        len(items)
    )


def get_movie_details(id, settings, handle):
    # get the details of the found series
    tvdb_client = tvdb.Client(settings)

    language = get_language(settings)
    movie = tvdb_client.get_movie_details_api(id, language=language)
    if not movie:
        xbmcplugin.setResolvedUrl(
            handle, False, xbmcgui.ListItem(offscreen=True))
        return
    liz = xbmcgui.ListItem(movie["name"], offscreen=True)
    people = get_cast(movie)
    liz.setCast(people["cast"])
    genres = get_genres(movie)
    duration_minutes = movie.get('runtime') or 0
    details = {
        'title': movie["name"],
        'plot': movie["overview"],
        'plotoutline': movie["overview"],
        'mediatype': 'movie',
        'writer': people["writers"],
        'director': people["directors"],
        'genre': genres,
        'duration': duration_minutes * 60,
    }
    premiere_date = get_premiere_date(movie)
    if premiere_date is not None:
        details["year"] = premiere_date["year"]
        details["premiered"] = premiere_date["date"]
    rating_country_code = get_rating_country_code(settings)
    rating = get_rating(movie, rating_country_code)
    if rating:
        details["mpaa"] = rating
    
    country = movie.get("originalCountry", None)
    if country:
        details["country"] = COUNTRIES_MAP.get(country, '')

    studio = get_studio(movie)
    if studio:
        details["studio"] = studio

    if settings.get('get_tags'):
        tags = get_tags(movie)
        if tags:
            details["tag"] = tags
    
    trailer = get_trailer(movie)
    if trailer:
        details["trailer"] = trailer

    set_ = get_set(movie)
    set_poster = None
    if set_:
        set_info = tvdb_client.get_movie_set_info(set_["id"], settings)
        details["set"] = set_info["name"]
        details["setoverview"] = set_info["overview"]
        first_movie_in_set_id = set_info["movie_id"]
        if first_movie_in_set_id:
            first_movie_in_set = tvdb_client.get_movie_details_api(first_movie_in_set_id,
                                                                   language=language)
            set_poster = first_movie_in_set["image"]
    liz.setInfo('video', details)

    unique_ids = get_unique_ids(movie)
    liz.setUniqueIDs(unique_ids, 'tvdb')

    add_artworks(movie, liz, set_poster, language=language)
    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=liz)


def get_cast(movie):
    cast = []
    directors = []
    writers = []
    characters = movie.get('characters') or ()
    for char in characters:
        if char["peopleType"] == "Actor":
            d = {
                'name': char["personName"],
                'role': char["name"],
            }
            thumbnail = char.get('image') or char.get('personImgURL')
            if thumbnail:
                if not thumbnail.startswith(ARTWORK_URL_PREFIX):
                    thumbnail = ARTWORK_URL_PREFIX + thumbnail
                d['thumbnail'] = thumbnail
            cast.append(d)
        if char["peopleType"] == "Director":
            directors.append(char["personName"])
        if char["peopleType"] == "Writer":
            writers.append(char["personName"])
    return {
        "directors": directors,
        "writers": writers,
        "cast": cast,
    }


def get_artworks_from_movie(movie: dict, language='eng') -> dict:

    def sorter(item):
        item_language = item.get('language')
        score = item.get('score') or 0
        if item_language == language:
            return 3, score
        if item_language is None:
            return 2, score
        if item_language == 'eng':
            return 1, score
        return 0, score

    artworks = movie.get("artworks") or ()
    posters = []
    backgrounds = []
    banners = []
    icons = []
    cleararts = []
    clearlogos = []
    for art in artworks:
        art_type = art.get('type')
        if art_type == ArtworkType.POSTER:
            posters.append(art)
        elif art_type == ArtworkType.BACKGROUND:
            backgrounds.append(art)
        elif art_type == ArtworkType.BANNER:
            banners.append(art)
        elif art_type == ArtworkType.ICON:
            icons.append(art)
        elif art_type == ArtworkType.CLEARART:
            cleararts.append(art)
        elif art_type == ArtworkType.CLEARLOGO:
            clearlogos.append(art)
    posters.sort(key=sorter, reverse=True)
    backgrounds.sort(key=sorter, reverse=True)
    banners.sort(key=sorter, reverse=True)
    icons.sort(key=sorter, reverse=True)
    cleararts.sort(key=sorter, reverse=True)
    clearlogos.sort(key=sorter, reverse=True)
    artwork_dict = {
        'poster': posters[:MAX_IMAGES_NUMBER],
        'fanart': backgrounds[:MAX_IMAGES_NUMBER],
        'banner': banners[:MAX_IMAGES_NUMBER],
        'icon': banners[:MAX_IMAGES_NUMBER],
        'clearart': cleararts[:MAX_IMAGES_NUMBER],
        'clearlogo': clearlogos[:MAX_IMAGES_NUMBER]
    }
    return artwork_dict


def add_artworks(movie, liz, set_poster=None, language='eng'):
    
    artworks = get_artworks_from_movie(movie, language=language)
    fanarts = artworks.pop('fanart')

    if set_poster:
        liz.addAvailableArtwork(set_poster, 'set.poster')

    for image_type, images in artworks.items():
        for image in images:
            image_url = image.get('image') or ''
            if ARTWORK_URL_PREFIX not in image_url:
                image_url = ARTWORK_URL_PREFIX + image_url
            liz.addAvailableArtwork(image_url, image_type)

    fanart_items = []
    for fanart in fanarts:
        image = fanart.get("image", "")
        thumb  = fanart["thumbnail"]
        if ARTWORK_URL_PREFIX not in image:
            image = ARTWORK_URL_PREFIX + image
            thumb = ARTWORK_URL_PREFIX + thumb
        fanart_items.append(
            {'image': image, 'preview': thumb})
    if fanarts:
        liz.setAvailableFanart(fanart_items)


def get_artworks(id, settings, handle):
    tvdb_client = tvdb.Client(settings)
    movie = tvdb_client.get_series_details_api(id, settings)
    if not movie:
        xbmcplugin.setResolvedUrl(
            handle, False, xbmcgui.ListItem(offscreen=True))
        return
    liz = xbmcgui.ListItem(id, offscreen=True)
    language = get_language(settings)
    add_artworks(movie, liz, language=language)
    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=liz)


def get_premiere_date(movie):
    releases = movie.get("releases")
    if not releases:
        return None
    if len(releases) > 1:
        releases.sort(key=lambda r: r['date'])
    date_str = releases[0]['date']
    year = int(date_str.split("-")[0])
    return {
        "year": year,
        "date": date_str,
    }


def get_genres(movie):
    genres = movie.get('genres') or ()
    return [genre["name"] for genre in genres]


def get_rating(movie, rating_country_code):
    ratings = movie.get("contentRatings")
    rating = ""
    if ratings:
        if len(ratings) == 1:
            rating = ratings[0]["name"]
            country_code = ratings[0]['country']
            if country_code in RATING_COUNTRY_MAP:
                country = RATING_COUNTRY_MAP[country_code]
            else:
                country = COUNTRIES_MAP.get(country_code)
            if country is not None and country_code != 'usa':
                rating = f'{country}:{rating}'
            else:
                rating = f'Rated {rating}'
        if not rating:
            usa_rating = ''
            local_rating = ''
            for rating in ratings:
                if rating['country'] == 'usa':
                    usa_rating = f"Rated {rating['name']}"
                elif rating_country_code != 'usa' and rating['country'] == rating_country_code:
                    local_rating = rating['name']
                    country_code = rating['country']
                    if country_code in RATING_COUNTRY_MAP:
                        country = RATING_COUNTRY_MAP[country_code]
                    else:
                        country = COUNTRIES_MAP.get(country_code)
                    if country is not None:
                        local_rating = f'{country}:{local_rating}'
            rating = local_rating if local_rating else usa_rating
    return rating


def get_studio(movie):
    studios = movie.get("studios", [])
    if not studios or len(studios) == 0:
        return None
    name = studios[0]["name"]
    return name


def get_tags(movie):
    tags = []
    tag_options = movie.get("tagOptions", [])
    if tag_options:
        for tag in tag_options:
            tags.append(tag["name"])
    return tags


def get_set(movie):
    lists = movie.get("lists", None)
    if not lists:
        return None
    
    name = ""
    id = 0
    score = -1.0
    logger.debug(lists)
    for l in lists:
        if l["isOfficial"] and l["score"] > score:
            score = l["score"]
            name = l["name"]
            id = l["id"]
    if name and id:
        logger.debug("name and id in get set")
        logger.debug(name)
        logger.debug(id)
        return {
            "name": name,
            "id": id,
        }
 
    return None


def get_trailer(movie):
    trailer_url = ""
    originalLang = movie.get("originalLanguage", None)
    if not originalLang:
        originalLang = "eng"
    
    trailers = movie.get("trailers", None)
    if not trailers:
        return None

    for trailer in trailers:
        if trailer["language"] == originalLang:
            trailer_url = trailer["url"]
    
    match = re.search("youtube", trailer_url)
    if not match:
        return None

    trailer_id_match = re.search("\?v=[A-z]+", trailer_url)
    if not trailer_id_match:
        return None
    trailer_id = trailer_id_match.group(0)
    url = f'plugin://plugin.video.youtube/play/?video_id={trailer_id}'
    return url


def get_unique_ids(movie):
    unique_ids = {'tvdb': movie['id']}
    remote_ids = movie.get('remoteIds')
    if remote_ids:
        for remote_id_info in remote_ids:
            source_name = remote_id_info.get('sourceName')
            if source_name in SUPPORTED_REMOTE_IDS:
                unique_ids[SUPPORTED_REMOTE_IDS[source_name]] = remote_id_info['id']
    return unique_ids

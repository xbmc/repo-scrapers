import enum
import urllib.parse

from resources.lib import simple_requests as requests
from resources.lib.constants import LANGUAGES_MAP
from resources.lib.utils import logger, ADDON

apikey = "edae60dc-1b44-4bac-8db7-65c0aaf5258b"
apikey_with_pin = "51bdbd35-bcd5-40d9-9bc3-788e24454baf"

USER_AGENT = 'TheTVDB v.4 TV Scraper for Kodi'


class ArtworkType(enum.IntEnum):
    BANNER = 1
    POSTER = 2
    BACKGROUND = 3
    ICON = 5
    CLEARART = 22
    CLEARLOGO = 23


class SeasonType(enum.IntEnum):
    DEFAULT = 1
    ABSOLUTE = 2
    DVD = 3
    ALTERNATE = 4
    REGIONAL = 5
    ALTDVD = 6


class Auth:
    logger.debug("logging in")

    def __init__(self, url, apikey, pin="", **kwargs):
        loginInfo = {"apikey": apikey}
        if pin:
            loginInfo["pin"] = pin
            loginInfo["apikey"] = apikey_with_pin
        loginInfo.update(kwargs)
        logger.debug("body in auth call")
        logger.debug(loginInfo)
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'application/json',
        }
        response = requests.post(url, headers=headers, json=loginInfo)
        if not response.ok:
            response.raise_for_status()
        self.token = response.json()['data']['token']

    def get_token(self):
        return self.token


class Request:
    def __init__(self, auth_token):
        self.auth_token = auth_token
        self.cache = {}

    def make_api_request(self, url):
        logger.debug(f"about to make request to url {url}")
        logger.debug(url)
        data = self.cache.get(url, None)
        if data:
            return data
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.auth_token}'
        }
        response = requests.get(url, headers=headers)
        if not response.ok:
            response.raise_for_status()
        data = response.json()['data']
        self.cache[url] = data
        return data

    @staticmethod
    def make_web_request(url):
        logger.debug(f"about to make request to url {url}")
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html',
        }
        response = requests.get(url, headers=headers)
        if not response.ok:
            response.raise_for_status()
        return response.text


class Url:
    def __init__(self):
        self.base_url = "https://api4.thetvdb.com/v4"

    def login_url(self):
        return "{}/login".format(self.base_url)

    def artwork_status_url(self):
        return "{}/artwork/statuses".format(self.base_url)

    def artwork_types_url(self):
        return "{}/artwork/types".format(self.base_url)

    def artwork_url(self, id, extended=False):
        url = "{}/artwork/{}".format(self.base_url, id)
        if extended:
            url = "{}/extended".format(url)
        return url

    def awards_url(self, page):
        if page < 0:
            page = 0
        url = "{}/awards?page={}".format(self.base_url, page)
        return url

    def award_url(self, id, extended=False):
        url = "{}/awards/{}".format(self.base_url, id)
        if extended:
            url = "{}/extended".format(url)
        return url

    def awards_categories_url(self):
        url = "{}/awards/categories".format(self.base_url)
        return url

    def award_category_url(self, id, extended=False):
        url = "{}/awards/categories/{}".format(self.base_url, id)
        if extended:
            url = "{}/extended".format(url)
        return url

    def content_ratings_url(self):
        url = "{}/content/ratings".format(self.base_url)
        return url

    def countries_url(self):
        url = "{}/countries".format(self.base_url)
        return url

    def companies_url(self, page=0):
        url = "{}/companies?page={}".format(self.base_url, page)
        return url

    def company_url(self, id):
        url = "{}/companies/{}".format(self.base_url, id)
        return url

    def all_series_url(self, page=0):
        url = "{}/series".format(self.base_url)
        return url

    def series_url(self, id, extended=False):
        url = "{}/series/{}".format(self.base_url, id)
        if extended:
            url = "{}/extended".format(url)
        return url

    def movies_url(self, page=0):
        url = "{}/movies".format(self.base_url, id)
        return url

    def movie_url(self, id, extended=False):
        url = "{}/movies/{}".format(self.base_url, id)
        if extended:
            url = "{}/extended".format(url)
        return url

    def season_url(self, id, extended=False):
        url = "{}/seasons/{}".format(self.base_url, id)
        if extended:
            url = "{}/extended?meta=episodes".format(url)
        return url

    def episode_url(self, id, extended=False):
        url = "{}/episodes/{}".format(self.base_url, id)
        if extended:
            url = "{}/extended".format(url)
        return url

    def episode_translation_url(self, id: int, language: str = "eng"):
        url = "{}/episodes/{}/translations/{}".format(
            self.base_url, id, language)
        return url

    def person_url(self, id, extended=False):
        url = "{}/people/{}".format(self.base_url, id)
        if extended:
            url = "{}/extended".format(url)
        return url

    def character_url(self, id):
        url = "{}/characters/{}".format(self.base_url, id)
        return url

    def people_types_url(self, id):
        url = "{}/people/types".format(self.base_url)
        return url

    def source_types_url(self):
        url = "{}/sources/types".format(self.base_url)
        return url

    def updates_url(self, since=0):
        url = "{}/updates?since={}".format(self.base_url, since)
        return url

    def tag_options_url(self):
        url = "{}/tags/options".format(self.base_url)
        return url

    def tag_option_url(self, id):
        url = "{}/tags/options/{}".format(self.base_url, id)
        return url

    def search_url(self, query, filters):
        filters["query"] = query
        qs = urllib.parse.urlencode(filters)
        url = "{}/search?{}".format(self.base_url, qs)
        return url

    def series_translation_url(self, id: int, language="eng"):
        url = "{}/series/{}/translations/{}".format(
            self.base_url, id, language)
        return url

    def series_season_episodes_url(self, id: int, season_type_number: int = 1, page: int = 0):
        season_type = SeasonType(season_type_number).name.lower()
        url = "{}/series/{}/episodes/{}?page={}".format(
            self.base_url, id, season_type, page)
        return url


class TVDB:
    def __init__(self, apikey: str, pin="", **kwargs):
        self.url = Url()
        login_url = self.url.login_url()
        self.auth = Auth(login_url, apikey, pin, **kwargs)
        auth_token = self.auth.get_token()
        self.request = Request(auth_token)

    def get_artwork_statuses(self) -> list:
        """Returns a list of artwork statuses"""
        url = self.url.artwork_status_url()
        return self.request.make_api_request(url)

    def get_artwork_types(self) -> list:
        """Returns a list of artwork types"""
        url = self.url.artwork_types_url()
        return self.request.make_api_request(url)

    def get_artwork(self, id: int) -> dict:
        """Returns an artwork dictionary"""
        url = self.url.artwork_url(id)
        return self.request.make_api_request(url)

    def get_artwork_extended(self, id: int) -> dict:
        """Returns an artwork extended dictionary"""
        url = self.url.artwork_url(id, True)
        return self.request.make_api_request(url)

    def get_all_awards(self, page=0) -> list:
        """Returns a list of awards"""
        url = self.url.awards_url(page)
        return self.request.make_api_request(url)

    def get_award(self, id: int) -> dict:
        """Returns an award dictionary"""
        url = self.url.award_url(id, False)
        return self.request.make_api_request(url)

    def get_award_extended(self, id: int) -> dict:
        """Returns an award extended dictionary"""
        url = self.url.award_url(id, True)
        return self.request.make_api_request(url)

    def get_all_award_categories(self) -> list:
        """Returns a list of award categories"""
        url = self.url.awards_categories_url()
        return self.request.make_api_request(url)

    def get_award_category(self, id: int) -> dict:
        """Returns an artwork category dictionary"""
        url = self.url.award_category_url(id, False)
        return self.request.make_api_request(url)

    def get_award_category_extended(self, id: int) -> dict:
        """Returns an award category extended dictionary"""
        url = self.url.award_category_url(id, True)
        return self.request.make_api_request(url)

    def get_content_ratings(self) -> list:
        """Returns a list of content ratings"""
        url = self.url.content_ratings_url()
        return self.request.make_api_request(url)

    def get_countries(self) -> list:
        """Returns a list of countries"""
        url = self.url.countries_url()
        return self.request.make_api_request(url)

    def get_all_companies(self, page=0) -> list:
        """Returns a list of companies"""
        url = self.url.companies_url(page)
        return self.request.make_api_request(url)

    def get_company(self, id: int) -> dict:
        """Returns a company dictionary"""
        url = self.url.company_url(id)
        return self.request.make_api_request(url)

    def get_all_series(self, page=0) -> list:
        """Returns a list of series"""
        url = self.url.all_series_url(page)
        return self.request.make_api_request(url)

    def get_series(self, id: int) -> dict:
        """Returns a series dictionary"""
        url = self.url.series_url(id, False)
        return self.request.make_api_request(url)

    def get_series_extended(self, id: int) -> dict:
        """Returns an series extended dictionary"""
        url = self.url.series_url(id, True)
        return self.request.make_api_request(url)

    def get_series_translation(self, id: int, lang: str) -> dict:
        """Returns a series translation dictionary"""
        url = self.url.series_translation_url(id, lang)
        return self.request.make_api_request(url)

    def get_all_movies(self, page=0) -> list:
        """Returns a list of movies"""
        url = self.url.movies_url(page)
        return self.request.make_api_request(url)

    def get_movie(self, id: int) -> dict:
        """Returns a movie dictionary"""
        url = self.url.movie_url(id, False)
        return self.request.make_api_request(url)

    def get_movie_extended(self, id: int) -> dict:
        """Returns a movie extended dictionary"""
        url = self.url.movie_url(id, True)
        return self.request.make_api_request(url)

    def get_movie_translation(self, lang: str) -> dict:
        """Returns a movie translation dictionary"""
        url = self.url.movie_translation_url(id, lang)
        return self.request.make_api_request(url)

    def get_season(self, id: int) -> dict:
        """Returns a season dictionary"""
        url = self.url.season_url(id, False)
        return self.request.make_api_request(url)

    def get_season_extended(self, id: int) -> dict:
        """Returns a season extended dictionary"""
        url = self.url.season_url(id, True)
        return self.request.make_api_request(url)

    def get_episode(self, id: int) -> dict:
        """Returns an episode dictionary"""
        url = self.url.episode_url(id, False)
        return self.request.make_api_request(url)

    def get_episode_translation(self, id: int, lang: str) -> dict:
        """Returns an episode translation dictionary"""
        url = self.url.episode_translation_url(id, lang)
        return self.request.make_api_request(url)

    def get_episode_extended(self, id: int) -> dict:
        """Returns an episode extended dictionary"""
        url = self.url.episode_url(id, True)
        return self.request.make_api_request(url)

    def get_person(self, id: int) -> dict:
        """Returns a person dictionary"""
        url = self.url.person_url(id, False)
        return self.request.make_api_request(url)

    def get_person_extended(self, id: int) -> dict:
        """Returns a person extended dictionary"""
        url = self.url.person_url(id, True)
        return self.request.make_api_request(url)

    def get_character(self, id: int) -> dict:
        """Returns a character dictionary"""
        url = self.url.character_url(id)
        return self.request.make_api_request(url)

    def get_all_people_types(self) -> list:
        """Returns a list of people types"""
        url = self.url.people_types_url()
        return self.request.make_api_request(url)

    def get_all_sourcetypes(self) -> list:
        """Returns a list of sourcetypes"""
        url = self.url.source_types_url()
        return self.request.make_api_request(url)

    def get_updates(self, since: int) -> list:
        """Returns a list of updates"""
        url = self.url.updates_url(since)
        return self.request.make_api_request(url)

    def get_all_tag_options(self, page=0) -> list:
        """Returns a list of tag options"""
        url = self.url.tag_options_url()
        return self.request.make_api_request(url)

    def get_tag_option(self, id: int) -> dict:
        """Returns a tag option dictionary"""
        url = self.url.tag_option_url(id)
        return self.request.make_api_request(url)

    def search(self, query, **kwargs) -> list:
        """Returns a list of search results"""
        url = self.url.search_url(query, kwargs)
        return self.request.make_api_request(url)

    def get_series_season_episodes(self, id: int, season_type: int = 1):
        page = 0
        episodes = []
        while True:
            url = self.url.series_season_episodes_url(id, season_type, page)
            res = self.request.make_api_request(url).get("episodes", [])
            page += 1
            if not res:
                break
            episodes.extend(res)
        return episodes

    def get_series_details_api(self, id, settings=None) -> dict:
        settings = settings or {}
        series = self.get_series_extended(id)
        language = get_language(settings)
        try:
            translation = self.get_series_translation(id, language)
        except requests.HTTPError as exc:
            logger.warning(f'{language} translation is not available: {exc}')
            translation = {}
        overview = translation.get("overview") or ''
        name = translation.get("name") or ''
        if not (overview or name) and translation.get('language') != 'eng':
            try:
                english_info = self.get_series_translation(id, 'eng')
            except requests.HTTPError as exc:
                logger.warning(f'eng info is not available: {exc}')
                english_info = {}
            if not overview:
                overview = english_info.get('overview') or ''
            if not name:
                name = english_info.get('name') or ''
        if name:
            series["name"] = name
        series["overview"] = overview
        return series

    def get_series_episodes_api(self, id, settings):
        season_type = get_season_type(settings)
        result = self.get_series_season_episodes(id, season_type)
        if not result:
            season_type_name = SeasonType(season_type).name.lower()
            logger.warning(
                f'No episodes returned for show {id}, season type "{season_type_name}"')
        return result

    def get_episode_details_api(self, id, settings):
        try:
            ep = self.get_episode_extended(id)
        except requests.HTTPError as e:
            logger.warning(f'No episode found with id={id}. [error: {e}]')
            return None

        trans = None

        primary_language = get_language(settings)
        language_attempties = [primary_language] if primary_language == "eng" else [
            primary_language, "eng"]
        for language in language_attempties:
            try:
                trans = self.get_episode_translation(id, language)
                break
            except requests.HTTPError as e:
                logger.warning(
                    f'No episode found with id={id} and language={language}. [error: {e}]')
        
        if not trans:
            return None

        overview = trans.get("overview") or ''
        name = trans.get("name") or ''
        if not (overview and name) and trans['language'] != 'eng':
            try:
                english_info = self.get_episode_translation(id, 'eng')
                if not overview:
                    overview = english_info.get('overview') or ''
                if not name:
                    name = english_info.get('name') or ''
            except requests.HTTPError as e:
                logger.warning(
                    f'No episode found with id={id} and language=eng . [error: {e}]')
        ep["overview"] = overview
        ep["name"] = name
        return ep


def get_language(path_settings):
    language = path_settings.get('language')
    if language is None:
        language = ADDON.getSetting('language') or 'English'
    language_code = LANGUAGES_MAP.get(language, 'eng')
    return language_code


def get_season_type(settings):
    season_type_str = settings.get("season_type", "1")
    return int(season_type_str)


class Client(object):
    _instance = None

    def __new__(cls, settings=None):
        settings = settings or {}
        if cls._instance is None:
            pin = settings.get("pin", "")
            gender = settings.get("gender", "Other")
            uuid = settings.get("uuid", "")
            birth_year = settings.get("year", "")
            cls._instance = TVDB(apikey, pin=pin, gender=gender,
                                 birthYear=birth_year, uuid=uuid)
        return cls._instance


def get_artworks_from_show(show: dict, language: str = 'eng'):

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

    artworks = show.get("artworks", [{}])
    banners = []
    posters = []
    fanarts = []
    icons = []
    cleararts = []
    clearlogos = []
    for art in artworks:
        art_type = art.get('type')
        if art_type == ArtworkType.BANNER:
            banners.append(art)
        elif art_type == ArtworkType.POSTER:
            posters.append(art)
        elif art_type == ArtworkType.BACKGROUND:
            fanarts.append(art)
        elif art_type == ArtworkType.ICON:
            icons.append(art)
        elif art_type == ArtworkType.CLEARART:
            cleararts.append(art)
        elif art_type == ArtworkType.CLEARLOGO:
            clearlogos.append(art)
    banners.sort(key=sorter, reverse=True)
    posters.sort(key=sorter, reverse=True)
    fanarts.sort(key=sorter, reverse=True)
    season_posters = [(season.get("image", ""), season.get("number", 0))
                      for season in show.get("seasons", [])]
    artwork_dict = {
        'banner': banners,
        'poster': posters,
        'icon': icons,
        'clearart': cleararts,
        'clearlogo': clearlogos,

        'fanarts': fanarts,
        'season_posters': season_posters,
    }
    return artwork_dict

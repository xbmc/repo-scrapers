import uuid

import xbmc
from xbmcaddon import Addon

from .constants import LANGUAGES_MAP, REVERSED_COUNTRIES_MAP

ADDON = Addon()
ADDON_ID = ADDON.getAddonInfo('id')


class logger:
    log_message_prefix = '[{} ({})]: '.format(
        ADDON_ID, ADDON.getAddonInfo('version'))

    @staticmethod
    def log(message, level=xbmc.LOGDEBUG):
        message = logger.log_message_prefix + str(message)
        xbmc.log(message, level)

    @staticmethod
    def info(message):
        logger.log(message, xbmc.LOGINFO)

    @staticmethod
    def error(message):
        logger.log(message, xbmc.LOGERROR)

    @staticmethod
    def debug(message):
        logger.log(message, xbmc.LOGDEBUG)


def create_uuid():
    return str(uuid.uuid4())


def get_language(path_settings):
    language = path_settings.get('language')
    if language is None:
        language = ADDON.getSetting('language') or 'English'
    language_code = LANGUAGES_MAP.get(language, 'eng')
    return language_code


def get_rating_country_code(path_settings):
    rating_country = path_settings.get('rating_country')
    if rating_country is None:
        rating_country = ADDON.getSetting('rating_country') or 'USA'
    return REVERSED_COUNTRIES_MAP[rating_country]

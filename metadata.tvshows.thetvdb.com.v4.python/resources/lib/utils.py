import uuid

import xbmc
from xbmcaddon import Addon

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
    def debug(*messages):
        for message in messages:
            logger.log(message, xbmc.LOGDEBUG)

    @staticmethod
    def warning(message):
        logger.log(message, xbmc.LOGWARNING)


def create_uuid():
    return str(uuid.uuid4())

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

"""Misc utils"""
from typing import Text, Any, Dict

import xbmc
from xbmcaddon import Addon

ADDON = Addon()
ADDON_ID = ADDON.getAddonInfo('id')
VERSION = ADDON.getAddonInfo('version')

EPISODE_ORDER_MAP = {
    0: 'default',
    1: 'dvd_release',
    2: 'verbatim_order',
    3: 'country_premiere',
    4: 'streaming_premiere',
    5: 'broadcast_premiere',
    6: 'language_premiere',
}


class logger:
    log_message_prefix = f'[{ADDON_ID} ({VERSION})]: '

    @staticmethod
    def log(message: str, level: int = xbmc.LOGDEBUG) -> None:
        message = logger.log_message_prefix + message
        xbmc.log(message, level)

    @classmethod
    def info(cls, message: str) -> None:
        cls.log(message, xbmc.LOGINFO)

    @classmethod
    def error(cls, message: str) -> None:
        cls.log(message, xbmc.LOGERROR)

    @classmethod
    def debug(cls, message: str) -> None:
        logger.log(message, xbmc.LOGDEBUG)

    @classmethod
    def warning(cls, message: str) -> None:
        logger.log(message, xbmc.LOGWARNING)


def get_episode_order(path_settings: Dict[Text, Any]) -> str:
    episode_order_enum = path_settings.get('episode_order')
    if episode_order_enum is None:
        episode_order_enum = ADDON.getSettingInt('episode_order')
    episode_order = EPISODE_ORDER_MAP.get(episode_order_enum, 'default')
    return episode_order

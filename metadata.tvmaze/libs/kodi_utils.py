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
import logging
from decimal import Decimal
from typing import Dict, Any

import xbmc
from xbmcaddon import Addon

ADDON = Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
KODI_VERSION = Decimal(xbmc.getInfoLabel('System.BuildVersion')[:4])


class Settings:
    """Access addon settings"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._path_settings = {}

    def initialize(self, path_settings: Dict[str, Any]) -> None:
        self._path_settings.update(path_settings)

    def get_value_str(self, key: str) -> str:
        value = self._path_settings.get(key)
        if value is None:
            value = ADDON.getSettingString(key)
        return value

    def get_value_int(self, key: str) -> int:
        value = self._path_settings.get(key)
        if value is None:
            value = ADDON.getSettingInt(key)
        return value

    def get_value_bool(self, key: str) -> bool:
        value = self._path_settings.get(key)
        if value is None:
            value = ADDON.getSettingBool(key)
        return value


class KodiLogHandler(logging.Handler):
    """
    Logging handler that writes to the Kodi log with correct levels

    It also adds {addon_id} and {addon_version} variables available to log format.
    """
    LOG_FORMAT = '[{addon_id} v.{addon_version}] {filename}:{lineno} - {message}'
    LEVEL_MAP = {
        logging.NOTSET: xbmc.LOGNONE,
        logging.DEBUG: xbmc.LOGDEBUG,
        logging.INFO: xbmc.LOGINFO,
        logging.WARN: xbmc.LOGWARNING,
        logging.WARNING: xbmc.LOGWARNING,
        logging.ERROR: xbmc.LOGERROR,
        logging.CRITICAL: xbmc.LOGFATAL,
    }

    def emit(self, record):
        record.addon_id = ADDON_ID
        record.addon_version = ADDON_VERSION
        message = self.format(record)
        kodi_log_level = self.LEVEL_MAP.get(record.levelno, xbmc.LOGDEBUG)
        xbmc.log(message, level=kodi_log_level)


def initialize_logging():
    """
    Initialize the root logger that writes to the Kodi log

    After initialization, you can use Python logging facilities as usual.
    """
    logging.basicConfig(
        format=KodiLogHandler.LOG_FORMAT,
        style='{',
        level=logging.DEBUG,
        handlers=[KodiLogHandler()],
        force=True
    )

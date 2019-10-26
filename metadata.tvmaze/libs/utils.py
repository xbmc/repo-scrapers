# coding: utf-8
#
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

from __future__ import absolute_import
import os
from requests.sessions import Session
from six import PY2, text_type
import xbmc
from xbmcaddon import Addon
import xbmcvfs

HEADERS = (
    ('User-Agent', 'Kodi scraper for tvmaze.com by Roman V.M.; roman1972@gmail.com'),
    ('Accept', 'application/json'),
)

ADDON_ID = 'metadata.tvmaze'
ADDON = Addon()


class logger:
    log_message_prefix = '[{} ({})]: '.format(ADDON_ID, ADDON.getAddonInfo('version'))

    @staticmethod
    def log(message, level=xbmc.LOGDEBUG):
        if PY2 and isinstance(message, text_type):
            message = message.encode('utf-8')
        message = logger.log_message_prefix + message
        xbmc.log(message, level)

    @staticmethod
    def notice(message):
        logger.log(message, xbmc.LOGNOTICE)

    @staticmethod
    def error(message):
        logger.log(message, xbmc.LOGERROR)

    @staticmethod
    def debug(message):
        logger.log(message, xbmc.LOGDEBUG)


def get_requests_session():
    """Create requests Session"""
    session = Session()
    session.headers.update(dict(HEADERS))
    return session


def get_cache_directory():
    profile_dir = xbmc.translatePath(ADDON.getAddonInfo('profile'))
    if PY2:
        profile_dir = profile_dir.decode('utf-8')
    cache_dir = os.path.join(profile_dir, 'cache')
    if not xbmcvfs.exists(cache_dir):
        xbmcvfs.mkdir(cache_dir)
    return cache_dir


def safe_get(dct, key, default=None):
    """
    Get a key from dict

    Returns the respective value or default if key is missing or the value is None.
    """
    if key in dct and dct[key] is not None:
        return dct[key]
    return default

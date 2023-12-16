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

"""Cache-related functionality"""

import json
import logging
import os
import time
from typing import Optional, Text, Dict, Any, Union

import xbmcgui
import xbmcvfs

from .utils import ADDON_ID

EPISODES_CACHE_TTL = 60 * 10  # 10 minutes


class MemoryCache:
    _instance = None
    CACHE_KEY = f'__{ADDON_ID}_cache__'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._window = xbmcgui.Window(10000)

    def set(self, obj_id: Union[int, str], obj: Any) -> None:
        cache = {
            'id': obj_id,
            'timestamp': time.time(),
            'object': obj,
        }
        cache_json = json.dumps(cache)
        self._window.setProperty(self.CACHE_KEY, cache_json)

    def get(self, obj_id: Union[int, str]) -> Optional[Any]:
        cache_json = self._window.getProperty(self.CACHE_KEY)
        if not cache_json:
            logging.debug('Memory cache empty')
            return None
        try:
            cache = json.loads(cache_json)
        except ValueError as exc:
            logging.debug(f'Memory cache error: {exc}')
            return None
        if cache['id'] != obj_id or time.time() - cache['timestamp'] > EPISODES_CACHE_TTL:
            logging.debug('Memory cache miss')
            return None
        logging.debug('Memory cache hit')
        return cache['object']


def cache_episodes_map(show_id: Union[int, str], episodes_map: Dict[Text, Any]) -> None:
    MemoryCache().set(int(show_id), episodes_map)


def load_episodes_map_from_cache(show_id: Union[int, str]) -> Optional[Dict[str, Any]]:
    episodes_map = MemoryCache().get(int(show_id))
    return episodes_map


def _get_cache_directory() -> str:  # pylint: disable=missing-docstring
    temp_dir = xbmcvfs.translatePath('special://temp')
    if isinstance(temp_dir, bytes):
        temp_dir = temp_dir.decode('utf-8')
    cache_dir = os.path.join(temp_dir, 'scrapers', ADDON_ID)
    if not xbmcvfs.exists(cache_dir):
        xbmcvfs.mkdir(cache_dir)
    return cache_dir


CACHE_DIR = _get_cache_directory()


def cache_show_info(show_info: Dict[str, Any]) -> None:
    """
    Save show_info dict to cache
    """
    file_name = str(show_info['id']) + '.json'
    cache_json = json.dumps(show_info)
    with open(os.path.join(CACHE_DIR, file_name), 'w', encoding='utf-8') as fo:
        fo.write(cache_json)


def load_show_info_from_cache(show_id: Union[int, str]) -> Optional[Dict[str, Any]]:
    """
    Load show info from a local cache

    :param show_id: show ID on TVmaze
    :return: show_info dict or None
    """
    file_name = str(show_id) + '.json'
    try:
        with open(os.path.join(CACHE_DIR, file_name), 'r', encoding='utf-8') as fo:
            cache_json = fo.read()
        show_info = json.loads(cache_json)
        logging.debug('Show info cache hit')
        return show_info
    except (IOError, EOFError, ValueError) as exc:
        logging.debug('Cache error: %s %s', type(exc), exc)
        return None

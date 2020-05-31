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

"""Cache-related functionality"""

from __future__ import absolute_import, unicode_literals

import os
from datetime import datetime, timedelta

from six import PY2
from six.moves import cPickle as pickle
import xbmc
import xbmcvfs

from .utils import ADDON, logger

try:
    from typing import Optional, Text, Dict, Any  # pylint: disable=unused-import
except ImportError:
    pass


CACHING_DURATION = timedelta(hours=3)  # type: timedelta


def _get_cache_directory():  # pylint: disable=missing-docstring
    # type: () -> Text
    profile_dir = xbmc.translatePath(ADDON.getAddonInfo('profile'))
    if PY2:
        profile_dir = profile_dir.decode('utf-8')
    cache_dir = os.path.join(profile_dir, 'cache')
    if not xbmcvfs.exists(cache_dir):
        xbmcvfs.mkdir(cache_dir)
    return cache_dir


CACHE_DIR = _get_cache_directory()  # type: Text


def cache_show_info(show_info):
    # type: (Dict[Text, Any]) -> None
    """
    Save show_info dict to cache
    """
    file_name = str(show_info['id']) + '.pickle'
    cache = {
        'show_info': show_info,
        'timestamp': datetime.now(),
    }
    with open(os.path.join(CACHE_DIR, file_name), 'wb') as fo:
        pickle.dump(cache, fo, protocol=2)


def load_show_info_from_cache(show_id):
    # type: (Text) -> Optional[Dict[Text, Any]]
    """
    Load show info from a local cache

    :param show_id: show ID on TVmaze
    :return: show_info dict or None
    """
    file_name = str(show_id) + '.pickle'
    try:
        with open(os.path.join(CACHE_DIR, file_name), 'rb') as fo:
            cache = pickle.load(fo)
        if datetime.now() - cache['timestamp'] > CACHING_DURATION:
            return None
        return cache['show_info']
    except (IOError, pickle.PickleError) as exc:
        logger.debug('Cache error: {} {}'.format(type(exc), exc))
        return None

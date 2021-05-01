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

import io
import json
import os
import sys
import time
from collections import OrderedDict

import six
import xbmcvfs

try:
    from xbmcvfs import translatePath
except ImportError:
    from xbmc import translatePath

from .utils import ADDON, logger

try:
    from typing import Optional, Text, Dict, Any  # pylint: disable=unused-import
except ImportError:
    pass


CACHING_DURATION = 60 * 10


def _get_cache_directory():  # pylint: disable=missing-docstring
    # type: () -> Text
    profile_dir = translatePath(ADDON.getAddonInfo('profile'))
    if six.PY2:
        profile_dir = profile_dir.decode('utf-8')
    cache_dir = os.path.join(profile_dir, 'cache')
    if not xbmcvfs.exists(profile_dir):
        xbmcvfs.mkdir(profile_dir)
    if not xbmcvfs.exists(cache_dir):
        xbmcvfs.mkdir(cache_dir)
    return cache_dir


CACHE_DIR = _get_cache_directory()  # type: Text


def cache_show_info(show_info):
    # type: (Dict[Text, Any]) -> None
    """
    Save show_info dict to cache
    """
    file_name = str(show_info['id']) + '.json'
    cache = {
        'show_info': show_info,
        'timestamp': time.time(),
    }
    cache_json = json.dumps(cache)
    if isinstance(cache_json, six.text_type):
        cache_json = cache_json.encode('utf-8')
    with open(os.path.join(CACHE_DIR, file_name), 'wb') as fo:
        fo.write(cache_json)


def load_show_info_from_cache(show_id):
    # type: (Text) -> Optional[Dict[Text, Any]]
    """
    Load show info from a local cache

    :param show_id: show ID on TVmaze
    :return: show_info dict or None
    """
    file_name = str(show_id) + '.json'
    try:
        with io.open(os.path.join(CACHE_DIR, file_name), 'r',
                     encoding='utf-8') as fo:
            cache_json = fo.read()
        loads_kwargs = {}
        if sys.version_info < (3, 6):
            loads_kwargs['object_pairs_hook'] = OrderedDict
        cache = json.loads(cache_json, **loads_kwargs)
        if time.time() - cache['timestamp'] > CACHING_DURATION:
            return None
        return cache['show_info']
    except (IOError, EOFError, ValueError) as exc:
        logger.debug('Cache error: {} {}'.format(type(exc), exc))
        return None

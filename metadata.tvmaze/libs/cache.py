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

import os
from datetime import datetime, timedelta
from six.moves import cPickle as pickle
from .utils import get_cache_directory, logger

CACHE_DIR = get_cache_directory()
CACHING_DURATION = timedelta(hours=3)


def cache_show_info(show_info):
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
    """
    Load show info from a local cache

    :param show_id: show ID on TV Maze
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

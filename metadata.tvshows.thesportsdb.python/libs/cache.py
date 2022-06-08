# -*- coding: UTF-8 -*-
#

"""Cache-related functionality"""

from __future__ import absolute_import, unicode_literals

import os
import pickle
import xbmc
import xbmcvfs

from .utils import ADDON, logger

try:
    from typing import Optional, Text, Dict, Any  # pylint: disable=unused-import
except ImportError:
    pass


def _get_cache_directory():  # pylint: disable=missing-docstring
    # type: () -> Text
    temp_dir = xbmcvfs.translatePath('special://temp')
    cache_dir = os.path.join(temp_dir, 'scrapers', ADDON.getAddonInfo('id'))
    if not xbmcvfs.exists(cache_dir):
        xbmcvfs.mkdir(cache_dir)
    logger.debug('the cache dir is ' + cache_dir)
    return cache_dir


CACHE_DIR = _get_cache_directory()  # type: Text


def cache_show_info(info, info_type='league'):
    # type: (Dict[Text, Any], str) -> None
    """
    Save league or roster info dict to cache
    """
    if info_type == 'roster':
        file_name = str(info['idTeam']) + '.pickle'
    else:
        file_name = str(info['idLeague']) + '.pickle'
    cache = {
        'info': info
    }
    with open(os.path.join(CACHE_DIR, file_name), 'wb') as fo:
        pickle.dump(cache, fo, protocol=2)


def load_show_info_from_cache(id):
    # type: (Text) -> Optional[Dict[Text, Any]]
    """
    Load info from a local cache

    :param id: league or team id
    :return: show_info dict or None
    """
    file_name = str(id) + '.pickle'
    try:
        with open(os.path.join(CACHE_DIR, file_name), 'rb') as fo:
            load_kwargs = {}
            load_kwargs['encoding'] = 'bytes'
            cache = pickle.load(fo, **load_kwargs)
        return cache['info']
    except (IOError, pickle.PickleError) as exc:
        logger.debug('Cache message: {} {}'.format(type(exc), exc))
        return None

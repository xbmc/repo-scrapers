#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import xbmc
import xbmcaddon

ID = xbmcaddon.Addon().getAddonInfo('id')


def safe_get(dct, key, default=None):
    """
    Get a key from dict

    Returns the respective value or default if key is missing or the value is None.
    """
    if key in dct and dct[key] is not None:
        return dct[key]
    return default

# log function


def log(msg):
    xbmc.log(msg=f'{ID}: {msg}', level=xbmc.LOGDEBUG)

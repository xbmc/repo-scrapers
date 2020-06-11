#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import xbmcgui
import xbmcplugin
from . import tvdb

HANDLE = int(sys.argv[1])


def add_artworks(show, liz, images_url: str):
    # Set primary images
    if hasattr(show, 'poster') and show.poster:
        liz.addAvailableArtwork(images_url+show.poster, 'poster')
    if hasattr(show, 'banner') and show.banner:
        liz.addAvailableArtwork(images_url+show.banner, 'banner')
    if hasattr(show, 'fanart') and show.fanart:
        liz.addAvailableArtwork(images_url+show.fanart, 'fanart')

    for poster in sorted(show.Images.poster, key=lambda image: image['ratingsInfo']['average'], reverse=True):
        liz.addAvailableArtwork(images_url+poster['fileName'], 'poster')
    for banner in sorted(show.Images.series, key=lambda image: image['ratingsInfo']['average'], reverse=True):
        liz.addAvailableArtwork(images_url+banner['fileName'], 'banner')
    for season in sorted(show.Images.season, key=lambda image: image['ratingsInfo']['average'], reverse=True):
        liz.addAvailableArtwork(
            images_url+season['fileName'], 'poster', season=int(season['subKey']))
    for seasonwide in sorted(show.Images.seasonwide, key=lambda image: image['ratingsInfo']['average'], reverse=True):
        liz.addAvailableArtwork(
            images_url+seasonwide['fileName'], 'banner', season=int(seasonwide['subKey']))
    fanarts = []
    for fanart in sorted(show.Images.fanart, key=lambda image: image['ratingsInfo']['average'], reverse=True):
        fanarts.append(
            {'image': images_url+fanart['fileName'], 'preview': images_url+fanart['thumbnail']})
    if fanarts:
        liz.setAvailableFanart(fanarts)


def get_artworks(id, images_url: str, settings):
    show = tvdb.get_series_details_api(id, settings, False)
    if not show:
        xbmcplugin.setResolvedUrl(
            HANDLE, False, xbmcgui.ListItem(offscreen=True))
        return
    liz = xbmcgui.ListItem(id, offscreen=True)
    add_artworks(show, liz, images_url)
    xbmcplugin.setResolvedUrl(handle=HANDLE, succeeded=True, listitem=liz)

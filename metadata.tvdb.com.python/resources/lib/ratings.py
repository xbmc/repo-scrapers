#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from .imdb_rating import get_imdb_rating_and_votes
from .trakt_rating import get_trakt_rating_and_votes

HANDLE = int(sys.argv[1])


def ratings(liz, item, is_episode: bool, settings):

    imdb_is_default = _get_and_set_imdb_ratings(liz, item, settings)

    trakt_is_default = _get_and_set_trakt_ratings(
        liz, item, is_episode, settings)

    liz.setRating("tvdb", item.siteRating,
                  item.siteRatingCount, not (imdb_is_default or trakt_is_default))


def _get_and_set_imdb_ratings(liz, item, settings):
    got_imdb_rating = False
    is_imdb_def = False

    if item.imdbId:
        imdb_rating = get_imdb_rating_and_votes(item.imdbId)
        if imdb_rating['votes'] > 0:
            got_imdb_rating = True
            is_imdb_def = (item.imdbId and settings.getSettingInt(
                'RatingS') == 1)  # IMDb
            liz.setRating(
                "imdb", imdb_rating['rating'], imdb_rating['votes'], is_imdb_def)

    return is_imdb_def and got_imdb_rating


def _get_and_set_trakt_ratings(liz, item, is_episode: bool, settings):
    got_trakt_rating = False
    is_trakt_def = False

    trakt_rating = get_trakt_rating_and_votes(item.id, is_episode)
    if 'rating' in trakt_rating and trakt_rating['rating'] > 0:
        got_trakt_rating = True
        is_trakt_def = (settings.getSettingInt(
            'RatingS') == 2)  # Trakt

        if ('votes' in trakt_rating and trakt_rating['votes'] > 0):
            liz.setRating(
                "trakt", trakt_rating['rating'], trakt_rating['votes'], is_trakt_def)
        else:
            liz.setRating(
                "trakt", trakt_rating['rating'], defaultt=is_trakt_def)

    return is_trakt_def and got_trakt_rating

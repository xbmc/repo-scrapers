# -*- coding: UTF-8 -*-
#
# Copyright (C) 2020, Team Kodi
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
#
# IMDb ratings from script.module.imdbratings
# pylint: disable=missing-docstring

import imdbratings

from . import get_imdb_id


def get_details(uniqueids):
    imdb_id = get_imdb_id(uniqueids)
    if not imdb_id:
        return {}

    rating = imdbratings.get_rating(imdb_id)
    if not rating:
        return {}

    return {"ratings": {"imdb": {"rating": rating[0], "votes": rating[1]}}}

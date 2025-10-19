# Copyright (C) 2025, Roman Miroshnychenko aka Roman V.M.
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

import json
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Sequence, List, Tuple, Type

from xbmc import Actor, InfoTagVideo

from .kodi_utils import Settings, KODI_VERSION

InfoType = Dict[str, Any]

CLEAN_PLOT_REPLACEMENTS = (
    ('<b>', '[B]'),
    ('</b>', '[/B]'),
    ('<i>', '[I]'),
    ('</i>', '[/I]'),
    ('</p><p>', '[CR]'),
)
TAG_RE = re.compile(r'<[^>]+>')

IMAGE_SIZES = ('large', 'original', 'medium')


def _clean_plot(plot: str) -> str:
    """Replace HTML tags with Kodi skin tags"""
    for repl in CLEAN_PLOT_REPLACEMENTS:
        plot = plot.replace(repl[0], repl[1])
    plot = TAG_RE.sub('', plot)
    return plot


def extract_artwork_url(resolutions: Dict[str, str]) -> str:
    """Extract image URL from the list of available resolutions"""
    url = ''
    for image_size in IMAGE_SIZES:
        url = resolutions.get(image_size) or ''
        if isinstance(url, dict):
            url = url.get('url') or ''
            if url:
                break
    return url


class BaseInfoTagPropertySetter(ABC):

    def __init__(self,
                 media_info: InfoType,
                 info_tag_method: str,
                 tvmaze_property: Optional[str] = None) -> None:
        self._media_info = media_info
        self._property_value = media_info.get(tvmaze_property)
        self._info_tag_method = info_tag_method

    @abstractmethod
    def should_set(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def set_info_tag_property(self, info_tag: InfoTagVideo) -> None:
        raise NotImplementedError


class SimpleInfoTagPropertySetter(BaseInfoTagPropertySetter):
    """
    Sets a media property from a dictionary returned by TVmaze API to
    xbmc.InfoTagVideo class instance
    """

    def should_set(self) -> bool:
        return bool(self._property_value)

    def get_method_args(self) -> Sequence[Any]:
        return (self._property_value,)

    def set_info_tag_property(self, info_tag: InfoTagVideo) -> None:
        args = self.get_method_args()
        method = getattr(info_tag, self._info_tag_method)
        method(*args)


class PlotSetter(SimpleInfoTagPropertySetter):

    def get_method_args(self) -> Sequence[Any]:
        cleaned_plot = _clean_plot(self._property_value)
        return (cleaned_plot,)


class TvshowMediaTypeSetter(SimpleInfoTagPropertySetter):

    def should_set(self) -> bool:
        return True

    def get_method_args(self) -> Sequence[Any]:
        return ('tvshow',)


class EpisodeMediaTypesSetter(TvshowMediaTypeSetter):

    def get_method_args(self) -> Sequence[Any]:
        return ('episode',)


class EpisodeGuideSetter(SimpleInfoTagPropertySetter):

    def should_set(self) -> bool:
        return True

    def _get_unique_ids(self) -> Dict[str, str]:
        """Extract unique ID in various online databases"""
        if unique_ids := self._media_info.get('unique_ids'):
            return unique_ids
        unique_ids = {'tvmaze': str(self._media_info['id'])}
        externals = self._media_info.get('externals') or {}
        for key, value in externals.items():
            if key == 'thetvdb':
                key = 'tvdb'
            unique_ids[key] = str(value)
        self._media_info['unique_ids'] = unique_ids
        return unique_ids

    def get_method_args(self) -> Sequence[Any]:
        unique_ids = self._get_unique_ids()
        return (json.dumps(unique_ids),)


class ShowUniqueIDsSetter(EpisodeGuideSetter):

    def get_method_args(self) -> Sequence[Any]:
        unique_ids = self._get_unique_ids()
        return unique_ids, 'tvmaze'


class CountrySetter(SimpleInfoTagPropertySetter):

    def should_set(self) -> bool:
        channel = self._media_info.get('network')
        if channel is None:
            channel = self._media_info.get('webChannel')
        if channel is None:
            return False
        country = channel.get('country')
        if not country:
            return False
        return True

    def get_method_args(self) -> Sequence[Any]:
        channel = self._media_info.get('network') or self._media_info.get('webChannel')
        return ([channel['country']['name']],)


class StudioSetter(SimpleInfoTagPropertySetter):

    def should_set(self) -> bool:
        channel = self._media_info.get('network')
        if channel is None:
            channel = self._media_info.get('webChannel')
        if channel is None:
            return False
        return True

    def get_method_args(self) -> Sequence[Any]:
        channel = self._media_info.get('network') or self._media_info.get('webChannel')
        return ([channel['name']],)


class YearSetter(SimpleInfoTagPropertySetter):

    def get_method_args(self) -> Sequence[Any]:
        year = self._property_value[:4]
        return (int(year),)

class PremieredSetter(SimpleInfoTagPropertySetter):

    def get_method_args(self) -> Sequence[Any]:
        return (self._property_value,)


class CreatorsSetter(SimpleInfoTagPropertySetter):

    def should_set(self) -> bool:
        return bool(self._media_info.get('_embedded', {}).get('crew'))

    def _get_credits(self) -> List[str]:
        """Extract show creator(s) from show info"""
        credits_ = []
        for item in self._media_info['_embedded']['crew']:
            if item['type'].lower() == 'creator':
                credits_.append(item['person']['name'])
        return credits_

    def get_method_args(self) -> Sequence[Any]:
        credits_ = self._get_credits()
        return (credits_,)


class CastSetter(SimpleInfoTagPropertySetter):

    def should_set(self) -> bool:
        return True

    def get_method_args(self) -> Sequence[Any]:
        cast = []
        for index, item in enumerate(self._media_info['_embedded']['cast'], 1):
            data = {
                'name': item['person']['name'],
                'role': item['character']['name'],
                'order': index,
            }
            thumb = None
            if item['character'].get('image') is not None:
                thumb = extract_artwork_url(item['character']['image'])
            if not thumb and item['person'].get('image') is not None:
                thumb = extract_artwork_url(item['person']['image'])
            if thumb:
                data['thumbnail'] = thumb
            cast.append(Actor(**data))
        return (cast,)


class ThumbSetter(SimpleInfoTagPropertySetter):

    def get_method_args(self) -> Sequence[Any]:
        image_url = extract_artwork_url(self._property_value)
        return image_url, 'thumb'


class RatingSetter(BaseInfoTagPropertySetter):

    def should_set(self) -> bool:
        return True

    def set_info_tag_property(self, info_tag: InfoTagVideo) -> None:
        set_rating_method = getattr(info_tag, self._info_tag_method)
        imdb_rating = self._media_info.get('imdb_rating')
        default_rating = Settings().get_value_str('default_rating')
        is_imdb_default = default_rating == 'IMDB' and imdb_rating is not None
        if self._property_value is not None and self._property_value['average'] is not None:
            rating = float(self._media_info['rating']['average'])
            set_rating_method(rating, type='tvmaze', isdefault=not is_imdb_default)
        if imdb_rating is not None:
            set_rating_method(imdb_rating['rating'], imdb_rating['votes'], type='imdb',
                       isdefault=is_imdb_default)


class SeasonInfoSetter(BaseInfoTagPropertySetter):

    def should_set(self) -> bool:
        return bool(self._media_info.get('_embedded', {}).get('seasons'))

    def set_info_tag_property(self, info_tag: InfoTagVideo) -> None:
        add_season_method = getattr(info_tag, self._info_tag_method)
        for season in self._media_info['_embedded']['seasons']:
            method_args = [season['number'], season.get('name') or '']
            if KODI_VERSION >= 22:
                season_plot = season.get('summary') or ''
                season_plot = _clean_plot(season_plot)
                method_args.append(season_plot)
            add_season_method(*method_args)
            image = season.get('image')
            if image is not None:
                url = extract_artwork_url(image)
                if url:
                    info_tag.addAvailableArtwork(url, 'poster', season=season['number'])


class DurationSetter(SimpleInfoTagPropertySetter):

    def should_set(self) -> bool:
        return self._property_value is not None

    def get_method_args(self) -> Sequence[Any]:
        return (self._property_value * 60,)


class EpisodeUniqueIDsSetter(SimpleInfoTagPropertySetter):

    def get_method_args(self) -> Sequence[Any]:
        return {'tvmaze': str(self._property_value)}, 'tvmaze'


class OriginalLanguageSetter(SimpleInfoTagPropertySetter):

    def should_set(self) -> bool:
        if KODI_VERSION < 22:
            return False
        return super().should_set()


BASIC_SHOW_MEDIA_PROPERTY_SETTERS: List[
    Tuple[str, Type[BaseInfoTagPropertySetter],  Optional[str]]
] = [
    ('addAvailableArtwork', ThumbSetter, 'image'),
    ('setUniqueIDs', ShowUniqueIDsSetter, None),
]

SHOW_MEDIA_PROPERTY_SETTERS: List[
    Tuple[str, Type[BaseInfoTagPropertySetter],  Optional[str]]
] = [
    ('setPlot', PlotSetter, 'summary'),
    ('setPlotOutline', PlotSetter, 'summary'),
    ('setGenres', SimpleInfoTagPropertySetter, 'genres'),
    ('setTitle', SimpleInfoTagPropertySetter, 'name'),
    ('setTvShowTitle', SimpleInfoTagPropertySetter, 'name'),
    ('setTvShowStatus', SimpleInfoTagPropertySetter, 'status'),
    ('setMediaType', TvshowMediaTypeSetter, None),
    ('setEpisodeGuide', EpisodeGuideSetter, None),
    ('setUniqueIDs', ShowUniqueIDsSetter, None),
    ('setCountries', CountrySetter, None),
    ('setStudios', StudioSetter, None),
    ('setYear', YearSetter, 'premiered'),
    ('setPremiered', PremieredSetter, 'premiered'),
    ('setWriters', CreatorsSetter, None),
    ('setCast', CastSetter, None),
    ('addAvailableArtwork', ThumbSetter, 'image'),
    ('setRating', RatingSetter, 'rating'),
    ('addSeason', SeasonInfoSetter, None),
    ('setOriginalLanguage', OriginalLanguageSetter, 'language'),
]

BASIC_EPISODE_MEDIA_PROPERTY_SETTERS: List[
    Tuple[str, Type[BaseInfoTagPropertySetter],  Optional[str]]
] = [
    ('setTitle', SimpleInfoTagPropertySetter, 'name'),
    ('setSeason', SimpleInfoTagPropertySetter, 'season'),
    ('setEpisode', SimpleInfoTagPropertySetter, 'number'),
    ('setPremiered', PremieredSetter, 'premiered'),
]

EPISODE_MEDIA_PROPERTY_SETTERS: List[
    Tuple[str, Type[BaseInfoTagPropertySetter],  Optional[str]]
] = [
    ('setTitle', SimpleInfoTagPropertySetter, 'name'),
    ('setSeason', SimpleInfoTagPropertySetter, 'season'),
    ('setEpisode', SimpleInfoTagPropertySetter, 'number'),
    ('setMediaType', EpisodeMediaTypesSetter, None),
    ('setFirstAired', SimpleInfoTagPropertySetter, 'airdate'),
    ('setPlot', PlotSetter, 'summary'),
    ('setPlotOutline', PlotSetter, 'summary'),
    ('setDuration', DurationSetter, 'runtime'),
    ('addAvailableArtwork', ThumbSetter, 'image'),
    ('setUniqueIDs', EpisodeUniqueIDsSetter, 'id'),
]

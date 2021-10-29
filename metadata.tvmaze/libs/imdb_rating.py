# coding: utf-8
from __future__ import absolute_import, unicode_literals

import json
import re

import requests

from .utils import logger

try:
    from typing import Text, Dict, Union, Optional  # pylint: disable=unused-import
except ImportError:
    pass

IMDB_TITLE_URL = 'https://www.imdb.com/title/{}/'


def get_imdb_rating(imdb_id):
    # type: (Text) -> Optional[Dict[Text, Union[int, float]]]
    url = IMDB_TITLE_URL.format(imdb_id)
    response = requests.get(url)
    if response.ok:
        ld_json_match = re.search(r'<script type="application/ld\+json">([^<]+?)</script>',
                                  response.text)
        if ld_json_match is not None:
            ld_json = json.loads(ld_json_match.group(1))
            aggregate_rating = ld_json.get('aggregateRating')
            if aggregate_rating:
                rating = aggregate_rating['ratingValue']
                votes = aggregate_rating['ratingCount']
                return {'rating': rating, 'votes': votes}
    logger.debug('Unable to get IMDB rating for ID {}. Status: {}, response: {}'.format(
        imdb_id, response.status_code, response.text))
    return None

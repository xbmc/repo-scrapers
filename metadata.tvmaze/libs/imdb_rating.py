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

import json
import re
from typing import Dict, Union, Optional

from . import simple_requests as requests
from .utils import logger

IMDB_TITLE_URL = 'https://www.imdb.com/title/{}/'


def get_imdb_rating(imdb_id: str) -> Optional[Dict[str, Union[int, float]]]:
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
    logger.debug(f'Unable to get IMDB rating for ID {imdb_id}. '
                 f'Status: {response.status_code}, response: {response.text}')
    return None

# coding: utf-8
#

"""Functions to interact with various web site APIs"""

from __future__ import absolute_import, unicode_literals

import json
from urllib.request import Request, urlopen
from urllib.error import URLError
from urllib.parse import urlencode
from pprint import pformat
from .utils import logger
try:
    from typing import Text, Optional, Union, List, Dict, Any  # pylint: disable=unused-import
    InfoType = Dict[Text, Any]  # pylint: disable=invalid-name
except ImportError:
    pass

HEADERS = {}


def set_headers(headers):
    # type: (Dict) -> None
    HEADERS.update(headers)


def load_info(url, params=None, default=None, resp_type='json', verboselog=False):
    # type: (Text, Dict, Text, Text, bool) -> Optional[Text]
    """
    Load info from external api

    :param url: API endpoint URL
    :param params: URL query params
    :default: object to return if there is an error
    :resp_type: what to return to the calling function
    :return: API response or default on error
    """
    if params:
        url = url + '?' + urlencode(params)
    logger.debug('Calling URL "{}"'.format(url))
    req = Request(url, headers=HEADERS)
    try:
        response = urlopen(req)
    except URLError as e:
        if hasattr(e, 'reason'):
            logger.debug(
                'failed to reach the remote site\nReason: {}'.format(e.reason))
        elif hasattr(e, 'code'):
            logger.debug(
                'remote site unable to fulfill the request\nError code: {}'.format(e.code))
        response = None
    if response is None:
        resp = default
    elif resp_type.lower() == 'json':
        try:
            resp = json.loads(response.read().decode('utf-8'))
        except json.decoder.JSONDecodeError:
            logger.debug('remote site sent back bad JSON')
            resp = default
    else:
        resp = response.read().decode('utf-8')
    if verboselog:
        logger.debug('the api response:\n{}'.format(pformat(resp)))
    return resp

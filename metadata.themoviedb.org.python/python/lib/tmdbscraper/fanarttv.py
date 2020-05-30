import requests
from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout, RequestException
try:
    from urllib import quote
except ImportError: # py2 / py3
    from urllib.parse import quote

API_KEY = '384afe262ee0962545a752ff340e3ce4'
API_URL = 'https://webservice.fanart.tv/v3/movies/{}'

ARTMAP = {
    'movielogo': 'clearlogo',
    'hdmovielogo': 'clearlogo',
    'hdmovieclearart': 'clearart',
    'movieart': 'clearart',
    'moviedisc': 'discart',
    'moviebanner': 'banner',
    'moviethumb': 'landscape',
    'moviebackground': 'fanart',
    'movieposter': 'poster'
}

def get_details(uniqueids, clientkey, language, set_tmdbid):
    media_id = _get_mediaid(uniqueids)
    if not media_id:
        return {}

    movie_data = _get_data(media_id, clientkey)
    movieset_data = _get_data(set_tmdbid, clientkey)
    if not movie_data and not movieset_data:
        return {}

    movie_art = {}
    movieset_art = {}
    if movie_data:
        movie_art = _parse_data(movie_data, language)
    if movieset_data:
        movieset_art = _parse_data(movieset_data, language)
        movieset_art = {'set.' + key: value for key, value in movieset_art.items()}

    available_art = movie_art
    available_art.update(movieset_art)

    return {'available_art': available_art}

def _get_mediaid(uniqueids):
    for source in ('tmdb', 'imdb', 'unknown'):
        if source in uniqueids:
            return uniqueids[source]

def _get_data(media_id, clientkey):
    headers = {'api-key': API_KEY}
    if clientkey:
        headers['client-key'] = clientkey

    try:
        response = requests.get(API_URL.format(media_id), headers=headers)
    except (Timeout, RequestsConnectionError, RequestException) as ex:
        return _format_error_message(ex)

    if not response or not response.status_code == 200:
        return None

    return response.json()

def _format_error_message(ex):
    message = type(ex).__name__
    if hasattr(ex, 'message'):
        message += ": {0}".format(ex.message)
    return {'error': message}

def _parse_data(data, language):
    result = {}
    for arttype, artlist in data.items():
        if arttype not in ARTMAP:
            continue
        for image in artlist:
            image_lang = _get_imagelanguage(arttype, image)
            if image_lang and image_lang != language:
                continue

            generaltype = ARTMAP[arttype]
            if generaltype == 'poster' and not image_lang:
                generaltype = 'keyart'
            if artlist and generaltype not in result:
                result[generaltype] = []

            url = quote(image['url'], safe="%/:=&?~#+!$,;'@()*[]")
            resultimage = {'url': url, 'preview': url.replace('.fanart.tv/fanart/', '.fanart.tv/preview/')}
            result[generaltype].append(resultimage)

    return result

def _get_imagelanguage(arttype, image):
    if 'lang' not in image or arttype == 'moviebackground':
        return None
    if arttype in ('movielogo', 'hdmovielogo', 'hdmovieclearart', 'movieart', 'moviebanner',
            'moviethumb', 'moviedisc'):
        return image['lang'] if image['lang'] not in ('', '00') else 'en'
    # movieposter may or may not have a title and thus need a language
    return image['lang'] if image['lang'] not in ('', '00') else None

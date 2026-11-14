# -*- coding: utf-8 -*-

def musicbrainz_artistfind(data, artist):
    artists = []
    for item in data.get('artists',[]):
        artistdata = {}
        artistdata['artist'] = item['name']
        artistdata['thumb'] = ''
        artistdata['genre'] = ''
        artistdata['born'] = item['life-span'].get('begin', '')
        if 'type' in item:
            artistdata['type'] = item['type']
        if 'gender' in item:
            artistdata['gender'] = item['gender']
        if 'disambiguation' in item:
            artistdata['disambiguation'] = item['disambiguation']
        artistdata['mbartistid'] = item['id']
        if item.get('score',1):
            artistdata['relevance'] = str(item['score'] / 100.00)
        artists.append(artistdata)
    return artists

def musicbrainz_artistdetails(data, locale=None):
    artistdata = {}
    artistdata['artist'] = data['name']
    artistdata['primary'] = data['name']

    if locale:
        requested = locale.replace('-', '_').lower()
        language = requested.split('_', 1)[0]
        aliases = [a for a in data.get('aliases', []) if a.get('type') == 'Artist name']

        candidates = []
        # prefer exact locale, then language, then regional variant
        for match in (lambda v: v == requested, lambda v: v == language, lambda v: v.startswith(language + '_')):
            candidates = [a for a in aliases if a.get('locale') and match(a['locale'].replace('-', '_').lower())]
            if candidates:
                break
        if candidates:
            candidates.sort(key=lambda a: (not bool(a.get('sort-name')), not bool(a.get('primary')), -len(a['name'])))
            alias = candidates[0]
            # prefer the primary MusicBrainz alias if none other found
            artistdata['artist'] = alias['name']
            if alias.get('sort-name'):
                artistdata['sortname'] = alias['sort-name']

    artistdata['mbartistid'] = data['id']
    if 'sort-name' in data:
        artistdata['sortname'] = data['sort-name']
    artistdata['type'] = data['type']
    artistdata['gender'] = data['gender']
    artistdata['disambiguation'] = data['disambiguation']
    if data.get('life-span','') and data.get('type',''):
        begin = data['life-span'].get('begin', '')
        end = data['life-span'].get('end', '')
        if data['type'] in ['Group', 'Orchestra', 'Choir']:
            artistdata['formed'] = begin
            artistdata['disbanded'] = end
        elif data['type'] in ['Person', 'Character']:
            artistdata['born'] = begin
            artistdata['died'] = end
    albums = []
    for item in data.get('release-groups',[]):
        albumdata = {}
        albumdata['title'] = item.get('title','')
        albumdata['year'] = item.get('first-release-date','')
        albumdata['musicbrainzreleasegroupid'] = item.get('id','')
        albums.append(albumdata)
    if albums:
        artistdata['albums'] = albums
    for item in data['relations']:
        if item['type'] == 'allmusic':
            artistdata['allmusic'] = item['url']['resource']
        elif item['type'] == 'discogs':
            dataid = item['url']['resource'].rsplit('/', 1)[1]
            artistdata['discogs'] = dataid
        elif item['type'] == 'wikidata':
            dataid = item['url']['resource'].rsplit('/', 1)[1]
            artistdata['wikidata'] = dataid
        elif item['type'] == 'wikipedia':
            dataid = item['url']['resource'].rsplit('/', 1)[1]
            artistdata['wikipedia'] = dataid
    return artistdata

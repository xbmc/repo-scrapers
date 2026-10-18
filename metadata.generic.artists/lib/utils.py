# -*- coding: utf-8 -*-

AUDIODBKEY = '95424d43204d6564696538'
AUDIODBURL = 'https://www.theaudiodb.com/api/v1/json/%s/%s'
AUDIODBSEARCH = 'search.php?s=%s'
AUDIODBDETAILS = 'artist-mb.php?i=%s'
AUDIODBDISCOGRAPHY = 'discography-mb.php?s=%s'
AUDIODBMVIDS = 'mvid-mb.php?i=%s'

MUSICBRAINZURL = 'https://musicbrainz.org/ws/2/artist/%s'
MUSICBRAINZSEARCH = '?query="%s"&fmt=json'
MUSICBRAINZDETAILS = '%s?inc=url-rels+release-groups+aliases&type=album&fmt=json'

DISCOGSURL = 'https://api.discogs.com/%s'
DISCOGSSEARCH = 'database/search?q=%s&type=artist&token=%s'
DISCOGSDETAILS = 'artists/%s?token=%s'
DISCOGSDISCOGRAPHY = 'artists/%s/releases?sort=format&page=1&per_page=100&token=%s'

ALLMUSICURL = 'https://www.allmusic.com/search/artists/%s'

FANARTVKEY = '88ca41db0d6878929f1f9771eade41fd'
FANARTVURL = 'https://webservice.fanart.tv/v3/music/%s?api_key=%s'

WIKIDATAURL = 'https://www.wikidata.org/wiki/Special:EntityData/%s.json'
WIKIPEDIAURL = 'https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&titles=%s&formatversion=2&exsentences=10&exlimit=1&explaintext=1'

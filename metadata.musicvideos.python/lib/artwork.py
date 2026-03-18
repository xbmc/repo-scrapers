# SPDX-License-Identifier: GPL-3.0-or-later

"""Artwork collection and output."""

from lib.api.audiodb import get_track_screenshots

# MySQL TEXT = 65,535 bytes; margin for safety
_C01_BUDGET = 60000


def set_artwork(vtag, track_data, artist_artwork, fanarttv_artwork):
    """Collect artwork from all sources and add to the listitem."""
    fanart = []
    c01 = []

    for url, preview in get_track_screenshots(track_data):
        c01.append(('thumb', url, preview))

    # Fanart.tv first — higher quality, community-curated
    if fanarttv_artwork:
        for art_type, items in fanarttv_artwork.items():
            for url, preview, _ in items:
                if art_type == 'fanart':
                    fanart.append(url)
                else:
                    c01.append((art_type, url, preview))

    if artist_artwork:
        for art_type, items in artist_artwork.items():
            for url, preview in items:
                if art_type == 'fanart':
                    fanart.append(url)
                else:
                    c01.append((art_type, url, preview))

    # Fanart has no column storage for musicvideos, no limit needed
    if fanart:
        vtag.setAvailableFanart([{'image': url} for url in fanart])

    used = 0
    for art_type, url, preview in c01:
        cost = _byte_cost(art_type, url, preview)
        if used + cost > _C01_BUDGET:
            break
        vtag.addAvailableArtwork(url, arttype=art_type, preview=preview)
        used += cost


def _byte_cost(art_type, url, preview):
    """Estimate XML byte cost of one artwork entry in the database."""
    # Kodi serializes as: <thumb spoof="" cache="" aspect="TYPE" preview="PREVIEW">URL</thumb>
    return 52 + len(art_type) + len(preview) + len(url)

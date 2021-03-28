import pytest
from .imdb_rating import get_imdb_rating_and_votes

@pytest.mark.vcr()
def test_get_imdb_rating_and_votes():
    imdb_rating = get_imdb_rating_and_votes('tt2098220')
    assert imdb_rating['rating'] == 8.9
    assert imdb_rating['votes'] == 45354
import bet_explorer.homepage_paths as bet_home
from bs4 import BeautifulSoup

from .constant_variables import MOCK_PATH

EXTRACT_PATH = MOCK_PATH / "extract_hyperlinks_mock.html"
HOMEPAGE_PATH = MOCK_PATH / "homepage_mock.html"


def test_extract_hyperlink():
    with open(EXTRACT_PATH, "r") as mock_file:
        mock_soup = BeautifulSoup(mock_file, "html.parser")

    paths = bet_home._extract_hyperlink_paths_from_homepage(mock_soup)

    assert len(paths) == 2
    assert all(href_mock in paths for href_mock in ["CorrectOne", "CorrectTwo"])


def test_filter_desired_sports():
    sports = {"soccer", "handball"}
    suffixes_mock = ["/soccer/ok/", "/handball/ok/", "/volleyball/not_ok"]

    filtered_suffixes = bet_home._filter_only_desired_sports(suffixes_mock, sports)

    assert len(filtered_suffixes) == 2
    assert all(
        suffix in filtered_suffixes for suffix in ["/soccer/ok/", "/handball/ok/"]
    )


def test_get_tournament_paths():
    sports = {"soccer", "handball"}

    with open(HOMEPAGE_PATH, "r") as mock_file:
        mock_soup = BeautifulSoup(mock_file, "html.parser")

    paths = bet_home._get_tournament_url_paths_from_homepage(mock_soup, sports)

    assert len(paths) == 3
    assert all(
        href_mock in paths
        for href_mock in [
            "/handball/tourney1/ok",
            "/handball/tourney2/ok",
            "/soccer/tourney1/ok",
        ]
    )

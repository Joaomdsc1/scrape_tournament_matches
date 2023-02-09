import pytest
import bet_explorer.scrape.scrape_matches as scp
from bs4 import BeautifulSoup

from .constant_variables import MOCK_PATH

EMPTY_QUERY_PATH = MOCK_PATH / "empty_main_query_mock.html"
QUERY_PATH = MOCK_PATH / "main_query_mock.html"


MATCHES_PATH = MOCK_PATH / "matches_webpage_mock.html"
GROUP_PATH = MOCK_PATH / "group_webpage_mock.html"
NO_HEADER_PATH = MOCK_PATH / "no_header_webpage_mock.html"


@pytest.fixture(scope="function")
def matches_mock():
    with open(MATCHES_PATH, "r") as mock:
        soup = BeautifulSoup(mock, "html.parser")
    return soup


@pytest.fixture(scope="function")
def group_mock():
    with open(GROUP_PATH, "r") as mock:
        soup = BeautifulSoup(mock, "html.parser")
    return soup


@pytest.fixture(scope="function")
def no_header_mock():
    with open(NO_HEADER_PATH, "r") as mock:
        soup = BeautifulSoup(mock, "html.parser")
    return soup


@pytest.fixture(scope="function")
def empty_query_mock():
    with open(EMPTY_QUERY_PATH, "r") as mock:
        soup = BeautifulSoup(mock, "html.parser")
    return soup


@pytest.fixture(scope="function")
def query_mock():
    with open(QUERY_PATH, "r") as mock:
        soup = BeautifulSoup(mock, "html.parser")
    return soup


def test_concatenate_results():
    for string in ["", "path/", "betexplorer.com/sport/country/name-year/"]:
        assert scp._concatenate_results_slash(string) == f"{string}results/"


def test_main_query(empty_query_mock, query_mock):
    assert scp._get_main_section_query(empty_query_mock) == ""
    assert scp._get_main_section_query(query_mock) == "?stage=main&month=all"


def test_date_formatting():
    day = "Today"
    for date in [day, f"0.29{day}", f"random{day}txt"]:
        assert scp._format_date_correctly(date) == date.replace(day, scp.TODAY)

    day = "Yesterday"
    for date in [day, f"0.29{day}", f"random{day}txt"]:
        assert scp._format_date_correctly(date) == date.replace(day, scp.YESTERDAY)

    for date in ["20.3.", "10.12.", "02.8.", "15.5."]:
        assert scp._format_date_correctly(date) == f"{date}{scp.CURRENT_YEAR}"

    for date in ["20.3.04", "10.12.14", "02.8.24", "15.5.04"]:
        assert scp._format_date_correctly(date) == date


def test_has_groups(matches_mock, group_mock, no_header_mock):
    assert scp._has_groups(group_mock)
    assert not scp._has_groups(matches_mock)
    assert not scp._has_groups(no_header_mock)


def test_ignore_tournament(matches_mock, group_mock, no_header_mock):
    assert scp._should_ignore_tournament(None)
    assert scp._should_ignore_tournament(group_mock)
    assert not scp._should_ignore_tournament(matches_mock)
    assert not scp._should_ignore_tournament(no_header_mock)


def test_is_not_header(matches_mock, no_header_mock):
    trs = matches_mock.find_all("tr")
    expected = [False, True, True, False, True, True]
    for tr, answer in zip(trs, expected):
        assert scp._is_not_header(tr) == answer

    trs = no_header_mock.find_all("tr")
    expected = [True, True]
    for tr, answer in zip(trs, expected):
        assert scp._is_not_header(tr) == answer


def test_get_rows_from_html_table(no_header_mock):
    match_rows = scp._get_rows_from_html_table(no_header_mock)

    assert len(match_rows) == 2
    assert "TeamA" in match_rows[0].find("td").text
    assert "TeamB" in match_rows[0].find("td").text
    assert "match1" in match_rows[0].find("td").a["href"]

    assert "TeamB" in match_rows[1].find("td").text
    assert "TeamC" in match_rows[1].find("td").text
    assert "match2" in match_rows[1].find("td").a["href"]


def test_get_teams_result_date(no_header_mock):
    match_rows = no_header_mock.find_all("tr")

    assert scp._get_teams_result_date(match_rows[0]) == [
        "TeamA - TeamB",
        "0:1",
        scp.TODAY,
    ]
    assert scp._get_teams_result_date(match_rows[1]) == [
        "TeamB - TeamC",
        "0:0",
        scp.YESTERDAY,
    ]


def test_get_all_odds(no_header_mock):
    match_rows = no_header_mock.find_all("tr")

    assert scp._get_all_odds(match_rows[0]) == [10.12, 6.97, 1.17]
    assert scp._get_all_odds(match_rows[1]) == []


def test_extract_all_information(no_header_mock):
    match_rows = no_header_mock.find_all("tr")

    teams, result, date, *odds = scp._extract_teams_result_date_odds(match_rows[0])
    assert teams == "TeamA - TeamB"
    assert result == "0:1"
    assert date == scp.TODAY
    assert odds == [10.12, 6.97, 1.17]

    teams, result, date, *odds = scp._extract_teams_result_date_odds(match_rows[1])
    assert teams == "TeamB - TeamC"
    assert result == "0:0"
    assert date == scp.YESTERDAY
    assert odds == []


def test_web_scrape(matches_mock):
    matches: list[list[str, float]] = scp._web_scrape_matches_information_from_soup(
        matches_mock
    )

    teams, result, date, *odds = matches[0]
    assert teams == "TeamA - TeamB"
    assert result == "0:1"
    assert date == scp.TODAY
    assert odds == [10.12, 6.97, 1.17]

    teams, result, date, *odds = matches[1]
    assert teams == "TeamB - TeamC"
    assert result == "0:0"
    assert date == scp.YESTERDAY
    assert odds == []

    teams, result, date, *odds = matches[2]
    assert teams == "TeamC - TeamA"
    assert result == "4:0"
    assert date == f"31.07.{scp.CURRENT_YEAR}"
    assert odds == [1.53, 4.86, 4.03]

    teams, result, date, *odds = matches[3]
    assert teams == "TeamB - TeamA"
    assert result == "0:5"
    assert date == "01.07.1995"
    assert odds == [1.51, 4.76, 4.13]

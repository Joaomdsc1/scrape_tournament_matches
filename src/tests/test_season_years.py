import pytest
import bet_explorer.scrape.season_years as sea
from bs4 import BeautifulSoup

from .constant_variables import MOCK_PATH

ONE_YEAR_PATH = MOCK_PATH / "one_year_dropdown_mock.html"
TWO_YEAR_PATH = MOCK_PATH / "two_year_dropdown_mock.html"


@pytest.fixture(scope="function")
def one_year_mock():
    with open(ONE_YEAR_PATH, "r") as mock:
        soup = BeautifulSoup(mock, "html.parser")
    return soup


@pytest.fixture(scope="function")
def two_year_mock():
    with open(TWO_YEAR_PATH, "r") as mock:
        soup = BeautifulSoup(mock, "html.parser")
    return soup


def test_default_path_with_year(one_year_mock):
    options = one_year_mock.find_all("option")

    assert (
        sea._create_default_path_with_year(options[0])
        == "/sport/country/name3-2024-2024/"
    )
    assert (
        sea._create_default_path_with_year(options[2]) == "/sport/country/name3-2022/"
    )
    assert (
        sea._create_default_path_with_year(options[-1])
        == "/sport/country/name1-1998-1998/"
    )


def test_extract_path_season_from_dropdown_options(one_year_mock):
    options = one_year_mock.find_all("option")

    assert sea._extract_path_season_from_dropdown_options(options[:3]) == [
        "/sport/country/name3-2024/",
        "/sport/country/name3-2023/",
        "/sport/country/name3-2022/",
    ]

    assert sea._extract_path_season_from_dropdown_options(options[-3:]) == [
        "/sport/country/name1-2000/",
        "/sport/country/name1-1999/",
        "/sport/country/name1-1998/",
    ]

    assert sea._extract_path_season_from_dropdown_options(options[7:10]) == [
        "/sport/country/name3-2017/",
        "/sport/country/name2-2016/",
        "/sport/country/name2-2015/",
    ]


def test_get_path_season_from_webpage(one_year_mock):
    assert sea._get_path_seasons_from_webpage(one_year_mock) == [
        "/sport/country/name3-2024/",
        "/sport/country/name3-2023/",
        "/sport/country/name3-2022/",
        "/sport/country/name3-2021/",
        "/sport/country/name3-2020/",
        "/sport/country/name3-2019/",
        "/sport/country/name3-2018/",
        "/sport/country/name3-2017/",
        "/sport/country/name2-2016/",
        "/sport/country/name2-2015/",
        "/sport/country/name2-2014/",
        "/sport/country/name2-2013/",
        "/sport/country/name1-2012/",
        "/sport/country/name1-2011/",
        "/sport/country/name1-2010/",
        "/sport/country/name1-2009/",
        "/sport/country/name1-2008/",
        "/sport/country/name1-2007/",
        "/sport/country/name1-2006/",
        "/sport/country/name1-2005/",
        "/sport/country/name1-2004/",
        "/sport/country/name1-2003/",
        "/sport/country/name1-2002/",
        "/sport/country/name1-2001/",
        "/sport/country/name1-2000/",
        "/sport/country/name1-1999/",
        "/sport/country/name1-1998/",
    ]


def test_create_all_desired_seasons_one_year():
    assert sea._create_all_desired_seasons_one_year("2015", "2018") == [
        "2015",
        "2016",
        "2017",
        "2018",
    ]

    assert sea._create_all_desired_seasons_one_year("1999", "2001") == [
        "1999",
        "2000",
        "2001",
    ]


def test_create_all_desired_seasons_two_years():
    assert sea._create_all_desired_seasons_two_years("2015-2016", "2018-2019") == [
        "2015-2016",
        "2016-2017",
        "2017-2018",
        "2018-2019",
    ]

    assert sea._create_all_desired_seasons_two_years("1999-2000", "2001-2002") == [
        "1999-2000",
        "2000-2001",
        "2001-2002",
    ]


def test_find_index_first_desired_seasons_in_paths__one_year():
    season_paths = [
        "/sport/country/name2-2014/",
        "/sport/country/name2-2013/",
        "/sport/country/name1-2012/",
    ]

    desired_seasons = ["2012", "2011"]
    sea._find_index_first_desired_seasons_in_paths(season_paths, desired_seasons) == 2

    desired_seasons = ["2011", "2012"]
    sea._find_index_first_desired_seasons_in_paths(season_paths, desired_seasons) == 2

    desired_seasons = ["2013", "2014"]
    sea._find_index_first_desired_seasons_in_paths(season_paths, desired_seasons) == 1

    desired_seasons = ["2010", "2011"]
    sea._find_index_first_desired_seasons_in_paths(
        season_paths, desired_seasons
    ) is None


def test_find_index_first_desired_seasons_in_paths__two_year():
    season_paths = [
        "/sport/country/name2-2014-2015/",
        "/sport/country/name2-2013-2014/",
        "/sport/country/name1-2012-2013/",
    ]

    desired_seasons = ["2012-2013", "2011-2012"]
    sea._find_index_first_desired_seasons_in_paths(season_paths, desired_seasons) == 2

    desired_seasons = ["2011-2012", "2012-2013"]
    sea._find_index_first_desired_seasons_in_paths(season_paths, desired_seasons) == 2

    desired_seasons = ["2013-2014", "2014-2015"]
    sea._find_index_first_desired_seasons_in_paths(season_paths, desired_seasons) == 1

    desired_seasons = ["2010-2011", "2011-2012"]
    sea._find_index_first_desired_seasons_in_paths(
        season_paths, desired_seasons
    ) is None


def test_find_first_index__one_year():
    season_paths = [
        "/sport/country/name2-2014/",
        "/sport/country/name2-2013/",
        "/sport/country/name1-2012/",
    ]

    desired_one = ["2012", "2011"]
    desired_two = ["2012-2013", "2011-2012"]
    sea._find_first_index(season_paths, desired_one, desired_two) == 2

    desired_one = ["2011", "2012"]
    desired_two = ["2011-2012", "2012-2013"]
    sea._find_first_index(season_paths, desired_one, desired_two) == 2

    desired_one = ["2013", "2014"]
    desired_two = ["2013-2015", "2014-2015"]
    sea._find_first_index(season_paths, desired_one, desired_two) == 1

    desired_one = ["2010", "2011"]
    desired_two = ["2010-2011", "2011-2012"]
    sea._find_first_index(season_paths, desired_one, desired_two) is None


def test_find_first_index__two_year():
    season_paths = [
        "/sport/country/name2-2014-2015/",
        "/sport/country/name2-2013-2014/",
        "/sport/country/name1-2012-2013/",
    ]

    desired_one = ["2012", "2011"]
    desired_two = ["2012-2013", "2011-2012"]
    sea._find_first_index(season_paths, desired_one, desired_two) == 2

    desired_one = ["2011", "2012"]
    desired_two = ["2011-2012", "2012-2013"]
    sea._find_first_index(season_paths, desired_one, desired_two) == 2

    desired_one = ["2013", "2014"]
    desired_two = ["2013-2015", "2014-2015"]
    sea._find_first_index(season_paths, desired_one, desired_two) == 1

    desired_one = ["2010", "2011"]
    desired_two = ["2010-2011", "2011-2012"]
    sea._find_first_index(season_paths, desired_one, desired_two) is None


def test_find_last_index__one_year():
    season_paths = [
        "/sport/country/name2-2014/",
        "/sport/country/name2-2013/",
        "/sport/country/name1-2012/",
    ]

    desired_one = ["2012", "2011"]
    desired_two = ["2012-2013", "2011-2012"]
    sea._find_last_index(season_paths, desired_one, desired_two) == 1

    desired_one = ["2011", "2012"]
    desired_two = ["2011-2012", "2012-2013"]
    sea._find_last_index(season_paths, desired_one, desired_two) == 2

    desired_one = ["2013", "2014"]
    desired_two = ["2013-2015", "2014-2015"]
    sea._find_last_index(season_paths, desired_one, desired_two) == 0

    desired_one = ["2010", "2011"]
    desired_two = ["2010-2011", "2011-2012"]
    sea._find_last_index(season_paths, desired_one, desired_two) is None


def test_find_last_index__two_year():
    season_paths = [
        "/sport/country/name2-2014-2015/",
        "/sport/country/name2-2013-2014/",
        "/sport/country/name1-2012-2013/",
    ]

    desired_one = ["2012", "2011"]
    desired_two = ["2012-2013", "2011-2012"]
    sea._find_last_index(season_paths, desired_one, desired_two) == 1

    desired_one = ["2011", "2012"]
    desired_two = ["2011-2012", "2012-2013"]
    sea._find_last_index(season_paths, desired_one, desired_two) == 2

    desired_one = ["2013", "2014"]
    desired_two = ["2013-2015", "2014-2015"]
    sea._find_last_index(season_paths, desired_one, desired_two) == 0

    desired_one = ["2010", "2011"]
    desired_two = ["2010-2011", "2011-2012"]
    sea._find_last_index(season_paths, desired_one, desired_two) is None


def test_filter_season_between_first_and_last__wrong_years(one_year_mock):
    season_paths = [
        "/sport/country/name2-2012/",
        "/sport/country/name2-2013/",
        "/sport/country/name2-2014/",
        "/sport/country/name2-2015/",
        "/sport/country/name2-2016/",
    ]

    assert (
        sea._filter_season_between_first_and_last(
            season_paths, ["00000", "0000"], ["11111", "11111"]
        )
        == []
    )


def test_filter_season_between_first_and_last__one_year():
    season_paths = [
        "/sport/country/name2-2016/",
        "/sport/country/name2-2015/",
        "/sport/country/name2-2014/",
        "/sport/country/name2-2013/",
        "/sport/country/name2-2012/",
    ]

    expected = [
        "/sport/country/name2-2015/",
        "/sport/country/name2-2014/",
        "/sport/country/name2-2013/",
    ]

    assert (
        sea._filter_season_between_first_and_last(
            season_paths, ["2013", "2013-2014"], ["2015", "2015-2016"]
        )
        == expected
    )

    expected = [
        "/sport/country/name2-2015/",
        "/sport/country/name2-2014/",
        "/sport/country/name2-2013/",
        "/sport/country/name2-2012/",
    ]

    assert (
        sea._filter_season_between_first_and_last(
            season_paths, ["2010", "2010-2011"], ["2015", "2015-2016"]
        )
        == expected
    )

    expected = [
        "/sport/country/name2-2016/",
        "/sport/country/name2-2015/",
        "/sport/country/name2-2014/",
        "/sport/country/name2-2013/",
    ]

    assert (
        sea._filter_season_between_first_and_last(
            season_paths, ["2013", "2013-2014"], ["2017", "2017-2018"]
        )
        == expected
    )

    expected = [
        "/sport/country/name2-2016/",
        "/sport/country/name2-2015/",
        "/sport/country/name2-2014/",
        "/sport/country/name2-2013/",
        "/sport/country/name2-2012/",
    ]

    assert (
        sea._filter_season_between_first_and_last(
            season_paths, ["2010", "2010-2011"], ["2017", "2017-2018"]
        )
        == expected
    )


def test_filter_season_between_first_and_last__two_year():
    season_paths = [
        "/sport/country/name2-2016-2017/",
        "/sport/country/name2-2015-2016/",
        "/sport/country/name2-2014-2015/",
        "/sport/country/name2-2013-2014/",
        "/sport/country/name2-2012-2013/",
    ]

    expected = [
        "/sport/country/name2-2015-2016/",
        "/sport/country/name2-2014-2015/",
        "/sport/country/name2-2013-2014/",
    ]

    assert (
        sea._filter_season_between_first_and_last(
            season_paths, ["2013", "2013-2014"], ["2015", "2015-2016"]
        )
        == expected
    )

    expected = [
        "/sport/country/name2-2015-2016/",
        "/sport/country/name2-2014-2015/",
        "/sport/country/name2-2013-2014/",
        "/sport/country/name2-2012-2013/",
    ]

    assert (
        sea._filter_season_between_first_and_last(
            season_paths, ["2010", "2010-2011"], ["2015", "2015-2016"]
        )
        == expected
    )

    expected = [
        "/sport/country/name2-2016-2017/",
        "/sport/country/name2-2015-2016/",
        "/sport/country/name2-2014-2015/",
        "/sport/country/name2-2013-2014/",
    ]

    assert (
        sea._filter_season_between_first_and_last(
            season_paths, ["2013", "2013-2014"], ["2017", "2017-2018"]
        )
        == expected
    )

    expected = [
        "/sport/country/name2-2016-2017/",
        "/sport/country/name2-2015-2016/",
        "/sport/country/name2-2014-2015/",
        "/sport/country/name2-2013-2014/",
        "/sport/country/name2-2012-2013/",
    ]

    assert (
        sea._filter_season_between_first_and_last(
            season_paths, ["2010", "2010-2011"], ["2017", "2017-2018"]
        )
        == expected
    )


def test_get_path_to_desired_seasons__one_year(one_year_mock):
    expected = [
        "/sport/country/name3-2018/",
        "/sport/country/name3-2017/",
        "/sport/country/name2-2016/",
        "/sport/country/name2-2015/",
        "/sport/country/name2-2014/",
        "/sport/country/name2-2013/",
    ]

    assert (
        sea._get_path_to_desired_seasons_from_soup(
            one_year_mock, ["2013", "2013-2014"], ["2018", "2015-2016"]
        )
        == expected
    )


def test_get_path_to_desired_seasons__two_years(two_year_mock):
    expected = [
        "/sport/country/name2-2018-2019/",
        "/sport/country/name2-2017-2018/",
        "/sport/country/name2-2016-2017/",
        "/sport/country/name1-2015-2016/",
        "/sport/country/name1-2014-2015/",
        "/sport/country/name1-2013-2014/",
    ]

    assert (
        sea._get_path_to_desired_seasons_from_soup(
            two_year_mock, ["2013", "2013-2014"], ["2018", "2018-2019"]
        )
        == expected
    )

    expected = ["/sport/country/name2-2022-2023/"]

    assert (
        sea._get_path_to_desired_seasons_from_soup(
            two_year_mock, ["2013", "2022-2023"], ["2018", "2022-2023"]
        )
        == expected
    )

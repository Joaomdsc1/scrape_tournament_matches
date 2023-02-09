import logging
import re
from typing import Optional, Pattern

import requests
from bs4 import BeautifulSoup, ResultSet, Tag

from logs import log

from ..utils import concatenate_homepage_url_to_path, run_three_times


def _create_default_path_with_year(season: Tag):
    # default season["value"] is like /sport/country/name/
    path_no_last_slash: str = season["value"][:-1]
    season_year: str = season.text.strip().replace("/", "-")

    return path_no_last_slash + "-" + season_year + "/"


def _extract_path_season_from_dropdown_options(
    dropdown_options: ResultSet,
) -> list[str]:
    # each tournament has a default path without any year after, that is,
    # like /sport/country/name/ rather than /sport/country/name-season/
    # and only this default path will have the "selected" attribute
    return [
        season["value"]
        if not season.has_attr("selected")
        else _create_default_path_with_year(season)
        for season in dropdown_options
    ]


def _get_path_seasons_from_webpage(tourney_soup: BeautifulSoup) -> list[str]:
    year_dropdown_menu: Tag = tourney_soup.find(
        "div", attrs={"class": "wrap-section__header__select"}
    )

    if year_dropdown_menu is None:
        return []

    # path to each season is stored in the "value" attribute inside each option
    any_char_re: Pattern[str] = re.compile(".*")
    dropdown_options: ResultSet = year_dropdown_menu.find_all(
        "option", attrs={"value": any_char_re}
    )

    return _extract_path_season_from_dropdown_options(dropdown_options)


def _create_all_desired_seasons_one_year(
    first_season: str, last_season: str
) -> list[str]:
    first_year: int = int(first_season)
    last_year: int = int(last_season) + 1

    return [f"{year}" for year in range(first_year, last_year)]


def _create_all_desired_seasons_two_years(
    first_season: str, last_season: str
) -> list[str]:
    both_years_first_season: list[str, str] = first_season.split("-")
    both_years_last_season: list[str, str] = last_season.split("-")

    first_year: int = int(both_years_first_season[0])
    last_year: int = int(both_years_last_season[0]) + 1

    return [f"{year}-{year + 1}" for year in range(first_year, last_year)]


def _find_index_first_desired_seasons_in_paths(
    season_paths: list[str], desired_seasons: list[str]
) -> Optional[int]:
    for season in desired_seasons:
        for i, year in enumerate(season_paths):
            if season in year:
                return i

    return None


def _find_first_index(
    season_paths: list[str], desired_one: list[str], desired_two: list[str]
) -> Optional[int]:
    two_year_index = _find_index_first_desired_seasons_in_paths(
        season_paths, desired_two
    )

    one_year_index = _find_index_first_desired_seasons_in_paths(
        season_paths, desired_one
    )

    if two_year_index is not None:
        return two_year_index

    if one_year_index is not None:
        return one_year_index

    return None


def _find_last_index(
    season_paths: list[str], desired_one: list[str], desired_two: list[str]
) -> Optional[int]:
    two_year_index = _find_index_first_desired_seasons_in_paths(
        season_paths, reversed(desired_two)
    )

    one_year_index = _find_index_first_desired_seasons_in_paths(
        season_paths, reversed(desired_one)
    )

    if two_year_index is not None:
        return two_year_index

    if one_year_index is not None:
        return one_year_index

    return None


def _filter_season_between_first_and_last(
    season_paths: list[str], first_season: tuple[str, str], last_season: tuple[str, str]
) -> list[str]:
    first_one_year, first_two_year = first_season
    last_one_year, last_two_year = last_season

    desired_one: list[str] = _create_all_desired_seasons_one_year(
        first_one_year, last_one_year
    )
    desired_two: list[str] = _create_all_desired_seasons_two_years(
        first_two_year, last_two_year
    )

    first_season_index: int = _find_first_index(season_paths, desired_one, desired_two)
    last_season_index: int = _find_last_index(season_paths, desired_one, desired_two)

    if first_season_index is None or last_season_index is None:
        return []

    # season years are in decreasing order
    return season_paths[last_season_index : first_season_index + 1]


def _get_path_to_desired_seasons_from_soup(
    default_soup: BeautifulSoup,
    first_season: tuple[str, str],
    last_season: tuple[str, str],
) -> list[str]:
    all_seasons: list[str] = _get_path_seasons_from_webpage(default_soup)

    desired_seasons: list[str] = _filter_season_between_first_and_last(
        all_seasons, first_season, last_season
    )
    return desired_seasons


@log(logging.info)
@run_three_times
def get_path_to_desired_seasons(
    default_path: str, first_season: tuple[str, str], last_season: tuple[str, str]
) -> list[str]:
    """
    Given a default betexplorer.com path, returns the
    path to all desired seasons, that is, seasons between
    first and last (both included).

    By default, this procedure will be attempted three times to
    mitigate possible connection problems.

    --------
    Parameters:

        path: str
            String of the form /sports/country/name/

        first_season: tuple[str, str]
            First season to be considered.

            It should be a tuple containing both types of seasons:
            one that starts and ends in the same year and one that
            starts in one year and ends in the next.

            Example: ("2015", "2013/2014")

        last_season: tuple[str, str]
            Last season to be considered.
            It is similar to the first_season parameter.

    --------
    Returns:

        list[str]
            After this procedure, each path will be of the form
            /sports/country/name-year/ and will take you to a
            specific season.

            Keep in mind, however, that some tournaments had their
            names changed at some point in time.

    """

    default_url: str = concatenate_homepage_url_to_path(default_path)

    webpage: bytes = requests.get(default_url).content
    default_soup: BeautifulSoup = BeautifulSoup(webpage, "html.parser")

    return _get_path_to_desired_seasons_from_soup(
        default_soup, first_season, last_season
    )

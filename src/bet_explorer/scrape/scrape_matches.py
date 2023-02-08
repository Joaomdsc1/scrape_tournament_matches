import re
import logging
from typing import Optional, Pattern, Union

import requests
from bs4 import BeautifulSoup, ResultSet, Tag
from logs import log

from ..utils import (
    CURRENT_YEAR,
    TODAY,
    YESTERDAY,
    concatenate_homepage_url_to_path,
    run_three_times,
)

Odds = list[float]
TeamsResultName = list[str]
Match = list[Union[float, int]]
Matches = list[Match]


def _concatenate_results_slash(path: str):
    return path + "results/"


def _get_main_section_query(default_soup: BeautifulSoup) -> str:
    # if there is a "main" section it will be in one of these submenus
    results_submenu: ResultSet = default_soup.find_all(
        "ul", attrs={"class": "list-tabs list-tabs--secondary"}
    )

    for submenu in results_submenu:
        for option in submenu.find_all("a"):
            if option.text.strip().lower() == "main":
                # option["href"] is the query for the main-result section

                # "&month=all": tourneys like "nba" are divided in month sub-sections
                # it's automatically ignored in the query if not necessary
                return option["href"] + "&month=all"

    return ""


def _get_soup_to_all_results(results_url: str) -> BeautifulSoup:
    webpage = requests.get(results_url).content
    results_soup = BeautifulSoup(webpage, "html.parser")

    # some tournaments require another request to get all results

    # it is possible to get the full path for all urls, but it would
    # require some redundant queries when there is no "main" section,
    # so I decided to solve it with a simple if statement
    query = _get_main_section_query(results_soup)

    if query:
        webpage = requests.get(results_url + query).content
        results_soup = BeautifulSoup(webpage, "html.parser")

    return results_soup


def _has_groups(match_table: Tag) -> bool:
    # "th" tags are the place where "group" can be found
    th_headers: ResultSet = match_table.find_all("th", attrs={"class": "h-text-left"})

    if not th_headers:
        return False

    return any("group" in th.text.lower() for th in th_headers)


def _should_ignore_tournament(match_table: Optional[Tag]) -> bool:
    return not match_table or _has_groups(match_table)


def _is_not_header(row: Tag) -> bool:
    return row.find("th") is None


def _get_rows_from_html_table(match_table: Tag) -> list[Tag]:
    # "tr" is the tag which contains both matches and round/group information (header)
    rows: ResultSet = match_table.find_all("tr")
    return [row for row in rows if _is_not_header(row)]


def _format_date_correctly(date: str) -> str:
    # usually date is represented by day.month.year
    # but there three edge cases:
    #   1. today show up as "Today"
    #   2. yesterday show up as "Yesterday"
    date = date.lower().strip().replace("today", TODAY).replace("yesterday", YESTERDAY)

    #   3. If a match happened in the current year, it is represented by day.month.
    return date + CURRENT_YEAR if date[-1] == "." else date


def _get_teams_result_date(match_row: Tag) -> TeamsResultName:
    # teams, result and date are text inside "td" tags
    row_text: list[str] = [col.text.strip() for col in match_row.find_all("td")]
    teams, result, *_, date = row_text

    date: str = _format_date_correctly(date)

    return [teams, result, date]


def _get_all_odds(match_row: Tag) -> Odds:
    # odds are stored as strings inside "data-odd" attributes
    any_char_re: Pattern[str] = re.compile(".*")
    data_odd_tags: ResultSet = match_row.find_all(attrs={"data-odd": any_char_re})

    return [float(tag["data-odd"].strip()) for tag in data_odd_tags]


def _extract_teams_result_date_odds(match_row: Tag) -> Match:
    teams_result_date: TeamsResultName = _get_teams_result_date(match_row)
    odds: Odds = _get_all_odds(match_row)

    return teams_result_date + odds


def _web_scrape_matches_information_from_soup(
    results_soup: BeautifulSoup,
) -> Optional[Matches]:
    match_table: Optional[Tag] = results_soup.find(
        "div", attrs={"id": "js-leagueresults-all"}
    )

    if _should_ignore_tournament(match_table):
        logging.warning("Season ignored.")
        return None

    match_rows: list[Tag] = _get_rows_from_html_table(match_table)

    return [_extract_teams_result_date_odds(match_row) for match_row in match_rows]


@log(logging.info)
@run_three_times
def web_scrape_matches_information(path: str) -> Optional[Matches]:
    """
    Given a path to a bet_explorer-webpage containing all matches
    of a tournament, web scrape the desired information, that is:
        teams, result, date, odds.


    ----
    Parameters:

        path: str
            string of the form /sport/country/name-year/.

            Example: /soccer/england/premier-league-2012-2013/
    """

    bet_url: str = concatenate_homepage_url_to_path(path)
    results_url: str = _concatenate_results_slash(bet_url)

    # unfortunately www.betexplorer.com/sport/country/name-year/results/
    # isn't always enough to get all matches, so it might be needed to do more
    results_soup: BeautifulSoup = _get_soup_to_all_results(results_url)

    return _web_scrape_matches_information_from_soup(results_soup)

import requests
import logging
from bs4 import BeautifulSoup, ResultSet, Tag

from .utils import HOMEPAGE, get_sport
from logs import log


def _extract_hyperlink_paths_from_homepage(bet_soup: BeautifulSoup) -> ResultSet:
    # Upcoming Events section inside homepage has some hyperlinks to tournaments
    upcoming_events: Tag = bet_soup.find("section", attrs={"id": "upcoming-events"})

    events: ResultSet = upcoming_events.find_all(
        "a", attrs={"class": "list-events__item__title"}
    )

    return [event["href"] for event in events]


def _filter_only_desired_sports(
    hyperlink_paths: ResultSet, sports: set[str]
) -> list[str]:
    return [
        hyperlink_path
        for hyperlink_path in hyperlink_paths
        if get_sport(hyperlink_path) in sports
    ]


def _get_tournament_url_paths_from_homepage(
    homepage_soup: BeautifulSoup, sports: set[str]
) -> list[str]:
    hyperlink_paths: ResultSet = _extract_hyperlink_paths_from_homepage(homepage_soup)
    filtered_paths: list[str] = _filter_only_desired_sports(hyperlink_paths, sports)

    return [suffix for suffix in filtered_paths]


@log(logging.info)
def get_tournament_url_paths(sports: set[str]) -> list[str]:
    """
    Parse through bet_explorer upcoming events (in its homepage)
    in order to get hyperlinks for some tournaments.
    Only tournaments of the desired "sports" will be used.

    This is only required if you don't have any hyperlinks at
    your disposal.

    -----
    Parameters:

        sports: Iterable[str]
            Desired sports

    -----
    Returns:

        list[str]:
            List of url paths.

            A url path for betexplorer.com is of the form:
                /sports/country/tournament_name/
    """

    bet_content: bytes = requests.get(HOMEPAGE).content
    bet_soup: BeautifulSoup = BeautifulSoup(bet_content, "html.parser")

    paths: list[str] = _get_tournament_url_paths_from_homepage(bet_soup, sports)

    return paths

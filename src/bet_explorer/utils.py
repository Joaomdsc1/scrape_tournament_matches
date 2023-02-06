from datetime import datetime, timedelta
from typing import Literal
from urllib.parse import urljoin

HOMEPAGE: Literal["https://www.betexplorer.com/"] = "https://www.betexplorer.com/"

TODAY_DATETIME: datetime = datetime.today()
YESTERDAY_DATETIME: datetime = TODAY_DATETIME - timedelta(days=1)

TODAY: str = TODAY_DATETIME.strftime("%d.%m.%Y")
YESTERDAY: str = YESTERDAY_DATETIME.strftime("%d.%m.%Y")
CURRENT_YEAR: str = str(TODAY_DATETIME.year)


def concatenate_homepage_url_to_path(path: str):

    """
        Adds path to homepage domain (https://www.betexplorer.com/).
    """

    return urljoin(HOMEPAGE, path)


def get_sport(path: str) -> str:

    """
        Returns what sport a path is for.

        Paths are of the form /sport/country/name/
    """
    _, sport, *_ = path.split("/")

    return sport


def get_tournament_name(path: str) -> str:

    """
        Returns what tournament a path is for.

        Paths are of the form /sport/country/name/
    """
    *_, name, _ = path.split("/")

    return name

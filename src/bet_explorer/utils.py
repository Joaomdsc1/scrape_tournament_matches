import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Literal
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


def run_three_times(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for trying to run a function more than once.
    """

    def wrapper(*args, **kwargs):
        for _ in range(3):
            result = func(*args, **kwargs)

            if result:  # if function's output is as expected
                return result

            time.sleep(random.uniform(6, 12))

        logging.warning("No results even after attempting three times.")
        logging.warning(f"args: {args}\n" + f"kwargs: {kwargs}")
        return []

    wrapper.__name__ = func.__name__

    return wrapper

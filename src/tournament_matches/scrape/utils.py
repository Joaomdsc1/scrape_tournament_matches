import logging
import random
import time
from datetime import datetime, timedelta
from typing import Callable, Literal, ParamSpec, TypeVar
from urllib.parse import urljoin

T = TypeVar("T")
P = ParamSpec("P")

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


def run_three_times(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator for trying to run a function more than once with shorter waits.
    """

    max_attempts = 3
    backoff_seconds = (1.5, 3.0)

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        for attempt in range(1, max_attempts + 1):
            result = func(*args, **kwargs)

            if result:  # if function's output is as expected
                return result

            if attempt < max_attempts:
                delay = backoff_seconds[min(attempt - 1, len(backoff_seconds) - 1)]
                jitter = random.uniform(0.0, 1.0)
                time.sleep(delay + jitter)

        logging.warning("No results even after attempting three times.")
        logging.warning("args: %s\nkwargs: %s", args, kwargs)
        return []

    wrapper.__name__ = func.__name__

    return wrapper

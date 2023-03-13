"""
    Module designed to group all filtering to be applied over
    web scraped matches.

    matches: pd.DataFrame[
        index=[
            "id" -> "{current_name}@/{sport}/{country}/{name-year}/",\n
        ],\n
        columns=[
            "date number" -> int
            "home"                -> str,\n
            "away"                -> str,\n
            "result"              -> "{home score}:{away score}",\n
            "winner"              -> Literal["h", "d", "a"]
                "h" -> home\n
                "d" -> draw\n
                "a" -> away
            "date"                -> "{day}.{month}.{year}",\n
            "odds home"           -> float,\n
            "odds tie (optional)" -> float,\n
            "odds away"           -> float,\n
        ]
    ]
"""

from . import filter_functions
from .filter import filter_and_save_tournaments_all_sports

__all__ = ["filter_functions", "filter_and_save_tournaments_all_sports"]

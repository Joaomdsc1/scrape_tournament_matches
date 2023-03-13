import logging
from pathlib import Path
from typing import Callable, Literal

import pandas as pd

from logs import log

from .utils import get_sets_intersection


def _filter_invalid_matches(matches: pd.DataFrame) -> pd.DataFrame:

    return matches.loc[
        matches["winner"].notna()
        & matches["home"].notna()
        & matches["away"].notna()
        & (matches.index.get_level_values("date number") != -1)
    ].sort_index()


def _filter_tournaments(
    matches: pd.DataFrame,
    *funcs: Callable[[pd.DataFrame], set[str]],
) -> pd.DataFrame:

    """
    Filter out tournaments according to provided functions.
    Matches that didn't happen (cancelled or postponed) will also be filtered out.

    ----
    Parameters:

        matches: pd.DataFrame
            tournaments matches

        *funcs: Callable[[pd.DataFrame], set[str]]

            Input: tournaments matches
                pd.DataFrame[
                    index=[
                        "id" -> str
                            "{current_name}@/{sport}/{country}/{name-year}/"
                        "date number" -> int
                    ],\n
                    columns=[
                        "home"                -> str (home team name),\n
                        "away"                -> str (away team name),\n
                        "result"              -> str
                            "{home score}:{away score}"
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

            Output: set of "id"s for all tournaments that should be kept.
    -----
    Returns:
        pd.DataFrame with only desired tournaments.
    """

    indexes: tuple[set[str], ...] = tuple(func(matches) for func in funcs)
    intersection_index = sorted(get_sets_intersection(*indexes))

    return matches.loc[intersection_index].sort_index()


@log(logging.debug)
def _filter_matches_and_tournaments(
    matches: pd.DataFrame,
    filter_matches: Literal["no", "before", "after"],
    *funcs: Callable[[pd.DataFrame], set[str]],
) -> pd.DataFrame:

    str_to_filter_matches_funcs = {
        "no": (lambda x: x, lambda x: x),
        "before": (_filter_invalid_matches, lambda x: x),
        "after": (lambda x: x, _filter_invalid_matches),
    }

    dft = (lambda x: x, lambda x: x)
    func_before, func_after = str_to_filter_matches_funcs.get(filter_matches, dft)

    input = func_before(matches)
    filtered_tournaments = _filter_tournaments(input, *funcs)
    return func_after(filtered_tournaments)


def filter_and_save_tournaments_all_sports(
    sports: list[str],
    format_dir: Path,
    filter_dir: Path,
    filter_matches: Literal["no", "before", "after"],
    *funcs: Callable[[pd.DataFrame], set[str]],
) -> None:

    """
    Filter and save tournaments for all sports.
    Before filtering, all invalid matches will be removed.

    ----
    Parameters:

        sports: list[str]
            List of sports to be filtered

        format_dir: Path
            Path to data with tournament matches.

            Filename should simply like: f"{sport}.csv"

        filter_dir: Path
            Path to which formatted data will be saved.

        filter_invalid_matches: Literal["no", "before", "after"]
            Whether or not invalid matches should be filtered out.

            "no": Do not filter them out.
            "before": Filter them 'before' applying filtering functions
            "after": Filter them 'after' applying filtering functions
            Any other value: same as "no".

            Remark: Order is important.
                Take for example a tournament with 70 matches, 20 of which are invalid.

                Suppose you are filtering out all tournaments with less than 60 matches.
                    "before": only 50 valid matches, so tournament is removed.
                    "after": 70 total matches, so tournament is NOT removed.

        *funcs: Callable[[pd.DataFrame], set[str]]

            Input: tournaments matches
                pd.DataFrame[
                    index=[
                        "id" -> str
                            "{current_name}@/{sport}/{country}/{name-year}/"
                        "date number" -> int
                    ],\n
                    columns=[
                        "home"                -> str (home team name),\n
                        "away"                -> str (away team name),\n
                        "result"              -> str
                            "{home score}:{away score}"
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

            Output: set of "id"s for all tournaments that should be kept.

    -----
    Saved pd.DataFrame is like:

        pd.DataFrame[
            index=[
                "id" -> "{current_name}@/{sport}/{country}/{name-year}/",\n
                "date number" -> int
            ],\n
            columns=[
                "home"                -> str,\n
                "away"                -> str,\n
                "result"                -> "{home score}:{away score}",\n
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
    filter_dir.mkdir(parents=True, exist_ok=True)

    for sport in sports:

        filepath = format_dir / f"{sport}.csv"

        if not filepath.exists():
            logging.warning(f"No file: {filepath}")
            continue

        matches = pd.read_csv(filepath).set_index(["id", "date number"])
        filtered = _filter_matches_and_tournaments(matches, filter_matches, *funcs)
        filtered.to_csv(filter_dir / f"{sport}.csv")

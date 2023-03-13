"""
Functions to filter tournaments.

Function signature:

    Input: Tournaments Matches
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
                "odds tie"            -> float,\n
                "odds away"           -> float,\n
            ]
        ]
        "result", "date", "odds <...>" are all optional.

    Output: set of "id"s for all tournaments that should be kept.
"""

import pandas as pd


def _get_number_of_matches_per_id(matches: pd.DataFrame) -> pd.Series:
    return matches.groupby("id").apply(len)


def by_num_matches(matches: pd.DataFrame, min: float, max: float) -> set[str]:

    """
    Returns only "id"s for tournaments with the desired number of matches:

        min <= number of matches in tournament <= max
    """

    number_matches = _get_number_of_matches_per_id(matches)

    mask = (min <= number_matches) & (number_matches <= max)
    only_true = mask[mask]

    return set(only_true.index.to_list())


def _get_number_teams_per_id(matches: pd.DataFrame) -> pd.Series:

    # apply func
    def _get_team_names_one_id(one_id_matches: pd.DataFrame) -> pd.Series:
        return set(one_id_matches["home"]) | set(one_id_matches["away"])

    return matches.groupby("id").apply(_get_team_names_one_id).apply(len)


def by_num_teams(matches: pd.DataFrame, min: float, max: float) -> set[str]:

    """
    Returns only "id"s for tournaments with the desired number of teams:

        min <= number of teams in tournament <= max
    """

    number_teams = _get_number_teams_per_id(matches)

    mask = (min <= number_teams) & (number_teams <= max)
    only_true = mask[mask]

    return set(only_true.index.to_list())


def _count_matches_per_id_per_date_per_teams(matches: pd.DataFrame) -> pd.Series:

    groupby_cols = ["id", "date number", "home", "away"]
    return matches.groupby(groupby_cols).apply(len)


def by_num_repeated_matches_each_day(
    matches: pd.DataFrame, min: float, max: float
) -> set[str]:

    """
    Returns only "id"s for tournaments with all matches (A, B) between
    'min' and 'max' for all tournament dates.

    Specifically, if any match (A, B) happened less than 'min' or more than 'max'
    in the same day, the entire tournament will be removed.

    Only tournaments that obey this rule will be considered:
        (min <= num_match_per_day.min()) & (num_match_per_day.max() <= max)
    where both min() and max() are taken over all pairs (match, day) in a tournament.

    Remark: (A, B) is not considered the same match as (B, A).
    """

    number_matches_each_day = _count_matches_per_id_per_date_per_teams(matches)

    min_num_each_day = number_matches_each_day.groupby("id").min()
    max_num_each_day = number_matches_each_day.groupby("id").max()

    mask = (min <= min_num_each_day) & (max_num_each_day <= max)
    only_true = mask[mask]

    return set(only_true.index.to_list())

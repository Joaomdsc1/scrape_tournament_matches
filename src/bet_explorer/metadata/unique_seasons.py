import pandas as pd

from .types import Id
from .utils import flatten_dict_of_lists


def get_unique_season_names_per_sport(
    sport_to_matches: dict[str, pd.DataFrame]
) -> dict[str, list[Id]]:

    """
    Get unique season names for all sports separately.

    ---
    Parameters:

        sport_to_matches: dict[str, Matches]
            dictionary mapping each sport to its matches
    """

    return {
        sport: sorted(set(matches.index.get_level_values("id")))
        for sport, matches in sport_to_matches.items()
    }


def get_all_unique_season_names(
    sport_to_unique_seasons: dict[str, list[Id]]
) -> list[Id]:

    """
    Get unique season names for all sports together.

    ---
    Parameters:

        sport_to_unique_seasons: dict[str, list[Id]]
            dictionary mapping each sport to its unique seasons
    """

    return flatten_dict_of_lists(sport_to_unique_seasons)

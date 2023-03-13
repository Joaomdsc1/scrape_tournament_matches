from collections import Counter

from .types import Id, NoSeasonId
from .utils import flatten_dict_of_lists


def _get_no_season_tournament_name_one_id(id_: Id) -> NoSeasonId:

    *desired_information, name_year, empty = id_.split("/")

    return "/".join(desired_information)


def get_no_season_tournament_names_per_sport(
    sport_to_unique_seasons: dict[str, list[Id]],
) -> dict[str, list[NoSeasonId]]:

    """
    Get no season tournament names for each sports separately.

    No-seasons means that we remove the "/{name-season}/" suffix,
    but we keep repeated values.

    ---
    Parameters:

        sport_to_unique_seasons: dict[str, list[Id]]
            dictionary mapping each sport to its unique seasons
    """

    return {
        sport: [
            _get_no_season_tournament_name_one_id(season) for season in unique_seasons
        ]
        for sport, unique_seasons in sport_to_unique_seasons.items()
    }


def get_all_no_season_tournament_names(
    sport_to_no_season: dict[str, list[NoSeasonId]]
) -> list[NoSeasonId]:

    """
    Get no season tournament names for all sports together.

    No-seasons means that we remove the "/{name-season}/" suffix,
    but we keep repeated values.

    ---
    Parameters:

        sport_to_no_season: dict[str, list[NoSeasonId]]
            dictionary mapping each sport to its no season names
    """

    return flatten_dict_of_lists(sport_to_no_season)


def get_unique_tournaments_per_sport(
    sport_to_no_season: dict[str, list[str]]
) -> dict[str, list[NoSeasonId]]:

    """
    Get unique tournament names for each sports separately.

    ---
    Parameters:

        sport_to_no_season: dict[str, list[Id]]
            dictionary mapping each sport to its no season names
    """

    return {
        sport: sorted(set(no_seasons))
        for sport, no_seasons in sport_to_no_season.items()
    }


def get_all_unique_tournaments(
    sport_to_unique_tourneys: dict[str, NoSeasonId]
) -> list[NoSeasonId]:

    """
    Get unique tournament names for all sports together.

    ---
    Parameters:

        sport_to_unique_tourneys: dict[str, list[NoSeasonId]]
            dictionary mapping each sport to its unique tournament names
    """

    return flatten_dict_of_lists(sport_to_unique_tourneys)


def get_count_with_each_amount_of_seasons(
    all_no_season_tournaments: list[NoSeasonId],
) -> Counter:

    """
    For each possible total number of seasons, counts how many tournaments
    have exactly such a number.

    -----
    Parameters:

        all_unique_tournaments: list[NoSeasonId]
            list of all tournament names
    """

    number_seasons_per_tourney: Counter = Counter(all_no_season_tournaments)

    return Counter(number_seasons_per_tourney.values())

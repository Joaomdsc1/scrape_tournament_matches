from .tournament_names import NoSeasonId


def _get_country_name(no_season_id: NoSeasonId) -> str:

    current_name, sport, country = no_season_id.split("/")

    return country


def get_country_names(all_unique_no_seasons: list[NoSeasonId]) -> list[str]:

    """
    Get unique country names for all sports together.

    -----
    Parameters:

        all_unique_no_seasons: list[NoSeasonId]
            list of all unique tournament names
    """

    return sorted(set(_get_country_name(tourney) for tourney in all_unique_no_seasons))

import pandas as pd


def get_number_of_matches_per_sport(
    sport_to_matches: dict[str, pd.DataFrame]
) -> dict[str, int]:

    """
    Get the number of matches for each sport separately.

    ---
    Parameters:

        sport_to_matches: dict[str, Matches]
            dictionary mapping each sport to its matches
    """

    return {sport: matches.shape[0] for sport, matches in sport_to_matches.items()}


def get_total_number_of_matches(sport_to_num_matches: dict[str, int]) -> int:

    """
    Get the total number of matches for all sports.

    ---
    Parameters:

        sport_to_num_matches: dict[str, int]
            dictionary mapping each sport to the number of matches
    """

    return sum(sport_to_num_matches.values())

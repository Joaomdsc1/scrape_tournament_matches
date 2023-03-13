"""
Module for describing the dataset considered, that is, to count how many
tournaments were studied, how many matches considered, etc..
"""

from . import print_metadata
from .number_of_matches import get_number_of_matches_per_sport
from .tournament_names import (
    get_all_no_season_tournament_names,
    get_no_season_tournament_names_per_sport,
    get_unique_tournaments_per_sport,
)
from .unique_seasons import get_unique_season_names_per_sport

__all__ = [
    "print_metadata",
    "get_number_of_matches_per_sport",
    "get_all_no_season_tournament_names",
    "get_no_season_tournament_names_per_sport",
    "get_unique_tournaments_per_sport",
    "get_unique_season_names_per_sport",
]

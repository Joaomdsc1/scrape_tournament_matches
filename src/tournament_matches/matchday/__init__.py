"""Module for organizing football matches into matchdays/rounds.

This module provides functionality to organize football matches into proper rounds,
ensuring that each team plays exactly once per round.

For a tournament with N teams:
- If N is even: each round has N/2 matches
- If N is odd: each round has (N-1)/2 matches (one team sits out each round)

Functions:
    organize_tournament_rounds: Organize matches into rounds for a single tournament
    analyze_round_quality: Analyze the quality of round organization
    process_all_tournaments: Process all tournaments in a dataset
"""

from .matchday_organizer import organize_tournament_rounds, process_all_tournaments
from .quality_analyzer import analyze_round_quality, generate_quality_report
from .utils import parse_date, get_tournament_teams, calculate_expected_matches_per_round

__all__ = [
    "organize_tournament_rounds",
    "process_all_tournaments", 
    "analyze_round_quality",
    "generate_quality_report",
    "parse_date",
    "get_tournament_teams",
    "calculate_expected_matches_per_round"
]
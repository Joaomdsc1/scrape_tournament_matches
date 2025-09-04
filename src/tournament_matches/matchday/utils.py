"""Utility functions for matchday organization."""

import pandas as pd
from datetime import datetime
from typing import List, Optional


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime object.
    
    Args:
        date_str: Date string in format 'dd.mm.yyyy' or 'yyyy-mm-dd'
        
    Returns:
        Parsed datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(date_str, '%d.%m.%Y')
    except ValueError:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None


def get_tournament_teams(df: pd.DataFrame, tournament_id: str) -> List[str]:
    """Get all unique teams for a tournament.
    
    Args:
        df: DataFrame containing match data
        tournament_id: Tournament identifier
        
    Returns:
        Sorted list of unique team names
    """
    tournament_matches = df[df['id'] == tournament_id]
    home_teams = set(tournament_matches['home'].unique())
    away_teams = set(tournament_matches['away'].unique())
    return sorted(list(home_teams.union(away_teams)))


def calculate_expected_matches_per_round(n_teams: int) -> int:
    """Calculate expected number of matches per round.
    
    Args:
        n_teams: Number of teams in the tournament
        
    Returns:
        Expected number of matches per round
    """
    if n_teams % 2 == 0:
        return n_teams // 2
    else:
        return (n_teams - 1) // 2


def get_teams_in_matches(matches: pd.DataFrame) -> set:
    """Get all teams involved in a set of matches.
    
    Args:
        matches: DataFrame containing match data
        
    Returns:
        Set of team names
    """
    home_teams = set(matches['home'].tolist())
    away_teams = set(matches['away'].tolist())
    return home_teams.union(away_teams)


def has_team_conflict(matches: pd.DataFrame) -> bool:
    """Check if any team appears more than once in a set of matches.
    
    Args:
        matches: DataFrame containing match data
        
    Returns:
        True if there's a conflict, False otherwise
    """
    teams_in_matches = get_teams_in_matches(matches)
    total_team_appearances = len(matches) * 2  # Each match has 2 teams
    return len(teams_in_matches) != total_team_appearances
"""Main matchday organization logic."""

import pandas as pd
import numpy as np
from collections import defaultdict
from typing import Dict, List, Tuple
import logging

from .utils import (
    parse_date, 
    get_tournament_teams, 
    calculate_expected_matches_per_round,
    get_teams_in_matches,
    has_team_conflict
)


def organize_tournament_rounds(df: pd.DataFrame, tournament_id: str) -> pd.DataFrame:
    """Organize matches into proper rounds for a tournament.
    
    Args:
        df: DataFrame containing all match data
        tournament_id: Tournament identifier
        
    Returns:
        DataFrame with matches organized into rounds
    """
    tournament_matches = df[df['id'] == tournament_id].copy()
    teams = get_tournament_teams(df, tournament_id)
    n_teams = len(teams)
    
    logging.info(f"Processing {tournament_id}:")
    logging.info(f"  Teams: {n_teams}")
    logging.info(f"  Matches: {len(tournament_matches)}")
    
    matches_per_round = calculate_expected_matches_per_round(n_teams)
    logging.info(f"  Expected matches per round: {matches_per_round}")
    
    # Parse dates and sort by date
    tournament_matches['parsed_date'] = tournament_matches['date'].apply(parse_date)
    tournament_matches = tournament_matches.sort_values('parsed_date')
    
    # Group matches by date
    date_groups = tournament_matches.groupby('date')
    
    # Organize into rounds
    rounds = []
    current_round = 1
    unassigned_matches = []
    
    for date, matches_on_date in date_groups:
        matches_list = matches_on_date.to_dict('records')
        
        while matches_list:
            round_matches = _select_round_matches(matches_list, matches_per_round)
            
            if not round_matches:
                # No valid round can be formed, add remaining to unassigned
                unassigned_matches.extend(matches_list)
                break
            
            # Assign round number to selected matches
            for match in round_matches:
                rounds.append({**match, 'round': current_round})
            
            # Remove assigned matches from the list
            for match in round_matches:
                matches_list.remove(match)
            
            current_round += 1
    
    # Handle unassigned matches
    for match in unassigned_matches:
        rounds.append({**match, 'round': -1})  # -1 indicates unassigned
    
    if unassigned_matches:
        logging.warning(f"  {len(unassigned_matches)} matches could not be assigned to proper rounds")
    
    return pd.DataFrame(rounds)


def _select_round_matches(available_matches: List[Dict], target_count: int) -> List[Dict]:
    """Select matches for a single round without team conflicts.
    
    Args:
        available_matches: List of available match dictionaries
        target_count: Target number of matches for the round
        
    Returns:
        List of selected matches for the round
    """
    if not available_matches:
        return []
    
    selected_matches = []
    used_teams = set()
    
    for match in available_matches:
        home_team = match['home']
        away_team = match['away']
        
        # Check if either team is already used in this round
        if home_team not in used_teams and away_team not in used_teams:
            selected_matches.append(match)
            used_teams.add(home_team)
            used_teams.add(away_team)
            
            # Stop if we've reached the target count
            if len(selected_matches) >= target_count:
                break
    
    return selected_matches


def process_all_tournaments(df: pd.DataFrame) -> pd.DataFrame:
    """Process all tournaments in the dataset.
    
    Args:
        df: DataFrame containing match data for all tournaments
        
    Returns:
        DataFrame with all matches organized into rounds
    """
    tournaments = df['id'].unique()
    all_organized_matches = []
    
    logging.info(f"Processing {len(tournaments)} tournaments...")
    
    for tournament_id in tournaments:
        try:
            organized_matches = organize_tournament_rounds(df, tournament_id)
            all_organized_matches.append(organized_matches)
        except Exception as e:
            logging.error(f"Error processing tournament {tournament_id}: {e}")
            # Add original matches with round = -1 (unassigned)
            tournament_matches = df[df['id'] == tournament_id].copy()
            tournament_matches['round'] = -1
            all_organized_matches.append(tournament_matches)
    
    if all_organized_matches:
        result_df = pd.concat(all_organized_matches, ignore_index=True)
        logging.info(f"Successfully organized {len(result_df)} total matches")
        return result_df
    else:
        logging.warning("No matches were organized")
        return pd.DataFrame()
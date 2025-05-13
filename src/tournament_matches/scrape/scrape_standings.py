import logging
import requests
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pathlib import Path
import json
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapping of our tournament names to Sofascore tournament IDs
TOURNAMENT_MAPPING = {
    "premier-league": "17",
    "la-liga": "8",
    "bundesliga": "35",
    "serie-a": "23",
    "ligue-1": "34",
    "champions-league": "7",
    "europa-league": "19",
    "nba": "132",
    "euroleague": "133"
}

def get_standings(tournament_id: str) -> Optional[pd.DataFrame]:
    """
    Get standings from Sofascore for a given tournament ID.
    
    Args:
        tournament_id: The Sofascore tournament ID
        
    Returns:
        DataFrame with standings or None if failed
    """
    try:
        # Get the current season ID first
        season_url = f"https://api.sofascore.com/api/v1/tournament/{tournament_id}/seasons"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.sofascore.com',
            'Referer': 'https://www.sofascore.com/',
            'Connection': 'keep-alive'
        }
        
        # Get current season
        season_response = requests.get(season_url, headers=headers)
        season_response.raise_for_status()
        season_data = season_response.json()
        
        if not season_data.get('seasons'):
            logger.warning(f"No seasons found for tournament {tournament_id}")
            return None
            
        current_season = season_data['seasons'][0]['id']
        logger.info(f"Found current season ID: {current_season}")
        
        # Get standings for current season
        standings_url = f"https://api.sofascore.com/api/v1/tournament/{tournament_id}/season/{current_season}/standings/total"
        standings_response = requests.get(standings_url, headers=headers)
        standings_response.raise_for_status()
        standings_data = standings_response.json()
        
        if not standings_data.get('standings'):
            logger.warning(f"No standings found for tournament {tournament_id}")
            return None
            
        # Extract standings data
        rows = []
        for standing in standings_data['standings']:
            for row in standing.get('rows', []):
                team_data = {
                    'position': row.get('position', ''),
                    'team': row.get('team', {}).get('name', ''),
                    'played': row.get('matches', 0),
                    'won': row.get('wins', 0),
                    'drawn': row.get('draws', 0),
                    'lost': row.get('losses', 0),
                    'goals_for': row.get('scoresFor', 0),
                    'goals_against': row.get('scoresAgainst', 0),
                    'goal_diff': row.get('scoresFor', 0) - row.get('scoresAgainst', 0),
                    'points': row.get('points', 0)
                }
                rows.append(team_data)
        
        if not rows:
            logger.warning(f"No standings data extracted for tournament {tournament_id}")
            return None
            
        return pd.DataFrame(rows)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error getting standings for tournament {tournament_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting standings for tournament {tournament_id}: {e}")
        return None

def save_standings(season_paths: List[Tuple[str, str]], output_dir: Path) -> None:
    """
    Save standings for all tournaments to CSV and JSON files.
    
    Args:
        season_paths: List of (tournament, season) tuples
        output_dir: Directory to save the files
    """
    logger.info(f"Starting to save standings for {len(season_paths)} tournaments")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created standings directory at {output_dir}")
    
    for path in season_paths:
        try:
            # Extract tournament name from path
            tournament = path[0].split('/')[-1]
            
            # Get Sofascore tournament ID
            tournament_id = TOURNAMENT_MAPPING.get(tournament)
            if not tournament_id:
                logger.warning(f"No mapping found for tournament {tournament}")
                continue
                
            logger.info(f"Getting standings for {tournament}")
            
            # Get standings
            standings_df = get_standings(tournament_id)
            if standings_df is None:
                logger.warning(f"Failed to get standings for {tournament}")
                continue
                
            # Add tournament and season information
            standings_df['tournament'] = tournament
            standings_df['season'] = path[1]
            standings_df['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Save to CSV
            csv_filename = f"{tournament}_{path[1]}_standings.csv"
            csv_path = output_dir / csv_filename
            standings_df.to_csv(csv_path, index=False)
            logger.info(f"Saved standings to {csv_path}")
            
            # Save to JSON
            json_filename = f"{tournament}_{path[1]}_standings.json"
            json_path = output_dir / json_filename
            standings_df.to_json(json_path, orient='records', indent=2)
            logger.info(f"Saved standings to {json_path}")
            
            # Be nice to the server
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error processing {path}: {e}")
            continue 
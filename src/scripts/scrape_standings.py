import json
import logging
from pathlib import Path

from tournament_matches.scrape import save_standings_to_json
from tournament_matches.scrape.season_years import get_path_to_desired_seasons

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Read paths from url_paths.json
    with open("data/url_paths.json", "r") as f:
        data = json.load(f)
        paths = data["paths"]

    # Get current season paths for each tournament
    current_season = ("2024", "2023/2024")  # Current season
    season_paths = []
    
    for path in paths:
        try:
            season_paths.extend(get_path_to_desired_seasons(path, current_season, current_season))
        except Exception as e:
            logging.error(f"Error getting season path for {path}: {e}")

    # Create output directory
    output_dir = Path("data/standings")
    
    # Scrape and save standings
    save_standings_to_json(season_paths, output_dir)

if __name__ == "__main__":
    main() 
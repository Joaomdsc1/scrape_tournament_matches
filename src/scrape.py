import config
import tournament_matches as tm
from pathlib import Path
import logging
from datetime import datetime


def scrape() -> None:
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    params = config.parser.read_json_configuration("scrape.json")

    sports = params["sports"]
    logging.info(f"Sports to scrape: {sports}")

    scrape_dir = config.path.SCRAPE_PATH
    scrape_dir.mkdir(exist_ok=True, parents=True)

    paths_params = params["url_paths"]
    paths = config.parser.get_url_paths(paths_params, sports)
    unique_paths = sorted(set(paths))
    logging.info(f"Found {len(unique_paths)} unique tournament paths")

    if paths_params["validate"]:
        tm.scrape.validate_url_paths(unique_paths)

    # Get season paths for matches
    first_season = tuple(params["seasons"]["first"])
    last_season = tuple(params["seasons"]["last"])
    logging.info(f"Scraping matches from seasons {first_season} to {last_season}")
    
    season_paths = []
    for path in unique_paths:
        try:
            paths = tm.scrape.get_path_to_desired_seasons(path, first_season, last_season)
            if paths:
                season_paths.extend(paths)
                logging.info(f"Found {len(paths)} seasons for {path}")
            else:
                logging.warning(f"No seasons found for {path}")
        except Exception as e:
            logging.error(f"Error getting season path for {path}: {e}")

    # Scrape matches
    sport_to_matches = tm.scrape.web_scrape_from_provided_paths(
        unique_paths,
        first_season,
        last_season,
    )
    tm.scrape.save_web_scraped_matches(sport_to_matches, scrape_dir)

    # Scrape standings for current season
    current_year = datetime.now().year
    current_season = (str(current_year), f"{current_year-1}/{current_year}")
    logging.info(f"Scraping standings for current season: {current_season}")
    
    standings_paths = []
    for path in unique_paths:
        try:
            paths = tm.scrape.get_path_to_desired_seasons(path, current_season, current_season)
            if paths:
                standings_paths.extend(paths)
                logging.info(f"Found current season path for {path}: {paths[0]}")
            else:
                logging.warning(f"No current season found for {path}")
        except Exception as e:
            logging.error(f"Error getting current season path for {path}: {e}")

    # Create standings directory and save standings
    standings_dir = config.path.STANDINGS_PATH
    standings_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Created standings directory at {standings_dir}")
    
    if not standings_paths:
        logging.error("No current season paths available for standings scraping")
        return
        
    logging.info(f"Starting to scrape standings for {len(standings_paths)} tournaments")
    tm.scrape.save_standings(standings_paths, standings_dir)


if __name__ == "__main__":
    scrape()

import config
import tournament_matches as tm
from pathlib import Path
import logging
from datetime import datetime


def _configure_logging() -> None:
    """
    Ajusta o logger raiz para também enviar mensagens ao terminal.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    # Evita adicionar múltiplos handlers ao rodar o script mais de uma vez
    if not any(type(handler) is logging.StreamHandler for handler in root_logger.handlers):
        root_logger.addHandler(console_handler)


def scrape() -> None:
    _configure_logging()

    params = config.parser.read_json_configuration("scrape.json")

    sports = params["sports"]
    logging.info(f"Sports to scrape: {sports}")

    scrape_dir = config.path.SCRAPE_PATH
    scrape_dir.mkdir(exist_ok=True, parents=True)

    paths_params = params["url_paths"]
    paths_list = paths_params["list"]

    # Extract all names from the "list" in scrape.json
    paths = []
    for path_group in paths_list:
        paths.extend(path_group["names"])

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


if __name__ == "__main__":
    scrape()

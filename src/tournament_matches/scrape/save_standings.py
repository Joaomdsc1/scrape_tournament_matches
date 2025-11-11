import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

from logs import log

from .scrape_standings import web_scrape_standings

@log(logging.info)
def save_standings(paths: List[str], output_dir: Path) -> None:
    """
    Scrapes standings for each tournament path and saves them to CSV and JSON files.

    Parameters:
        paths: List[str]
            List of tournament paths to scrape standings from.
            Each path should be of the form /sport/country/name-year/
        
        output_dir: Path
            Directory where the CSV and JSON files will be saved.
            Each file will be named after the tournament path.
    """
    # Create the standings directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Created/verified directory: {output_dir}")

    if not paths:
        logging.warning("No paths provided for standings scraping")
        return

    logging.info(f"Starting to scrape standings for {len(paths)} tournaments")
    
    for path in paths:
        logging.info(f"Processing standings for {path}")
        standings = web_scrape_standings(path)
        
        if not standings:
            logging.warning(f"No standings found for {path}")
            continue

        try:
            # Convert standings to DataFrame
            df = pd.DataFrame(standings)
            
            # Create a filename from the path
            filename = path.strip("/").replace("/", "_") + "_standings.csv"
            output_path = output_dir / filename

            # Save to CSV
            df.to_csv(output_path, index=False, encoding='utf-8')
            logging.info(f"Saved standings for {path} to {output_path}")

            # Also save as JSON for backup
            json_filename = path.strip("/").replace("/", "_") + "_standings.json"
            json_path = output_dir / json_filename
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(standings, f, indent=2, ensure_ascii=False)
            logging.info(f"Saved standings backup for {path} to {json_path}")
            
        except Exception as e:
            logging.error(f"Error saving standings for {path}: {e}")
            continue

    logging.info("Finished scraping and saving standings") 
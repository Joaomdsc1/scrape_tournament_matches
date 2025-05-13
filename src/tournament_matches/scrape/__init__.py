"""
    Provide functions to web scrape https://www.betexplorer.com.

    Data format:

        pd.DataFrame[
            index=[],\n
            columns=[
                "id"   -> "{current_name}@/{sport}/{country}/{name-year}/"
                "teams"               -> "{home} - {away}",\n
                "result"              -> "{home score}:{away score}",\n
                "date"                -> "{day}.{month}.{year}",\n
                "odds home"           -> float,\n
                "odds tie (optional)" -> float,\n
                "odds away"           -> float,\n
            ]
        ]
"""

from .scrape_standings import save_standings
from .scrape_matches import web_scrape_from_provided_paths, save_web_scraped_matches
from .validate_url_paths import validate_url_paths
from .get_season_paths import get_path_to_desired_seasons

__all__ = [
    "save_standings",
    "web_scrape_from_provided_paths",
    "save_web_scraped_matches",
    "validate_url_paths",
    "get_path_to_desired_seasons",
]

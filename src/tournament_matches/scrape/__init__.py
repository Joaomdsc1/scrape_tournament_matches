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

from .homepage_paths import get_tournament_url_paths
from .validate_paths import validate_url_paths
from .web_scrape import save_web_scraped_matches, web_scrape_from_provided_paths

__all__ = [
    "get_tournament_url_paths",
    "validate_url_paths",
    "web_scrape_from_provided_paths",
    "save_web_scraped_matches",
]

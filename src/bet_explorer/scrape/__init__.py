"""
    Provide functions to web scrape https://www.betexplorer.com.
"""

from .homepage_paths import get_tournament_url_paths
from .web_scrape import web_scrape_from_provided_paths, save_web_scraped_matches

__all__ = [
    "get_tournament_url_paths",
    "web_scrape_from_provided_paths",
    "save_web_scraped_matches",
]

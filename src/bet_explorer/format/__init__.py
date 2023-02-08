"""
    Provide functions to format web scraped data.

    Input Data Format:

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

    Output Data format:

        pd.DataFrame[
            index=[
                "id" -> "{current_name}@/{sport}/{country}/{name-year}/",\n
                "date number" -> int (explained below),
            ],\n
            columns=[
                "home"                -> str (home team name),\n
                "away"                -> str (away team name),\n
                "result"              -> "{home score}:{away score}",\n
                "winner"              -> Literal["h", "d", "a"]
                    "h" -> home\n
                    "d" -> draw\n
                    "a" -> away
                "date"                -> "{day}.{month}.{year}",\n
                "odds home"           -> np.float16,\n
                "odds tie (optional)" -> np.float16,\n
                "odds away"           -> np.float16,\n
            ]
        ]


"""

from .format_scraped_data import (
    format_web_scraped,
    save_formatted_web_scraped_all_sports,
)

__all__ = ["format_web_scraped", "save_formatted_web_scraped_all_sports"]

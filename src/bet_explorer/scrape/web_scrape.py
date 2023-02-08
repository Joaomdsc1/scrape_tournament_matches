from collections import defaultdict
from pathlib import Path
from typing import Optional

import pandas as pd

from .scrape_matches import Matches, web_scrape_matches_information
from .season_years import get_path_to_desired_seasons
from ..utils import get_sport, get_tournament_name


def _create_tournament_id(name: str, season_path: str) -> str:
    return name + "@" + season_path


def _convert_matches_list_to_data_frame(
    id: str, matches: list[Matches]
) -> pd.DataFrame:
    df_matches: pd.DataFrame = pd.DataFrame(matches)

    df_matches.loc[:, "id"] = id
    return df_matches.set_index("id")


def _rename_columns(df_matches: pd.DataFrame) -> pd.DataFrame:
    # some sports don't have ties and because of it they only contain five columns
    COLUMN_NAMES: dict[int, list[str]] = {
        5: ["teams", "result", "date", "odds home", "odds away"],
        6: ["teams", "result", "date", "odds home", "odds tie", "odds away"],
    }

    columns: list[str] = COLUMN_NAMES[df_matches.shape[1]]
    return df_matches.set_axis(columns, axis="columns")


def _rename_columns_all_sports(
    sport_to_df_matches: dict[str, pd.DataFrame]
) -> dict[str, pd.DataFrame]:
    return {
        sport: _rename_columns(df_matches)
        for sport, df_matches in sport_to_df_matches.items()
    }


def _web_scrape_from_paths(
    paths: list[str], first_season: tuple[str, str], last_season: tuple[str, str]
) -> dict[str, pd.DataFrame]:
    sport_to_matches: dict[str, pd.DataFrame] = defaultdict(pd.DataFrame)

    for path in paths:  # path: /sport/country/current_name/
        # name is necessary because some tournaments had their names changed
        name: str = get_tournament_name(path)
        sport: str = get_sport(path)

        season_paths: list[str] = get_path_to_desired_seasons(
            path, first_season, last_season
        )

        for season_path in season_paths:  # season_path: /sport/country/name-year/
            # id for data_frame: f"{current_name}@{season_path}"
            id: str = _create_tournament_id(name, season_path)

            matches: Optional[Matches] = web_scrape_matches_information(season_path)

            if not matches:
                continue

            df_matches: pd.DataFrame = _convert_matches_list_to_data_frame(id, matches)
            sport_to_matches[sport] = pd.concat([sport_to_matches[sport], df_matches])

    stm_right_columns: dict[str, pd.DataFrame] = _rename_columns_all_sports(
        sport_to_matches
    )

    return stm_right_columns


def web_scrape_from_provided_paths(
    paths: list[str], first_season: tuple[str, str], last_season: tuple[str, str]
) -> dict[str, Matches]:
    """
    Given a list of default betexplorer.com paths and an interval of seasons,
    returns a dictionary with matches to all seasons grouped by sport.

    --------
    Parameters:

        path: list[str]
            String of the form /sports/country/name/

        first_season: tuple[str, str]
            First season to be considered.

            It should be a tuple containing both types of seasons: one that starts
            and ends in the same year and one that starts in one year and ends in
            the next.

            Example: ("2015", "2013/2014")

        last_season: tuple[str, str]
            Last season to be considered.
            It is similar to the first_season parameter.

    --------
    Returns:

        dict[
            str,\n
            pd.DataFrame[
                index=[
                    "id"   -> "{current_name}@/{sport}/{country}/{name-year}/"
                ],\n
                columns=[
                    "teams"               -> "{home} - {away}",\n
                    "result"              -> "{home score}:{away score}",\n
                    "date"                -> "{day}.{month}.{year}",\n
                    "odds home"           -> float,\n
                    "odds tie (optional)" -> float,\n
                    "odds away"           -> float,\n
                ]
            ]
        ]:
            Dictionary with the matches of desired tournaments.
                Key: sport
                Value: pd.DataFrame with matches' information for all tournaments
    """

    return _web_scrape_from_paths(paths, first_season, last_season)


def save_web_scraped_matches(
    sport_to_matches: dict[str, pd.DataFrame], directory_path: Path
) -> None:
    """
    Save all web scraped matches inside "directory_path" per sport, that is,
    each sport has its own file with all the respective tournaments.

    -----
    Parameters:
        sport_to_matches: dict[
            str,\n
            pd.DataFrame[
                index=[
                    "id"   -> "{current_name}@/{sport}/{country}/{name-year}/"
                ],\n
                columns=[
                    "teams"               -> "{home} - {away}",\n
                    "result"              -> "{home score}:{away score}",\n
                    "date"                -> "{day}.{month}.{year}",\n
                    "odds home"           -> float,\n
                    "odds tie (optional)" -> float,\n
                    "odds away"           -> float,\n
                ]
            ]
        ]
            Dictionary with all the matches for all tournament
            separated by sport (dict key).

        directory_path: Path
            Path to the folder where it will be saved on.
    """

    directory_path.mkdir(parents=True, exist_ok=True)

    for sport, df_matches in sport_to_matches.items():
        file_path: Path = directory_path / f"{sport}.csv"
        df_matches.to_csv(file_path)

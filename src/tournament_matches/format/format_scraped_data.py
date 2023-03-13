import logging
import re
from pathlib import Path
from typing import Any, Iterable, Literal, Pattern, Union

import numpy as np
import pandas as pd

from logs import log


def _is_not_valid_match_result(result: str) -> bool:
    pattern: Pattern[str] = re.compile(r"\d+:\d+")  # "number1:number2"

    return re.fullmatch(pattern, result) is None


def _remove_suffixes(result: str) -> str:
    # some results have 'suffixes' like ET
    only_result, *_ = result.strip().split(" ")
    return only_result


def _was_there_a_match(result: str) -> bool:
    # cancelled or postponed flags
    did_not_happen_flags = ("can", "postp")

    return not any(flag in result.lower() for flag in did_not_happen_flags)


def _change_invalid_result_to_empty_string(result: str) -> str:
    """
    Given a match result, returns it back if the result is valid
    otherwise returns an empty string.

    ----
    Parameters:
        result: str
            String of the form "{number}:{number}"

    -----
    Returns:
        result if it is valid, else returns "".
    """

    if not isinstance(result, str):
        logging.warning(f"Result is not a string: {result}.")
        return ""

    only_result: str = _remove_suffixes(result)

    if _is_not_valid_match_result(only_result):
        if not _was_there_a_match(only_result):  # match cancelled or postponed
            logging.warning(f"Match cancelled or postponed: {result}.")
            return "CAN/POSTP"

        # match may have been awarded but no result provided
        logging.warning(f"Result is not valid: {result}.")
        return ""

    return result


def _get_scores(result: str) -> tuple[int, int]:
    home, away = result.split(":")
    return int(home), int(away)


def _get_winner_from_result(result: str) -> Union[Literal["h", "d", "a"], float]:
    """
    Given a match result, returns the winner.

    ----
    Parameters:
        result: str
            String of the form "{number}:{number}"

    -----
    Returns:
        Literal["h", "d", "a"] | np.nan
            "h" for home
            "a" for away
            "d" for draw
        Imputes "h" if it is not a valid result, i.e., an empty string.
    """

    if not result:
        return "h"  # imputing home win

    if result == "CAN/POSTP":
        return np.nan  # ignoring when the match was cancelled/postponed

    only_result: str = _remove_suffixes(result)
    home, away = _get_scores(only_result)

    if home > away:
        return "h"
    elif home < away:
        return "a"
    else:
        return "d"


def _is_not_valid_home_away(teams: str) -> bool:
    pattern: Pattern[str] = re.compile(r".+? - .+?")  # "team1 - team2"
    return re.fullmatch(pattern, teams) is None


def _get_home_away(teams: str) -> tuple[str, str]:
    home, away = teams.strip().split(" - ")
    return home.strip(), away.strip()


def _get_home_from_teams(teams: str) -> Union[str, float]:
    """
    Given the name of teams of a match, returns home-team's name.

    -------
    Parameters:
        teams: str
            String of the form "{home-team} - {away-team}"

    -----
    Returns:
        str
            Home-team if teams is a valid parameter
            else ""
    """

    if not isinstance(teams, str):
        logging.warning(f"Teams are not a string: {teams}.")
        return np.nan

    if _is_not_valid_home_away(teams.strip()):
        logging.warning(f"Team name is not valid: {teams}")
        return np.nan

    home, _ = _get_home_away(teams)

    return home


def _get_away_from_teams(teams: str) -> str:
    """
    Given the name of teams of a match, returns away-team's name.

    -------
    Parameters:
        teams: str
            String of the form "{home-team} - {away-team}"

    -----
    Returns:
        str
            Away-team if teams is a valid parameter
            else ""
    """

    if not isinstance(teams, str):
        logging.warning("Teams are not a string.")
        return np.nan

    if _is_not_valid_home_away(teams.strip()):
        logging.warning(f"Team name is not valid: {teams}")
        return np.nan

    _, away = _get_home_away(teams)

    return away


def _is_not_valid_date(date: str) -> bool:
    pattern: Pattern[str] = re.compile(r"\d+\.\d+\.\d+")  # "day.month.year"

    return re.fullmatch(pattern, date) is None


def _create_yearmonthday(date: str) -> int:
    day, month, year = date.split(".")

    return int(f"{year}{month:0>2}{day:0>2}")  # Ex.: "{'9':0>2}" turns "9" into "09"


def _converts_date_to_yearmonthday(date: str) -> int:
    """
    Given a date (string separated by dots), returns an integer that
    represents it.

    ---
    Parameters:
        date: str
            String of the form "{day}.{month}.{year}"

    ----
    Returns:
        int:
            If date is valid it will turn into a number with
            year as the most significant values; followed by
            month; and day as the least significant ones.

            Otherwise, returns -1

    ---
    Example:
        both "15.09.2015" and "15.9.2015" turn into 20150915
    """

    if not isinstance(date, str):
        logging.warning("Date is not a string.")
        return -1

    if _is_not_valid_date(date):
        logging.warning(f"Team name is not valid: {date}")
        return -1

    return _create_yearmonthday(date)


def _are_all_not_nan(values: Iterable[Any]) -> bool:
    for value in values:
        # real checks removes the possibility of being string
        if np.isreal(value) and np.isnan(value):
            return False
    return True


def _remove_unnecessary_dates(
    date_ints: Iterable[int],
    winners: Iterable[Union[str, float]],  # float here is np.nan
    homes: Iterable[Union[str, float]],
    aways: Iterable[Union[str, float]],
) -> list[int]:
    """
    When any of (winner, home, away) cols do no exist, the match cannot
    be considered. So it is better to just set the date to the sentinel
    value -1 to avoid having 'empty' dates numbers.

    By 'empty' date number I mean a date number with no matches, meaning
    that there some date number would be skipped (defeating the whole
    purpose of having date numbers).
    """

    return [
        date_int if _are_all_not_nan(winner_home_away) else -1
        for date_int, *winner_home_away in zip(date_ints, winners, homes, aways)
    ]


def _create_date_to_number_dict(dates: list[int]) -> dict[int, int]:
    sorted_dates: list[int] = sorted(set(dates))

    if -1 in dates:  # deal with invalid dates
        sorted_dates.remove(-1)

    conversion_dict = {date: i for i, date in enumerate(sorted_dates)}
    conversion_dict[-1] = -1

    return conversion_dict


def _converts_dates_to_date_numbers(dates: list[int]) -> list[int]:
    """
    Given a list of dates (yearmonthday integers), returns
    a list of numbers (starting from zero) that represents them.

    ----
    Parameters:
        dates: list[int]
            List of yearmonthday integers

    -----
    Returns:
        list[int]
            List of numbers starting from zero that represents them.
            See example below.

    ----
    Examples:
        1)
            dates = [20150910, 20140910, 20150912, 20140910]

                sorted_dates -> [20140910, 20150910, 20150912]
                date_numbers: {
                    20140910: 0, # first date
                    20150910: 1, # second date
                    20150912: 2, # third date
                }

            function returns [1, 0, 2, 0]
    """

    date_to_number: dict[int, int] = _create_date_to_number_dict(dates)

    return [date_to_number[date] for date in dates]


def _converts_dates_to_date_numbers_per_id(date_ints: pd.Series) -> list[str]:
    return (
        # .groupby().apply() links each id to a list,
        # [...] so .explode() is needed to get the original shape back
        date_ints.groupby("id", observed=True)
        .apply(lambda series: _converts_dates_to_date_numbers(series.to_list()))
        .explode()
        .to_list()
    )


@log(logging.info)
def format_web_scraped(web_scraped_df: pd.DataFrame) -> pd.DataFrame:
    """
    Format web_scrape data into desired type for data analysis.

    ------
    Parameters:
        web_scraped_df:
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

    -----
    Returns:
        pd.DataFrame[
            index=[
                "id" -> "{current_name}@/{sport}/{country}/{name-year}/",\n
                "date number" -> int
            ],\n
            columns=[
                "home"                -> str,\n
                "away"                -> str,\n
                "result"              -> "{home score}:{away score}",\n
                "winner"              -> Literal["h", "d", "a"]
                    "h" -> home\n
                    "d" -> draw\n
                    "a" -> away
                "date"                -> "{day}.{month}.{year}",\n
                "odds home"           -> float,\n
                "odds tie (optional)" -> float,\n
                "odds away"           -> float,\n
            ]
        ]
    """
    sorted_df: pd.DataFrame = web_scraped_df.set_index("id").sort_index()

    sorted_df.loc[:, "result"] = sorted_df.loc[:, "result"].apply(
        _change_invalid_result_to_empty_string
    )
    sorted_df.loc[:, "winner"] = sorted_df.loc[:, "result"].apply(
        _get_winner_from_result
    )

    sorted_df.loc[:, "home"] = sorted_df.loc[:, "teams"].apply(_get_home_from_teams)
    sorted_df.loc[:, "away"] = sorted_df.loc[:, "teams"].apply(_get_away_from_teams)

    date_ints: pd.Series = sorted_df.loc[:, "date"].apply(
        _converts_date_to_yearmonthday
    )
    desired_date_ints: pd.Series = pd.Series(
        _remove_unnecessary_dates(
            date_ints.to_list(),
            sorted_df.loc[:, "winner"].to_list(),
            sorted_df.loc[:, "home"].to_list(),
            sorted_df.loc[:, "away"].to_list(),
        ),
        index=date_ints.index,
        name=date_ints.name,
    )
    sorted_df.loc[:, "date number"] = _converts_dates_to_date_numbers_per_id(
        desired_date_ints
    )

    return (
        sorted_df.drop("teams", axis=1)
        .set_index("date number", append=True)
        .sort_index()
    )


@log(logging.info)
def save_formatted_web_scraped_all_sports(
    sports: list[str], web_scrape_dir: Path, format_dir: Path
) -> None:
    """
    Format web scraped matches into desired type for data analysis
    and save it to disk.

    ------
    Parameters:
        sports: list[str]
            List of sports desired

        web_scrape_dir: Path
            Folder with web scraped matches

        format_dir: Path
            Folder formatted matches will be saved to.

    -----
    DataFrame style saved to disk:
        pd.DataFrame[
            index=[
                "id" -> "{current_name}@/{sport}/{country}/{name-year}/",\n
                "date number" -> int
            ],\n
            columns=[
                "home"                -> str,\n
                "away"                -> str,\n
                "result"                -> "{home score}:{away score}",\n
                "winner"              -> Literal["h", "d", "a"]
                    "h" -> home\n
                    "d" -> draw\n
                    "a" -> away
                "date"                -> "{day}.{month}.{year}",\n
                "odds home"           -> float,\n
                "odds tie (optional)" -> float,\n
                "odds away"           -> float,\n
            ]
        ]

            "date number" are numbers that represent each date:
                For example, [20150910, 20140910, 20150912, 20140910]
                would be represented as [1, 0, 2, 0] since 20140910 is
                the first date (number 0); 20150910 the second
                (number 1); and 20150912 is the last one (number 2).

    """

    format_dir.mkdir(parents=True, exist_ok=True)

    for sport in sports:
        filepath: Path = web_scrape_dir / f"{sport}.csv"

        if not filepath.exists():
            logging.warning(f"No file: {filepath}")
            continue
        web_scrape_df: pd.DataFrame = pd.read_csv(filepath)

        formatted_df: pd.DataFrame = format_web_scraped(web_scrape_df)

        format_filepath: Path = format_dir / f"{sport}.csv"
        formatted_df.to_csv(format_filepath)

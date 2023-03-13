from functools import partial

import bet_explorer as bet
import config
from bet_explorer.filter import filter_functions as ff

FILTERING_FUNCTIONS = [
    partial(ff.by_num_matches, min=50, max=float("inf")),
    partial(ff.by_num_teams, min=8, max=float("inf")),
    partial(ff.by_num_repeated_matches_each_day, min=0, max=1),
]


def filter() -> None:
    params = config.parser.read_json_configuration("scrape.json")
    sports = params["sports"]

    format_dir = config.path.FORMAT_PATH
    filter_dir = config.path.FILTER_PATH
    filter_dir.mkdir(exist_ok=True, parents=True)

    bet.filter.filter_and_save_tournaments_all_sports(
        sports,
        format_dir,
        filter_dir,
        "before",
        *FILTERING_FUNCTIONS,
    )


if __name__ == "__main__":
    filter()

import pandas as pd

import config
import tournament_matches.metadata as md


def print_metadata() -> None:
    params = config.parser.read_json_configuration("scrape.json")
    sports = params["sports"]

    sport_to_matches = {
        sport: pd.read_csv(
            config.path.FILTER_PATH / f"{sport}.csv",
            index_col=["id", "date number"],
        )
        for sport in sports
    }

    sport_to_num_matches = md.get_number_of_matches_per_sport(sport_to_matches)
    sport_to_u_seasons = md.get_unique_season_names_per_sport(sport_to_matches)
    sport_to_ns_id = md.get_no_season_tournament_names_per_sport(sport_to_u_seasons)
    sport_to_u_tourneys = md.get_unique_tournaments_per_sport(sport_to_ns_id)
    all_no_seasons = md.get_all_no_season_tournament_names(sport_to_ns_id)

    md.print_metadata.print_number_of_matches(sport_to_num_matches)
    md.print_metadata.print_number_unique_seasons(sport_to_u_seasons)
    md.print_metadata.print_number_tournament_names(sport_to_u_tourneys)
    md.print_metadata.print_num_tournaments_with_n_seasons(all_no_seasons)
    md.print_metadata.print_num_countries(all_no_seasons)


if __name__ == "__main__":
    print_metadata()

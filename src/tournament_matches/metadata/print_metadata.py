from . import country_names as cn
from . import number_of_matches as nm
from . import tournament_names as tn
from . import unique_seasons as us


def print_number_of_matches(sport_to_num_matches: dict[str, int]) -> None:

    print("Number of Matches")

    for sport, num_matches in sport_to_num_matches.items():
        print(f"{sport.title():<15} {num_matches}")

    total = nm.get_total_number_of_matches(sport_to_num_matches)
    print(f"{'Total':<15} {total}", end="\n\n")


def print_number_unique_seasons(sport_to_unique_seasons: dict[str, list[str]]) -> None:

    print("Number of Unique Seasons")

    for sport, unique_seasons in sport_to_unique_seasons.items():
        print(f"{sport.title():<15} {len(unique_seasons)}")

    all = us.get_all_unique_season_names(sport_to_unique_seasons)
    print(f"{'Total':<15} {len(all)}", end="\n\n")


def print_number_tournament_names(
    sport_to_unique_tourneys: dict[str, list[str]]
) -> None:

    print("Number of Tournament Names")

    for sport, unique_seasons in sport_to_unique_tourneys.items():
        print(f"{sport.title()}: {len(unique_seasons)}")

    all = tn.get_all_unique_tournaments(sport_to_unique_tourneys)
    print(f"{'Total':<15} {len(all)}", end="\n\n")


def print_num_tournaments_with_n_seasons(all_no_seasons: list[str]) -> None:

    print("Number of Tournaments with 'n' Seasons")

    counter = tn.get_count_with_each_amount_of_seasons(all_no_seasons)

    print(f"{'#Seasons':<15} {'#Tournaments'}")
    for key, count in counter.items():
        print(f"{key:<15} {count}", end="\n\n")


def print_num_countries(all_no_seasons: list[str]) -> None:

    print("Number of Countries")

    names = cn.get_country_names(all_no_seasons)

    print(f"{'Total':<15} {len(names)}")

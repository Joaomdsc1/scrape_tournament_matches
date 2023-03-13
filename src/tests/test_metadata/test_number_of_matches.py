import pandas as pd

import bet_explorer.metadata.number_of_matches as dnm


def test_get_number_of_matches_per_sport():

    sport1 = {
        "id": ["one/k", "one/k", "one/k", "one/l", "one/l", "two/a", "two/a", "two/a"],
        "home": ["a", "b", "c", "A", "B", "one", "two", "three"],
        "away": ["c", "a", "a", "C", "A", "two", "three", "one"],
    }

    sport2 = {
        "id": ["three/k", "three/k", "four/k", "four/l", "four/l", "five/a", "five/a"],
        "home": ["c", "a", "A", "A", "B", "three", "three"],
        "away": ["a", "b", "C", "C", "A", "two", "two"],
    }

    sport_to_matches = {
        "sport1": pd.DataFrame(sport1).set_index("id"),
        "sport2": pd.DataFrame(sport2).set_index("id"),
    }

    expected = {"sport1": 8, "sport2": 7}

    assert dnm.get_number_of_matches_per_sport(sport_to_matches) == expected


def test_get_total_number_of_matches():

    sport_to_num_matches = {}

    assert dnm.get_total_number_of_matches(sport_to_num_matches) == 0

    sport_to_num_matches = {"sport1": 62}

    assert dnm.get_total_number_of_matches(sport_to_num_matches) == 62

    sport_to_num_matches = {"sport1": 5, "sport2": 7}

    assert dnm.get_total_number_of_matches(sport_to_num_matches) == 12

    sport_to_num_matches = {"sport1": 2, "sport2": 4, "sport3": 2}

    assert dnm.get_total_number_of_matches(sport_to_num_matches) == 8

    sport_to_num_matches = {"sport1": 8, "sport2": 7, "sport3": 5}

    assert dnm.get_total_number_of_matches(sport_to_num_matches) == 20

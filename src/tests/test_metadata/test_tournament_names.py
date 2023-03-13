import tournament_matches.metadata.tournament_names as dtn


def test_get_no_season_tournament_name_one_id():

    assert (
        dtn._get_no_season_tournament_name_one_id("abc@/sport1/two/three-2001/")
        == "abc@/sport1/two"
    )
    assert (
        dtn._get_no_season_tournament_name_one_id("abc@/sport1/two/three-2002/")
        == "abc@/sport1/two"
    )
    assert (
        dtn._get_no_season_tournament_name_one_id("ok@/sport1/two/three-2005/")
        == "ok@/sport1/two"
    )
    assert (
        dtn._get_no_season_tournament_name_one_id("abcd@/sport2/ah/three-2001/")
        == "abcd@/sport2/ah"
    )
    assert (
        dtn._get_no_season_tournament_name_one_id("abcd@/sport2/ha/three-2002/")
        == "abcd@/sport2/ha"
    )
    assert (
        dtn._get_no_season_tournament_name_one_id("ok@/sport2/two/three-2005/")
        == "ok@/sport2/two"
    )


def test_get_no_season_tournament_names_per_sport():

    sport_to_unique_seasons = {
        "sport1": sorted(
            [
                "abc@/sport1/two/three-2001/",
                "abc@/sport1/two/three-2002/",
                "ok@/sport1/two/three-2005/",
            ]
        ),
        "sport2": sorted(
            [
                "abcd@/sport2/ah/three-2001/",
                "abcd@/sport2/ha/three-2002/",
                "ok@/sport2/two/three-2005/",
            ]
        ),
    }

    expected = {
        "sport1": sorted(["abc@/sport1/two", "abc@/sport1/two", "ok@/sport1/two"]),
        "sport2": sorted(["abcd@/sport2/ah", "abcd@/sport2/ha", "ok@/sport2/two"]),
    }

    assert (
        dtn.get_no_season_tournament_names_per_sport(sport_to_unique_seasons)
        == expected
    )


def test_get_all_no_season_tournament_names():

    sport_to_no_season = {
        "sport1": sorted(["abc@/sport1/two", "abc@/sport1/two", "ok@/sport1/two"]),
        "sport2": sorted(["abcd@/sport2/ah", "abcd@/sport2/ha", "ok@/sport2/two"]),
    }

    expected = sorted(
        [
            "abc@/sport1/two",
            "abc@/sport1/two",
            "ok@/sport1/two",
            "abcd@/sport2/ah",
            "abcd@/sport2/ha",
            "ok@/sport2/two",
        ]
    )

    assert dtn.get_all_no_season_tournament_names(sport_to_no_season) == expected


def test_get_unique_tournaments_per_sport():

    sport_to_no_seasons = {
        "sport1": sorted(["abc@/sport1/two", "abc@/sport1/two", "ok@/sport1/two"]),
        "sport2": sorted(["abcd@/sport2/ah", "abcd@/sport2/ha", "ok@/sport2/two"]),
    }

    expected = {
        "sport1": ["abc@/sport1/two", "ok@/sport1/two"],
        "sport2": ["abcd@/sport2/ah", "abcd@/sport2/ha", "ok@/sport2/two"],
    }

    assert dtn.get_unique_tournaments_per_sport(sport_to_no_seasons) == expected


def test_get_all_unique_tournaments():

    sport_to_unique_tourneys = {
        "sport1": ["abc@/sport1/two", "ok@/sport1/two"],
        "sport2": ["abcd@/sport2/ha", "ok@/sport2/two"],
    }

    expected = sorted(
        ["abc@/sport1/two", "ok@/sport1/two", "abcd@/sport2/ha", "ok@/sport2/two"]
    )

    assert dtn.get_all_unique_tournaments(sport_to_unique_tourneys) == expected


def test_get_count_with_each_amount_of_seasons():

    all_no_seasons_tournaments = sorted(
        [
            "abc@/sport1/two",
            "abc@/sport1/two",
            "ok@/sport1/two",
            "abcd@/sport2/ah",
            "abcd@/sport2/ha",
            "ok@/sport2/two",
        ]
    )

    count = dtn.get_count_with_each_amount_of_seasons(all_no_seasons_tournaments)

    assert count.get(0) is None
    assert count.get(1) == 4
    assert count.get(2) == 1

    for i in range(3, 100):
        assert count.get(i) is None

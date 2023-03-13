import pandas as pd

import tournament_matches.metadata.unique_seasons as dus


def test_get_unique_season_names_per_sport():

    sport1 = {
        "id": [
            "abc@/sport1/two/three-2001/",
            "abc@/sport1/two/three-2001/",
            "abc@/sport1/two/three-2002/",
            "abc@/sport1/two/three-2002/",
            "ok@/sport1/two/three-2005/",
            "ok@/sport1/two/three-2005/",
            "ok@/sport1/two/three-2005/",
        ]
    }

    sport2 = {
        "id": [
            "abcd@/sport2/ah/three-2001/",
            "abcd@/sport2/ah/three-2001/",
            "abcd@/sport2/ha/three-2002/",
            "abcd@/sport2/ha/three-2002/",
            "ok@/sport2/two/three-2005/",
            "ok@/sport2/two/three-2005/",
            "ok@/sport2/two/three-2005/",
        ]
    }

    sport_to_matches = {
        "sport1": pd.DataFrame(sport1).set_index("id"),
        "sport2": pd.DataFrame(sport2).set_index("id"),
    }

    expected = {
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

    assert dus.get_unique_season_names_per_sport(sport_to_matches) == expected


def test_get_all_unique_seasons_names():

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

    expected = sorted(
        [
            "abc@/sport1/two/three-2001/",
            "abc@/sport1/two/three-2002/",
            "ok@/sport1/two/three-2005/",
            "abcd@/sport2/ah/three-2001/",
            "abcd@/sport2/ha/three-2002/",
            "ok@/sport2/two/three-2005/",
        ]
    )

    assert dus.get_all_unique_season_names(sport_to_unique_seasons) == expected

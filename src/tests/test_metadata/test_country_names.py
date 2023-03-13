import tournament_matches.metadata.country_names as dcn


def test_get_country_name():

    assert dcn._get_country_name("abc@/sport1/two") == "two"
    assert dcn._get_country_name("abc@/sport1/three") == "three"
    assert dcn._get_country_name("ok@/sport1/two") == "two"
    assert dcn._get_country_name("abcd@/sport2/ah") == "ah"
    assert dcn._get_country_name("abcd@/sport2/ha") == "ha"
    assert dcn._get_country_name("ok@/sport2/two") == "two"


def test_get_country_names():

    all_unique_no_seasons = [
        "abc@/sport1/two",
        "abc@/sport1/three",
        "ok@/sport1/two",
        "abcd@/sport2/ah",
        "abcd@/sport2/ha",
        "ok@/sport2/two",
    ]

    expected = sorted(["two", "ah", "ha", "three"])

    assert dcn.get_country_names(all_unique_no_seasons) == expected

import numpy as np
import pandas as pd
import bet_explorer.format.format_scraped_data as fmt


def test_remove_suffixes():
    assert fmt._remove_suffixes("") == ""
    assert fmt._remove_suffixes("first second ") == "first"
    assert fmt._remove_suffixes(" first second third") == "first"
    assert fmt._remove_suffixes("45:29 ET ") == "45:29"
    assert fmt._remove_suffixes("4:2 suffix") == "4:2"


def test_is_not_valid_match_result():
    assert fmt._is_not_valid_match_result("")
    assert fmt._is_not_valid_match_result(":")
    assert fmt._is_not_valid_match_result("as:ds")
    assert not fmt._is_not_valid_match_result("1:2")
    assert not fmt._is_not_valid_match_result("12:23")


def test_did_the_match_happen():
    assert fmt._was_there_a_match("")
    assert fmt._was_there_a_match(":")
    assert fmt._was_there_a_match("as:ds")
    assert fmt._was_there_a_match("1:2")
    assert fmt._was_there_a_match("12:23")
    assert not fmt._was_there_a_match("CAN.")
    assert not fmt._was_there_a_match("POSTP.")


def test_change_invalid_result_to_empty_string():
    assert fmt._change_invalid_result_to_empty_string(10) == ""
    assert fmt._change_invalid_result_to_empty_string("") == ""
    assert fmt._change_invalid_result_to_empty_string(":") == ""
    assert fmt._change_invalid_result_to_empty_string("as:ds") == ""
    assert fmt._change_invalid_result_to_empty_string("CAN.") == "CAN/POSTP"
    assert fmt._change_invalid_result_to_empty_string("POSTP.") == "CAN/POSTP"
    assert fmt._change_invalid_result_to_empty_string("1:2 ET") == "1:2 ET"
    assert fmt._change_invalid_result_to_empty_string("1:2") == "1:2"
    assert fmt._change_invalid_result_to_empty_string("12:23") == "12:23"


def test_get_scores():
    assert fmt._get_scores("1:2") == (1, 2)
    assert fmt._get_scores("3:24") == (3, 24)
    assert fmt._get_scores("363:246") == (363, 246)


def test_get_winner():
    assert fmt._get_winner_from_result("") == "h"
    assert fmt._get_winner_from_result(" 12:2 ") == "h"
    assert fmt._get_winner_from_result(" 1:2 suffix") == "a"
    assert fmt._get_winner_from_result("30:30") == "d"


def test_is_not_home_away():
    assert fmt._is_not_valid_home_away("")
    assert fmt._is_not_valid_home_away("flaskjdf")
    assert not fmt._is_not_valid_home_away("lk - lk")
    assert not fmt._is_not_valid_home_away("team1 - team2")


def test_get_home_away():
    assert fmt._get_home_away(" team1 - team2 ") == ("team1", "team2")
    assert fmt._get_home_away("   1   -    2   ") == ("1", "2")
    assert fmt._get_home_away("one - two") == ("one", "two")


def test_get_home_from_teams():
    assert np.isnan(fmt._get_home_from_teams(""))
    assert np.isnan(fmt._get_home_from_teams("random a;lkskd"))
    assert fmt._get_home_from_teams("home - teamTwo") == "home"
    assert fmt._get_home_from_teams("   Ok-2    - Away") == "Ok-2"
    assert fmt._get_home_from_teams("   O k - Away") == "O k"


def test_away_home_from_teams():
    assert np.isnan(fmt._get_away_from_teams(""))
    assert np.isnan(fmt._get_away_from_teams("random a;lkskd"))
    assert fmt._get_away_from_teams("teamOne - away") == "away"
    assert fmt._get_away_from_teams("   Ok-2    - spa ce   ") == "spa ce"
    assert fmt._get_away_from_teams("   O k -    Aw ay   ") == "Aw ay"


def test_is_not_valid_date():
    assert fmt._is_not_valid_date("")
    assert fmt._is_not_valid_date("fljs.fjsl.fslj")
    assert fmt._is_not_valid_date("day.month.year")
    assert fmt._is_not_valid_date(".10.8")
    assert fmt._is_not_valid_date("2..8")
    assert fmt._is_not_valid_date("2.1.")
    assert not fmt._is_not_valid_date("2.1.2")
    assert not fmt._is_not_valid_date("02.10.2019")
    assert not fmt._is_not_valid_date("30.07.1998")


def test_create_yearmonthday():
    assert fmt._create_yearmonthday("02.10.2015") == 20151002
    assert fmt._create_yearmonthday("2.10.2015") == 20151002
    assert fmt._create_yearmonthday("3.9.2017") == 20170903
    assert fmt._create_yearmonthday("31.07.2022") == 20220731


def test_converts_date_to_yearmonthday():
    assert fmt._converts_date_to_yearmonthday("") == -1
    assert fmt._converts_date_to_yearmonthday("skf.lks.fsjl") == -1
    assert fmt._converts_date_to_yearmonthday("09.12.") == -1
    assert fmt._converts_date_to_yearmonthday("02.9.2000") == 20000902
    assert fmt._converts_date_to_yearmonthday("25.11.2001") == 20011125


def test_are_all_not_nan():
    assert fmt._are_all_not_nan([1, 2, "3", 4])
    assert fmt._are_all_not_nan([1, 2.343, "24"])
    assert not fmt._are_all_not_nan([np.nan, 2, "3", 4])


def test_remove_unnecessary_dates():
    values = [1, 2, 3, 4, 5]
    winners = [1, 2.02, 3.56, 4, 5.35]
    homes = ["1", "2", "3", "#", "^"]
    aways = ["h", "1", "3", "4", "a"]

    assert fmt._remove_unnecessary_dates(values, winners, homes, aways) == values

    values = [1, 2, 3, 4, 5]
    winners = ["a", "h", "d", "a", "h"]
    homes = ["C", "B", "A", "C", "B"]
    aways = ["A", "C", "C", "B", "A"]

    assert fmt._remove_unnecessary_dates(values, winners, homes, aways) == values

    values = [1, 2, 3, 4, 5]
    winners = ["a", "h", "d", "a", np.nan]
    homes = ["C", "B", "A", "C", "B"]
    aways = ["A", "C", "C", "B", "A"]

    assert fmt._remove_unnecessary_dates(values, winners, homes, aways) == [
        1,
        2,
        3,
        4,
        -1,
    ]

    values = [1, 2, 3, 4, 5]
    winners = [1, 2.02, 3.56, 4, 2.54]
    homes = ["1", "2", "3", np.nan, "^"]
    aways = ["h", "1", "3", "4", "a"]

    assert fmt._remove_unnecessary_dates(values, winners, homes, aways) == [
        1,
        2,
        3,
        -1,
        5,
    ]

    values = [1, 2, 3, 4, 5]
    winners = [1, 2.02, 3.56, 4, 2.54]
    homes = ["1", "2", "3", "3", "^"]
    aways = ["h", "1", np.nan, "4", "a"]

    assert fmt._remove_unnecessary_dates(values, winners, homes, aways) == [
        1,
        2,
        -1,
        4,
        5,
    ]

    values = [1, 2, 3, 4, 5]
    winners = [1, 2.02, 3.56, 4, np.nan]
    homes = [np.nan, "2", "3", "3", "^"]
    aways = ["h", "1", np.nan, "4", "a"]

    assert fmt._remove_unnecessary_dates(values, winners, homes, aways) == [
        -1,
        2,
        -1,
        4,
        -1,
    ]


def test_create_date_to_number():
    assert fmt._create_date_to_number_dict([]) == {-1: -1}

    dates = [5, 7, 10, 24, 15]
    expected = {-1: -1, 5: 0, 7: 1, 10: 2, 15: 3, 24: 4}
    assert fmt._create_date_to_number_dict(dates) == expected

    dates = [5, 7, 10, 7, 7]
    expected = {-1: -1, 5: 0, 7: 1, 10: 2}
    assert fmt._create_date_to_number_dict(dates) == expected

    dates = [20000510, 20101108, 20000510]
    expected = {-1: -1, 20000510: 0, 20101108: 1}
    assert fmt._create_date_to_number_dict(dates) == expected

    dates = [20150610, 20140708, 20160909, 20140808, 20140809]
    expected = {-1: -1, 20140708: 0, 20140808: 1, 20140809: 2, 20150610: 3, 20160909: 4}
    assert fmt._create_date_to_number_dict(dates) == expected


def test_converts_dates_to_date_numbers():
    assert fmt._converts_dates_to_date_numbers([]) == []

    dates = [5, 7, 15, 24, 13]
    expected = [0, 1, 3, 4, 2]
    assert fmt._converts_dates_to_date_numbers(dates) == expected

    dates = [3, 7, 175, 8, 8]
    expected = [0, 1, 3, 2, 2]
    assert fmt._converts_dates_to_date_numbers(dates) == expected

    dates = [19990510, 20101108, 19990510, 20000000]
    expected = [0, 2, 0, 1]
    assert fmt._converts_dates_to_date_numbers(dates) == expected

    dates = [20150610, 20140708, 20160909, 20140808, 20140809]
    expected = [3, 0, 4, 1, 2]
    assert fmt._converts_dates_to_date_numbers(dates) == expected


def test_converts_dates_to_date_numbers_per_id():
    test = pd.Series({"one": [0, 0, 0, 7, 5]}).explode().rename_axis("id")
    expected = pd.Series({"one": [0, 0, 0, 2, 1]}).explode().to_list()
    assert fmt._converts_dates_to_date_numbers_per_id(test) == expected

    test = (
        pd.Series({"one": [20150408, 20140725, 20140725], "two": [20140725, 20130101]})
        .explode()
        .rename_axis("id")
    )
    expected = pd.Series({"one": [1, 0, 0], "two": [1, 0]}).explode().to_list()
    assert fmt._converts_dates_to_date_numbers_per_id(test) == expected

    test = (
        pd.Series(
            {
                "one": [20120508, 20201923, 20201923, 20120508, 20140725],
                "two": [20140725, 20130101, 20130101, 20130101],
            }
        )
        .explode()
        .rename_axis("id")
    )
    expected = (
        pd.Series({"one": [0, 2, 2, 0, 1], "two": [1, 0, 0, 0]}).explode().to_list()
    )
    assert fmt._converts_dates_to_date_numbers_per_id(test) == expected


def test_format_web_scraped():
    test_cols = {
        "id": ["season2", "season2", "season2", "season1", "season1"],
        "teams": ["A - B", "not_teams", "B - A", "  one -   two", "three   -   four"],
        "result": ["CANC", "2:2", "to_be_imputed", " 54:16 ", "  76:101 ET"],
        "date": ["06.5.2020", "31.06.2019", "31.06.2019", "07.12.2015", "not_date"],
    }
    test = pd.DataFrame(data=test_cols)

    expected_cols = {
        "id": ["season1", "season1", "season2", "season2", "season2"],
        "date number": [0, -1, -1, -1, 0],
        "date": ["07.12.2015", "not_date", "06.5.2020", "31.06.2019", "31.06.2019"],
        "winner": ["h", "a", np.nan, "d", "h"],
        "home": ["one", "three", "A", np.nan, "B"],
        "away": ["two", "four", "B", np.nan, "A"],
        "result": [" 54:16 ", "  76:101 ET", "CAN/POSTP", "2:2", ""],
    }
    expected = (
        pd.DataFrame(data=expected_cols).set_index(["id", "date number"]).sort_index()
    )

    assert (
        fmt.format_web_scraped(test)
        .sort_index(axis=1)
        .equals(expected.sort_index(axis=1))
    )

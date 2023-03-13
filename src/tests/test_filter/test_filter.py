import pandas as pd
import pytest

import bet_explorer.filter.filter as ftr


@pytest.fixture
def matches():

    cols = {
        "id": ["2", "2", "2", "2", "3", "3", "3", "1", "1", "1", "1", "1"],
        "home": [
            "A",
            "B",
            "C",
            "E",
            "one",
            "one",
            "one",
            "one",
            "three",
            "one",
            pd.NA,
            "two",
        ],
        "away": [
            "B",
            "E",
            "D",
            "F",
            "two",
            "three",
            "two",
            "two",
            "one",
            "two",
            "one",
            pd.NA,
        ],
        "date number": [0, 0, 2, 1, 1, 0, 1, 0, 1, -1, 2, 2],
        "winner": ["a", "h", "d", "a", "d", "h", "a", "h", pd.NA, "a", "h", "d"],
        "odds home": [1.25, 1.5, None, pd.NA, 5.68, 1.76, 2.5, 3, 4, 0.25, 0.15, 0.68],
    }
    return pd.DataFrame(data=cols).set_index(["id", "date number"])


@pytest.fixture
def matches_not_na():

    cols = {
        "id": ["2", "2", "2", "2", "3", "3", "3", "1"],
        "home": ["A", "B", "C", "E", "one", "one", "one", "one"],
        "away": ["B", "E", "D", "F", "two", "three", "two", "two"],
        "date number": [0, 0, 2, 1, 1, 0, 1, 0],
        "winner": ["a", "h", "d", "a", "d", "h", "a", "h"],
        "odds home": [1.25, 1.5, None, pd.NA, 5.68, 1.76, 2.5, 3],
    }
    return pd.DataFrame(data=cols).set_index(["id", "date number"])


def _num_matches(df: pd.DataFrame, min: float, max: float) -> pd.Series:
    match_count = df.groupby("id").apply(len)
    return set(match_count[(min <= match_count) & (match_count <= max)].index)


def test_filter_invalid_matches(matches: pd.DataFrame, matches_not_na: pd.DataFrame):

    assert ftr._filter_invalid_matches(matches).equals(matches_not_na.sort_index())


def test_filter_tournaments(matches_not_na: pd.DataFrame):

    sorted_not_na = matches_not_na.sort_index()

    filter_functions = [lambda df: set(df.index.get_level_values("id"))]
    assert ftr._filter_tournaments(matches_not_na, *filter_functions).equals(
        sorted_not_na
    )

    for min, max in [(0, 0), (5, float("inf")), (float("-inf"), 0)]:
        filter_functions = [lambda match: _num_matches(match, min, max)]
        assert ftr._filter_tournaments(matches_not_na, *filter_functions).empty

    for min, max, to_drop in [
        (0, 2.1, ["2", "3"]),
        (1, 3, ["2"]),
        (3, 3, ["1", "2"]),
        (2, 4, ["1"]),
        (0.9, float("inf"), []),
    ]:
        filter_functions = [lambda match: _num_matches(match, min, max)]
        ftr_expected = sorted_not_na.drop(to_drop)
        assert ftr._filter_tournaments(matches_not_na, *filter_functions).equals(
            ftr_expected
        )

    filter_functions = [
        lambda match: _num_matches(match, 0, 3),
        lambda match: _num_matches(match, 3, 4),
    ]
    ftr_expected = sorted_not_na.drop(["1", "2"])
    assert ftr._filter_tournaments(matches_not_na, *filter_functions).equals(
        ftr_expected
    )

    filter_functions = [
        lambda match: _num_matches(match, 0, 3),
        lambda match: _num_matches(match, float("-inf"), 4),
        lambda match: _num_matches(match, float("inf"), 4),
    ]
    assert ftr._filter_tournaments(matches_not_na, *filter_functions).empty


def test_filter_matches_and_tournaments_no(
    matches: pd.DataFrame, matches_not_na: pd.DataFrame
):

    sorted_matches = matches.sort_index()
    sorted_not_na = matches_not_na.sort_index()

    filter_functions = [lambda df: set(df.index.get_level_values("id"))]
    assert ftr._filter_matches_and_tournaments(matches, "no", *filter_functions).equals(
        sorted_matches
    )

    for min, max, to_drop in [
        (0, 2.1, ["1", "2", "3"]),
        (1, 3, ["1", "2"]),
        (3, 3, ["1", "2"]),
        (2, 4, ["1"]),
        (0.9, float("inf"), []),
    ]:
        filter_functions = [lambda match: _num_matches(match, min, max)]
        ftr_expected = sorted_matches.drop(to_drop)
        assert ftr._filter_matches_and_tournaments(
            matches, "no", *filter_functions
        ).equals(ftr_expected)

    filter_functions = [lambda df: set(df.index.get_level_values("id"))]
    assert ftr._filter_matches_and_tournaments(
        matches_not_na, "no", *filter_functions
    ).equals(sorted_not_na)

    for min, max, to_drop in [
        (0, 2.1, ["2", "3"]),
        (1, 3, ["2"]),
        (3, 3, ["1", "2"]),
        (2, 4, ["1"]),
        (0.9, float("inf"), []),
    ]:
        filter_functions = [lambda match: _num_matches(match, min, max)]
        ftr_expected = sorted_not_na.drop(to_drop)
        assert ftr._filter_matches_and_tournaments(
            matches_not_na, "no", *filter_functions
        ).equals(ftr_expected)


def test_filter_matches_and_tournaments_before(
    matches: pd.DataFrame, matches_not_na: pd.DataFrame
):

    sorted_not_na = matches_not_na.sort_index()

    filter_functions = [lambda df: set(df.index.get_level_values("id"))]
    assert ftr._filter_matches_and_tournaments(
        matches, "before", *filter_functions
    ).equals(sorted_not_na)

    for min, max, to_drop in [
        (0, 2.1, ["2", "3"]),
        (1, 3, ["2"]),
        (3, 3, ["1", "2"]),
        (2, 4, ["1"]),
        (0.9, float("inf"), []),
    ]:
        filter_functions = [lambda match: _num_matches(match, min, max)]
        ftr_expected = sorted_not_na.drop(to_drop)
        assert ftr._filter_matches_and_tournaments(
            matches, "before", *filter_functions
        ).equals(ftr_expected)


def test_filter_matches_and_tournaments_after(
    matches: pd.DataFrame, matches_not_na: pd.DataFrame
):

    sorted_not_na = matches_not_na.sort_index()

    filter_functions = [lambda df: set(df.index.get_level_values("id"))]
    assert ftr._filter_matches_and_tournaments(
        matches, "after", *filter_functions
    ).equals(sorted_not_na)

    for min, max, to_drop in [
        (0, 2.1, ["1", "2", "3"]),
        (1, 3, ["1", "2"]),
        (3, 3, ["1", "2"]),
        (2, 4, ["1"]),
        (0.9, float("inf"), []),
    ]:
        filter_functions = [lambda match: _num_matches(match, min, max)]
        ftr_expected = sorted_not_na.drop(to_drop)
        assert ftr._filter_matches_and_tournaments(
            matches, "after", *filter_functions
        ).equals(ftr_expected)

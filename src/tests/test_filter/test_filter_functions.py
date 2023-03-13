import pandas as pd
import pytest

import bet_explorer.filter.filter_functions as ff


@pytest.fixture
def first_matches():
    cols = {
        "id": ["1", "2", "2"],
        "date number": [0, 0, 0],
        "home": ["one", "A", "C"],
        "away": ["four", "B", "D"],
    }
    return pd.DataFrame(data=cols).set_index(["id", "date number"])


@pytest.fixture
def second_matches():

    cols = {
        "id": ["1", "1", "2", "2", "2", "3"],
        "date number": [0, 1, 0, 1, 1, 0],
        "home": ["one", "three", "A", "B", "C", "o"],
        "away": ["two", "four", "B", "A", "A", "k"],
    }
    return pd.DataFrame(data=cols).set_index(["id", "date number"])


def test_get_number_of_matches_per_id_first(first_matches: pd.DataFrame):

    expected = pd.Series(index=["1", "2"], data=[1, 2])
    assert ff._get_number_of_matches_per_id(first_matches).equals(expected)


def test_get_number_of_matches_per_id_second(second_matches: pd.DataFrame):

    expected = pd.Series(index=["1", "2", "3"], data=[2, 3, 1])
    assert ff._get_number_of_matches_per_id(second_matches).equals(expected)


def test_by_num_matches_first(first_matches: pd.DataFrame):

    assert ff.by_num_matches(first_matches, 0, 0) == set()
    assert ff.by_num_matches(first_matches, 1, 1) == {"1"}
    assert ff.by_num_matches(first_matches, 1, 1.5) == {"1"}
    assert ff.by_num_matches(first_matches, 1, float("inf")) == {"1", "2"}
    assert ff.by_num_matches(first_matches, 2, 2) == {"2"}
    assert ff.by_num_matches(first_matches, 2, float("inf")) == {"2"}
    assert ff.by_num_matches(first_matches, 3, float("inf")) == set()


def test_by_num_matches_second(second_matches: pd.DataFrame):

    assert ff.by_num_matches(second_matches, 0, 0) == set()
    assert ff.by_num_matches(second_matches, 1, 1) == {"3"}
    assert ff.by_num_matches(second_matches, 1, 2.1) == {"1", "3"}
    assert ff.by_num_matches(second_matches, 1, float("inf")) == {
        "1",
        "2",
        "3",
    }
    assert ff.by_num_matches(second_matches, 2, 2) == {"1"}
    assert ff.by_num_matches(second_matches, 2, float("inf")) == {"1", "2"}
    assert ff.by_num_matches(second_matches, 3, float("inf")) == {"2"}
    assert ff.by_num_matches(second_matches, 5, float("inf")) == set()


def test_get_number_teams_per_id_first(first_matches: pd.DataFrame):

    expected_index = ["1", "2"]
    expected_data = [2, 4]
    expected = pd.Series(expected_data, expected_index)

    assert ff._get_number_teams_per_id(first_matches).equals(expected)


def test_get_number_teams_per_id_second(second_matches: pd.DataFrame):

    expected_index = ["1", "2", "3"]
    expected_data = [4, 3, 2]
    expected = pd.Series(expected_data, expected_index)

    assert ff._get_number_teams_per_id(second_matches).equals(expected)


def test_by_num_teams_first(first_matches: pd.DataFrame):

    assert ff.by_num_teams(first_matches, 1, 1) == set()
    assert ff.by_num_teams(first_matches, 2, 3.2) == {"1"}
    assert ff.by_num_teams(first_matches, 2, float("inf")) == {"1", "2"}
    assert ff.by_num_teams(first_matches, 3, 3.5) == set()
    assert ff.by_num_teams(first_matches, 3, float("inf")) == {"2"}
    assert ff.by_num_teams(first_matches, 4, float("inf")) == {"2"}
    assert ff.by_num_teams(first_matches, 5, 5) == set()
    assert ff.by_num_teams(first_matches, 5, float("inf")) == set()


def test_by_num_teams_second(second_matches: pd.DataFrame):

    assert ff.by_num_teams(second_matches, 1, 1) == set()
    assert ff.by_num_teams(second_matches, 1, 2.2) == {"3"}
    assert ff.by_num_teams(second_matches, 1, 3) == {"2", "3"}
    assert ff.by_num_teams(second_matches, 1, float("inf")) == {"1", "2", "3"}
    assert ff.by_num_teams(second_matches, 2, 2) == {"3"}
    assert ff.by_num_teams(second_matches, 2, 3.11) == {"2", "3"}
    assert ff.by_num_teams(second_matches, 2, float("inf")) == {"1", "2", "3"}
    assert ff.by_num_teams(second_matches, 3, 3) == {"2"}
    assert ff.by_num_teams(second_matches, 3, 4) == {"1", "2"}
    assert ff.by_num_teams(second_matches, 3, float("inf")) == {"1", "2"}
    assert ff.by_num_teams(second_matches, 4, float("inf")) == {"1"}
    assert ff.by_num_teams(second_matches, 5, float("inf")) == set()


@pytest.fixture
def matches():

    cols = {
        "id": ["2", "2", "2", "2", "1", "1", "1", "1", "1"],
        "date number": [0, 0, 0, 1, 0, 0, 0, 0, 0],
        "home": ["a", "b", "c", "a", "a", "c", "c", "a", "a"],
        "away": ["b", "a", "d", "b", "b", "d", "d", "b", "b"],
    }

    return pd.DataFrame(cols).set_index(["id", "date number", "home", "away"])


def test_count_matches_per_id_per_date_per_teams(matches: pd.DataFrame):

    index = pd.MultiIndex.from_arrays(
        [
            ["2", "2", "2", "2", "1", "1"],
            [0, 0, 0, 1, 0, 0],
            ["a", "b", "c", "a", "a", "c"],
            ["b", "a", "d", "b", "b", "d"],
        ],
        names=("id", "date number", "home", "away"),
    )

    data = [1, 1, 1, 1, 3, 2]
    expected = pd.Series(index=index, data=data)

    assert ff._count_matches_per_id_per_date_per_teams(matches).equals(
        expected.sort_index()
    )


def test_by_num_repeated_matches_each_day(matches: pd.DataFrame):

    assert ff.by_num_repeated_matches_each_day(matches, 0, 0) == set()
    assert ff.by_num_repeated_matches_each_day(matches, 0, 2) == {"2"}
    assert ff.by_num_repeated_matches_each_day(matches, 0, 3) == {"1", "2"}
    assert ff.by_num_repeated_matches_each_day(matches, 0, float("inf")) == {"1", "2"}
    assert ff.by_num_repeated_matches_each_day(matches, 1, 1) == {"2"}
    assert ff.by_num_repeated_matches_each_day(matches, 1, 2.1) == {"2"}
    assert ff.by_num_repeated_matches_each_day(matches, 1, 3) == {"1", "2"}
    assert ff.by_num_repeated_matches_each_day(matches, 1, float("inf")) == {"1", "2"}
    assert ff.by_num_repeated_matches_each_day(matches, 2, 2.5) == set()
    assert ff.by_num_repeated_matches_each_day(matches, 2, 3) == {"1"}
    assert ff.by_num_repeated_matches_each_day(matches, 2, 3.2) == {"1"}
    assert ff.by_num_repeated_matches_each_day(matches, 2, float("inf")) == {"1"}
    assert ff.by_num_repeated_matches_each_day(matches, 3, float("inf")) == set()

import pandas as pd
import pytest
import bet_explorer.scrape.web_scrape as scrape


@pytest.fixture
def data_frame_one():
    index = ["id_test", "id_test"]
    dict_test = {0: [1, 3], 1: [2, 4]}  # dicts become cols

    return pd.DataFrame(data=dict_test, index=index)


@pytest.fixture
def data_frame_five_no_name_cols():
    index = ["1", "1"]
    dict_test = {i: [i, i + 1] for i in range(5)}

    return pd.DataFrame(data=dict_test, index=index)


@pytest.fixture
def data_frame_five_cols():
    index = ["1", "1"]
    cols = ["teams", "result", "date", "odds home", "odds away"]
    dict_test = {col: [i, i + 1] for i, col in zip(range(5), cols)}

    return pd.DataFrame(data=dict_test, index=index)


@pytest.fixture
def data_frame_six_cols():
    index = ["ok", "ok"]
    cols = ["teams", "result", "date", "odds home", "odds tie", "odds away"]
    dict_test = {col: [1, 2] for _, col in zip(range(6), cols)}

    return pd.DataFrame(data=dict_test, index=index)


def test_create_id():
    assert scrape._create_tournament_id("first", "second") == "first@second"
    assert scrape._create_tournament_id("name", "/s/c/n-y/") == "name@/s/c/n-y/"


def test_convert_matches_to_data_frame(data_frame_one, data_frame_five_no_name_cols):
    id = "id_test"
    data = [[1, 2], [3, 4]]

    assert scrape._convert_matches_list_to_data_frame(id, data).equals(data_frame_one)

    id = "1"
    data = [list(range(5)), list(range(1, 6))]

    assert scrape._convert_matches_list_to_data_frame(id, data).equals(
        data_frame_five_no_name_cols
    )


def test_rename_cols(data_frame_five_cols, data_frame_six_cols):
    index = ["1", "1"]
    dict_test = {i: [i, i + 1] for i in range(5)}

    assert scrape._rename_columns(pd.DataFrame(data=dict_test, index=index)).equals(
        data_frame_five_cols
    )

    index = ["ok", "ok"]
    dict_test = {str(2 * i): [1, 2] for i in range(6)}

    assert scrape._rename_columns(pd.DataFrame(data=dict_test, index=index)).equals(
        data_frame_six_cols
    )


def test_rename_cols_all_sports(data_frame_five_cols, data_frame_six_cols):
    dict_to_df = dict()

    index = ["1", "1"]
    dict_test = {i: [i, i + 1] for i in range(5)}
    dict_to_df["test"] = pd.DataFrame(data=dict_test, index=index)

    assert scrape._rename_columns_all_sports(dict_to_df)["test"].equals(
        data_frame_five_cols
    )

    index = ["ok", "ok"]
    dict_test = {str(2 * i): [1, 2] for i in range(6)}
    dict_to_df["test2"] = pd.DataFrame(data=dict_test, index=index)

    assert scrape._rename_columns_all_sports(dict_to_df)["test"].equals(
        data_frame_five_cols
    )
    assert scrape._rename_columns_all_sports(dict_to_df)["test2"].equals(
        data_frame_six_cols
    )

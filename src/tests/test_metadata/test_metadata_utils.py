import tournament_matches.metadata.utils as utils


def test_flatten_dict_of_lists():

    dictionary = {
        "one": list(range(11)),
        "two": list(range(11, 101)),
    }

    expected = list(range(101))

    assert utils.flatten_dict_of_lists(dictionary) == expected

    dictionary = {
        "one": list(range(11)),
        "two": list(range(11)),
        "three": list(range(11)),
    }

    expected = sorted(list(range(11)) * 3)

    assert utils.flatten_dict_of_lists(dictionary) == expected

    dictionary = {
        "one": ["one/a", "one/b", "one/c", "one/d"],
        "two": ["two/a", "two/b", "two/c", "two/d"],
    }

    expected = sorted(
        ["one/a", "one/b", "one/c", "one/d", "two/a", "two/b", "two/c", "two/d"]
    )

    assert utils.flatten_dict_of_lists(dictionary) == expected

import tournament_matches.filter.utils as utils


def test_get_sets_intersection_trivial():

    index_one = {"one", "two"}
    assert utils.get_sets_intersection(index_one) == index_one


def test_get_sets_intersection_one():

    index_one = {"one", "two", "three"}
    index_two = set()

    expected = set()

    assert utils.get_sets_intersection(index_one, index_two) == expected

    index_one = {"one", "two", "three"}
    index_two = {"four", "five"}

    expected = set()

    assert utils.get_sets_intersection(index_one, index_two) == expected

    index_one = {"one", "two", "three"}
    index_two = {"three", "five"}

    expected = {"three"}

    assert utils.get_sets_intersection(index_one, index_two) == expected

    index_one = {"two", "three"}
    index_two = {"three", "two"}

    expected = {"three", "two"}

    assert utils.get_sets_intersection(index_one, index_two) == expected


def test_get_sets_intersection_two():

    index_one = {"one", "two", "three"}
    index_two = set()
    index_three = {"a", "b"}

    expected = set()

    assert utils.get_sets_intersection(index_one, index_two, index_three) == expected

    index_one = {"one", "two", "three"}
    index_two = {"four", "five"}
    index_three = {"one", "four"}

    expected = set()

    assert utils.get_sets_intersection(index_one, index_two, index_three) == expected

    index_one = {"one", "two", "three"}
    index_two = {"three", "five"}
    index_three = {"three", "two"}

    expected = {"three"}

    assert utils.get_sets_intersection(index_one, index_two, index_three) == expected

    index_one = {"two", "three"}
    index_two = {"three", "two"}
    index_three = {"one", "two", "three"}

    expected = {"three", "two"}

    assert utils.get_sets_intersection(index_one, index_two, index_three) == expected

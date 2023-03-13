from typing import TypeVar

Key = TypeVar("Key")
T = TypeVar("T")


def flatten_dict_of_lists(dictionary: dict[Key, list[T]]) -> list[T]:

    """
    Convert a dict of lists into a list containing all values.

    Returned list is also sorted.
    """

    list_of_values: list[list[T]] = [lst for lst in dictionary.values()]

    return sorted(value for values in list_of_values for value in values)

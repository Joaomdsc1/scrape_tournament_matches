from typing import TypeVar

T = TypeVar("T")


def get_sets_intersection(*sets: set[T]) -> list[T]:

    if not sets:
        return []

    intersection, *others = sets

    for index in others:
        intersection = intersection & index

    return intersection

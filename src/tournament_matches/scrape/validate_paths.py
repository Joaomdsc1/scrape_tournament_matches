import logging

import requests

from .utils import CURRENT_YEAR, concatenate_homepage_url_to_path

NOT_FOUND_CODE = 404
CURRENT_SEASON = int(CURRENT_YEAR)


class InvalidPaths(Exception):
    pass


def _is_path_invalid(path: str) -> bool:

    url = concatenate_homepage_url_to_path(path)
    request = requests.get(url)

    return request.status_code == NOT_FOUND_CODE


def validate_url_paths(paths: list[str]) -> None:

    invalid_paths = [path for path in paths if _is_path_invalid(path)]

    if invalid_paths:
        message = (
            f"Found Invalid Paths: {invalid_paths}.\n"
            "Likely caused by tournaments having their names changed."
        )
        logging.warning(message)
        raise InvalidPaths(message)

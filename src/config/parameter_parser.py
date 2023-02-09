import json
import logging
from pathlib import Path
from typing import Iterable

import bet_explorer as bet
from logs import log

JsonKey = str
JsonData = str | list[str] | dict[str, str | list[str]]
ConfigurationType = dict[JsonKey, JsonData]


def read_json_configuration(path: Path) -> ConfigurationType:
    with open(path, "r") as config_file:
        configuration = json.load(config_file)

    return configuration


def get_url_paths(url_paths_config: ConfigurationType, sports: Iterable[str]):
    """
    Get url paths depending on scraping mode.
    """

    mode: str = url_paths_config["mode"]

    if mode == "homepage":
        return bet.scrape.get_tournament_url_paths(set(sports))

    if mode == "json_list":
        return url_paths_config["list"]

    if mode == "file":
        filepath: Path = Path(url_paths_config["file"])

        with open(filepath, "r") as config_file:
            paths = json.load(config_file)

        return paths["paths"]

    logging.error(f"Invalid mode: {mode}")
    raise ValueError(
        "Only valid parameters.json modes are: ['homepage', 'json_list', 'file']."
    )

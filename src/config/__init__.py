"""
Module responsible for dealing with configuration files.

It contains both general purpose functions and adapter functions
(prepare_dataset_adapter) to connect the configuration options to
all dataset preparation modules.
"""

from . import dataset_paths as path
from . import parameter_parser as parser

__all__ = [
    "path",
    "parser",
]

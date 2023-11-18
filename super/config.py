
import functools
from typing import Callable, Any, Union
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.joinpath('super.yml')


def tagged(field_name: str) -> Callable:
    """Decorator that tags the given function with a field name. This is so
    that it can be assigned its correct config value later.

    :param field_name: Name of config field. An entry with the same field name
    should exist.
    :return: Wrapper function
    """
    def wrapper(f: Callable) -> Callable:
        f.config_field = field_name
        return f

    return wrapper


def field_name(f: Callable) -> str:
    """Get the tagged config_field, assigned by the `tagged` decorator

    :param f: Function, that should already have been tagged
    :raises AttributeError: If not tagged
    :return: Name of config field
    """
    return getattr(f, 'config_field')


def load(path: str = None) -> dict:
    """Load the config at the given path. If no path is explicitly specified,
    it will attempt to load from the default path `./super.yml`.

    :param path: Path to config file
    :return: Config, can be empty
    """
    if path is None:
        path = DEFAULT_CONFIG_PATH

    try:
        with open(path) as fp:
            conf = yaml.safe_load(fp)

            if conf is None:
                return {}

            return conf
    except FileNotFoundError:
        return {}

import argparse
import dataclasses
import os
import sys
import typing
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Literal

import toml
from loguru import logger

from creosote import formatters, parsers, resolvers
from creosote.__about__ import __version__


@dataclass
class Config:
    """Structured configuration data.

    It is important that these attributes exactly match
    the ``dest`` specified in ``add_argument``.
    """

    format: Literal["default", "no-color", "porcelain"] = "default"  # noqa: A003
    paths: List[str] = field(default_factory=lambda: ["src"])
    sections: List[str] = field(default_factory=lambda: ["project.dependencies"])
    exclude_deps: List[str] = field(default_factory=list)
    deps_file: str = "pyproject.toml"
    venvs: List[str] = field(
        default_factory=lambda: [os.environ.get("VIRTUAL_ENV", ".venv")]
    )
    features: List[str] = field(default_factory=list)


class Features(Enum):
    """Features that can be enabled via the --use-feature flag."""

    FAIL_EXCLUDED_AND_NOT_INSTALLED = "fail-excluded-and-not-installed"


class CustomAppendAction(argparse.Action):
    """Custom action to append values to a list.

    When using the `append` action, the default value is not removed
    from the list. This problem is described in
    https://github.com/python/cpython/issues/60603

    This custom action aims to fix this problem by removing the default
    value when the argument is specified for the first time.
    """

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        """Initialize the action."""
        self.called_times = 0
        self.default_value = kwargs.get("default")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        """When the argument is specified on the commandline."""
        current_values = getattr(namespace, self.dest)

        if self.called_times == 0 and current_values == self.default_value:
            current_values = []

        current_values.append(values)
        setattr(namespace, self.dest, current_values)
        self.called_times += 1


def parse_args_for_formatting(args):
    init_parser = argparse.ArgumentParser(
        add_help=False,
    )
    # Immediately parse verbosity
    init_parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help="increase output verbosity",
    )
    init_parser.add_argument(
        "-f",
        "--format",
        dest="format",
        choices=typing.get_args(Config.__annotations__["format"]),
        help="output format",
    )
    fmt_args, _ = init_parser.parse_known_args(args)
    return init_parser, fmt_args


def parse_args(init_parser: argparse.ArgumentParser, args):
    parser = argparse.ArgumentParser(
        description=(
            "Prevent bloated virtual environments by identifing installed, "
            "but unused, dependencies"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[init_parser],
    )

    parser.add_argument(
        "-V",
        "--version",
        dest="version",
        action="version",
        version=__version__,
        help="show version and exit",
    )
    parser.add_argument(
        "-p",
        "--path",
        dest="paths",
        metavar="PATH",
        action=CustomAppendAction,  # TODO: add tests for v3-args before releasing 3.0.0
        help="path(s) to Python source code to scan for imports",
    )
    parser.add_argument(
        "-s",
        "--section",
        dest="sections",
        metavar="TOML_SECTION",
        action=CustomAppendAction,  # TODO: add tests for v3-args before releasing 3.0.0
        help="pyproject.toml section(s) to scan for dependencies",
    )
    parser.add_argument(
        "--exclude-dep",
        dest="exclude_deps",
        metavar="DEPENDENCY",
        action="append",  # TODO: add tests for v3-args before releasing 3.0.0
        help="dependency(ies) to exclude from the scan",
    )
    parser.add_argument(
        "-d",
        "--deps-file",
        dest="deps_file",
        metavar="PATH",
        help="path to the pyproject.toml or requirements[.txt|.in] file",
    )
    parser.add_argument(
        "-v",
        "--venv",
        dest="venvs",
        metavar="PATH",
        action=CustomAppendAction,
        help="path(s) to the virtual environment (or site-packages)",
    )
    parser.add_argument(
        "--use-feature",
        dest="features",
        metavar="FEATURE",
        action="append",
        choices=[v.value for v in Features.__members__.values()],
        help=(
            "enable new/experimental functionality, "
            "that may be backward incompatible"
        ),
    )

    defaults = load_defaults()
    parser.set_defaults(**dataclasses.asdict(defaults))
    parsed_args = parser.parse_args(args)
    return parsed_args


def load_defaults(src: str = "pyproject.toml") -> Config:
    """Load pyproject.toml defaults form user config.

    Expects user configuration at ``[tool.creosote]``.
    """
    logger.debug(f"Attempting to load configuration from {src}")
    try:
        with open(src, "r", encoding="utf-8") as f:
            project_config = toml.loads(f.read())
        logger.debug(f"{src} configuration loaded.")
    except FileNotFoundError:
        logger.debug(f"{src} configuration file not found.")
        project_config = {}
    creosote_config = project_config.get("tool", {}).get("creosote", {})
    if creosote_config:
        logger.debug(f"Loaded creosote config: {creosote_config}")
    else:
        logger.debug("Empty/missing [tool.creosote] section.")
    # Convert all hyphens to underscores
    creosote_config = {k.replace("-", "_"): v for k, v in creosote_config.items()}
    return Config(**creosote_config)

import argparse
import os
import sys
import typing
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Literal

import toml
from loguru import logger

from creosote.__about__ import __version__


@dataclass
class Config:
    """Structured configuration data.

    It is important that these attributes exactly match
    the ``dest`` specified in ``add_argument``.
    """

    format: Literal["default", "no-color", "porcelain"] = "default"
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
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        """When the argument is specified on the commandline."""
        current_values = getattr(namespace, self.dest)

        if self.called_times == 0:
            current_values = []

        current_values.append(values)
        setattr(namespace, self.dest, current_values)
        self.called_times += 1


def show_migration_message():
    """Show warning if you are using v2.x args with v3.x code."""

    args = sys.argv[1:]
    outdated_args = ["--exclude-deps", "--paths", "--sections"]
    for outdated_arg in outdated_args:
        if outdated_arg in args:
            logger.error(
                "Creosote was updated to v3.x with breaking changes. "
                "You need to update your CLI arguments. "
                "See the migration guide at https://github.com/fredrikaverpil/creosote"
            )
            sys.exit(1)


def parse_args(args):
    show_migration_message()

    defaults = load_defaults()

    parser = argparse.ArgumentParser(
        description=(
            "Prevent bloated virtual environments by identifing installed, "
            "but unused, dependencies"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help="increase output verbosity",
    )
    parser.add_argument(
        "-f",
        "--format",
        dest="format",
        choices=typing.get_args(Config.__annotations__["format"]),
        default=defaults.format,
        help="output format",
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
        action=CustomAppendAction,
        default=defaults.paths,
        help="path(s) to Python source code to scan for imports",
    )
    parser.add_argument(
        "-s",
        "--section",
        dest="sections",
        metavar="TOML_SECTION",
        action=CustomAppendAction,
        default=defaults.sections,
        help="pyproject.toml section(s) to scan for dependencies",
    )
    parser.add_argument(
        "--exclude-dep",
        dest="exclude_deps",
        metavar="DEPENDENCY",
        action="append",
        default=defaults.exclude_deps,
        help="dependency(ies) to exclude from the scan",
    )
    parser.add_argument(
        "-d",
        "--deps-file",
        dest="deps_file",
        metavar="PATH",
        default=defaults.deps_file,
        help="path to the pyproject.toml or requirements[.txt|.in] file",
    )
    parser.add_argument(
        "-v",
        "--venv",
        dest="venvs",
        metavar="PATH",
        action=CustomAppendAction,
        default=defaults.venvs,
        help="path(s) to the virtual environment (or site-packages)",
    )
    parser.add_argument(
        "--use-feature",
        dest="features",
        metavar="FEATURE",
        action="append",
        choices=[v.value for v in Features.__members__.values()],
        default=defaults.features,
        help=(
            "enable new/experimental functionality, "
            "that may be backward incompatible"
        ),
    )

    parsed_args = parser.parse_args(args)
    return parsed_args, defaults


def load_defaults(src: str = "pyproject.toml") -> Config:
    """Load pyproject.toml defaults from user config.

    Expects user configuration at ``[tool.creosote]``.
    """

    try:
        with open(src, "r", encoding="utf-8", errors="replace") as f:
            project_config = toml.loads(f.read())
    except FileNotFoundError:
        project_config = {}
    creosote_config = project_config.get("tool", {}).get("creosote", {})
    # Convert all hyphens to underscores
    creosote_config = {k.replace("-", "_"): v for k, v in creosote_config.items()}
    return Config(**creosote_config)


def fail_fast(args: argparse.Namespace) -> bool:
    """Check if we should fail fast."""
    if is_missing_file(args.deps_file):
        logger.error(f"File not found: {args.deps_file}")
        return True
    return False


def is_missing_file(file_path: str) -> bool:
    return not Path(file_path).is_file()

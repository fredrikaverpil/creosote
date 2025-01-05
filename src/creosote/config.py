import argparse
import os
import sys
import typing
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Literal, Optional, Union

if sys.version_info >= (3, 11):
    import tomllib  # pyright: ignore[reportUnreachable]
else:
    import tomli as tomllib

from loguru import logger

from creosote.__about__ import __version__


@dataclass
class Config:
    """Structured configuration data.

    It is important that these attributes exactly match
    the ``dest`` specified in ``add_argument``.
    """

    verbose: bool = False
    format: Literal["default", "no-color", "porcelain"] = "default"
    paths: list[str] = field(default_factory=lambda: ["src"])
    sections: list[str] = field(default_factory=lambda: ["project.dependencies"])
    exclude_deps: list[str] = field(default_factory=list)
    deps_file: str = "pyproject.toml"
    venvs: list[str] = field(
        default_factory=lambda: [os.environ.get("VIRTUAL_ENV", ".venv")]
    )
    features: list[str] = field(default_factory=list)


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

    def __init__(  # type: ignore[no-untyped-def]
        self,
        option_strings: list[str],
        dest: str,
        nargs: Optional[list[str]] = None,
        **kwargs,  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
    ):
        """Initialize the action."""
        self.called_times: int = 0
        super().__init__(option_strings, dest, **kwargs)  # pyright: ignore[reportUnknownArgumentType]

    def __call__(self, parser, namespace, values, option_string=None):  # type: ignore[no-untyped-def]  # pyright: ignore[reportMissingParameterType, reportImplicitOverride]
        """When the argument is specified on the commandline."""
        current_values = getattr(namespace, self.dest)  # pyright: ignore[reportAny]

        if self.called_times == 0:
            current_values = []

        _ = current_values.append(values)  # pyright: ignore[reportUnknownMemberType]
        setattr(namespace, self.dest, current_values)
        self.called_times += 1


def show_migration_message() -> None:
    """Show warning if you are using v2.x args with v3.x code."""

    args = sys.argv[1:]
    outdated_args = ["--exclude-deps", "--paths", "--sections"]
    for outdated_arg in outdated_args:
        if outdated_arg in args:
            logger.error(
                "Creosote was updated to v3.x with breaking changes. "
                + "You need to update your CLI arguments. "
                + "See the migration guide at https://github.com/fredrikaverpil/creosote"
            )
            sys.exit(1)


def parse_args(args: Optional[Sequence[str]]) -> Config:
    show_migration_message()

    defaults = load_defaults()

    parser = argparse.ArgumentParser(
        description=(
            "Prevent bloated virtual environments by identifing installed, "
            "but unused, dependencies"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _ = parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        default=defaults.verbose,
        help="increase output verbosity",
    )
    _ = parser.add_argument(
        "-f",
        "--format",
        dest="format",
        choices=typing.get_args(Config.__annotations__["format"]),
        default=defaults.format,
        help="output format",
    )
    _ = parser.add_argument(
        "-V",
        "--version",
        dest="version",
        action="version",
        version=__version__,
        help="show version and exit",
    )
    _ = parser.add_argument(
        "-p",
        "--path",
        dest="paths",
        metavar="PATH",
        action=CustomAppendAction,
        default=defaults.paths,
        help="path(s) to Python source code to scan for imports",
    )
    _ = parser.add_argument(
        "-s",
        "--section",
        dest="sections",
        metavar="TOML_SECTION",
        action=CustomAppendAction,
        default=defaults.sections,
        help="pyproject.toml section(s) to scan for dependencies",
    )
    _ = parser.add_argument(
        "--exclude-dep",
        dest="exclude_deps",
        metavar="DEPENDENCY",
        action="append",
        default=defaults.exclude_deps,
        help="dependency(ies) to exclude from the scan",
    )
    _ = parser.add_argument(
        "-d",
        "--deps-file",
        dest="deps_file",
        metavar="PATH",
        default=defaults.deps_file,
        help="path to the pyproject.toml or requirements[.txt|.in] file",
    )
    _ = parser.add_argument(
        "-v",
        "--venv",
        dest="venvs",
        metavar="PATH",
        action=CustomAppendAction,
        default=defaults.venvs,
        help="path(s) to the virtual environment (or site-packages)",
    )
    _ = parser.add_argument(
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
    return Config(**vars(parsed_args))  # pyright: ignore[reportAny]


def load_defaults(src: Union[str, Path] = "pyproject.toml") -> Config:
    """Load pyproject.toml defaults from user config.

    Expects user configuration at ``[tool.creosote]``.
    """

    try:
        with open(src, "rb") as f:
            project_config = tomllib.load(f)
    except FileNotFoundError:
        project_config = {}
    creosote_config = project_config.get("tool", {}).get("creosote", {})  # pyright: ignore[reportAny]
    # Convert all hyphens to underscores
    creosote_config = {k.replace("-", "_"): v for k, v in creosote_config.items()}  # pyright: ignore[reportAny]
    return Config(**creosote_config)  # pyright: ignore[reportAny]


def fail_fast(args: Config) -> bool:
    """Check if we should fail fast."""
    if is_missing_file(args.deps_file):
        logger.error(f"File not found: {args.deps_file}")
        return True
    return False


def is_missing_file(file_path: str) -> bool:
    return not Path(file_path).is_file()

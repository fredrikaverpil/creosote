import argparse
import dataclasses
import sys
import toml
import typing

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Literal

from loguru import logger

from creosote import formatters, parsers, resolvers
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
    venvs: List[str] = field(default_factory=lambda: [".venv"])
    features: List[str] = field(default_factory=list)


def load_defaults(src="pyproject.toml") -> Config:
    """Load pyproject.toml defaults form user config.

    Expects user configuration at ``[tool.creosote]``.
    """
    with open(src, "r", encoding="utf-8") as f:
        project_config = toml.loads(f.read())
    creosote_config = project_config.get("tool", {}).get("creosote", {})
    # Convert all hyphens to underscores
    creosote_config = {
        k.replace("-", "_"): v
        for k, v in creosote_config.items()
    }
    return Config(**creosote_config)


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


def parse_args(args: List, defaults: Config):
    parser = argparse.ArgumentParser(
        description=(
            "Prevent bloated virtual environments by identifing installed, "
            "but unused, dependencies"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
        "--verbose",
        dest="verbose",
        action="store_true",
        help="increase output verbosity",
    )
    parser.add_argument(
        "-f",
        "--format",
        dest="format",
        choices=typing.get_args(defaults.__annotations__['format']),
        help="output format",
    )
    parser.add_argument(
        "-p",
        "--path",
        dest="paths",
        metavar="PATH",
        action=CustomAppendAction,
        help="path(s) to Python source code to scan for imports",
    )
    parser.add_argument(
        "-s",
        "--section",
        dest="sections",
        metavar="TOML_SECTION",
        action=CustomAppendAction,
        help="pyproject.toml section(s) to scan for dependencies",
    )
    parser.add_argument(
        "--exclude-dep",
        dest="exclude_deps",
        metavar="DEPENDENCY",
        action="append",
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
    parser.set_defaults(**dataclasses.asdict(defaults))

    parsed_args = parser.parse_args(args)

    return parsed_args


def main(args_=None):
    args = parse_args(args_, defaults=load_defaults())

    formatters.configure_logger(verbose=args.verbose, format_=args.format)

    logger.debug(f"Creosote version: {__version__}")
    logger.debug(f"Command: creosote {' '.join(sys.argv[1:])}")
    logger.debug(f"Arguments: {args}")

    if args.features:
        logger.info(f"Feature(s) enabled: {', '.join(args.features)}")

    # Get imports from source code
    imports = parsers.get_module_names_from_code(args.paths)

    # Read dependencies from pyproject.toml or requirements.txt
    deps_reader = parsers.DependencyReader(
        deps_file=args.deps_file,
        sections=args.sections,
        exclude_deps=args.exclude_deps,
    )
    dependency_names = deps_reader.read()

    # Warn if excluded dependencies are not installed
    excluded_deps_and_not_installed = parsers.get_excluded_deps_which_are_not_installed(
        excluded_deps=args.exclude_deps, venvs=args.venvs
    )

    # Resolve
    deps_to_scan_for = list(set(dependency_names) - set(args.exclude_deps))
    deps_resolver = resolvers.DepsResolver(
        imports=imports,
        dependency_names=deps_to_scan_for,
        venvs=args.venvs,
    )
    unused_dependency_names = deps_resolver.resolve_unused_dependency_names()

    # Print final results
    formatters.print_results(
        unused_dependency_names=unused_dependency_names, format_=args.format
    )

    # Return with exit code
    if unused_dependency_names:
        return 1
    elif excluded_deps_and_not_installed:  # noqa: SIM102
        if Features.FAIL_EXCLUDED_AND_NOT_INSTALLED.value in args.features:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

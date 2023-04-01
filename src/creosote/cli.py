import argparse
import glob
import sys
from enum import Enum

from loguru import logger

from creosote import formatters, parsers, resolvers
from creosote.__about__ import __version__


class Features(Enum):
    """Features that can be enabled via the --use-feature flag."""

    FAIL_EXCLUDED_AND_NOT_INSTALLED = "fail-excluded-and-not-installed"


def parse_args(args):
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
        default="default",
        choices=["default", "porcelain"],
        help="output format",
    )
    parser.add_argument(
        "-p",
        "--paths",
        dest="paths",
        default=glob.glob("src"),
        nargs="*",
        help="paths(s) to Python source code to scan for imports",
    )
    parser.add_argument(
        "-v",
        "--venv",
        dest="venv",
        default=".venv",
        help="path to the virtual environment to scan for dependencies",
    )
    parser.add_argument(
        "-d",
        "--deps-file",
        dest="deps_file",
        metavar="PATH",
        default="pyproject.toml",
        help="path to the pyproject.toml or requirements[.txt|.in] file",
    )
    parser.add_argument(
        "-s",
        "--sections",
        dest="sections",
        metavar="SECTION",
        nargs="*",
        default=["project.dependencies"],
        help="pyproject.toml section(s) to scan for dependencies",
    )
    parser.add_argument(
        "--exclude-deps",
        dest="exclude_deps",
        metavar="DEPENDENCY",
        nargs="*",
        default=[],
        help="dependencies to exclude from the scan",
    )
    parser.add_argument(
        "--use-feature",
        dest="features",
        metavar="FEATURE",
        action="append",
        choices=[v.value for v in Features.__members__.values()],
        default=[],
        help=(
            "enable new/experimental functionality, "
            "that may be backward incompatible"
        ),
    )

    parsed_args = parser.parse_args(args)

    return parsed_args


def main(args_=None):
    args = parse_args(args_)

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
        excluded_deps=args.exclude_deps, venv=args.venv
    )

    # Resolve
    deps_to_scan_for = list(set(dependency_names) - set(args.exclude_deps))
    deps_resolver = resolvers.DepsResolver(
        imports=imports,
        dependency_names=deps_to_scan_for,
        venv=args.venv,
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

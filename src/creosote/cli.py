import argparse
import glob
import sys
from typing import List

from loguru import logger

from creosote import formatters, parsers, resolvers
from creosote.__about__ import __version__


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
        action="store_true",
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

    parsed_args = parser.parse_args(args)

    return parsed_args


def excluded_deps_not_installed(excluded_deps: List[str], venv: str) -> List[str]:
    dependency_names = []
    if excluded_deps:
        for dep_name in excluded_deps:
            if dep_name not in parsers.get_installed_dependency_names(venv):
                dependency_names.append(dep_name)

    if dependency_names:
        logger.warning(
            "Excluded dependencies not found in virtual environment: "
            f"{', '.join(dependency_names)}"
        )
    return dependency_names


def main(args_=None):
    args = parse_args(args_)

    if args.version:
        print(__version__)
        return 0

    formatters.configure_logger(verbose=args.verbose, format_=args.format)

    logger.debug(f"Creosote version: {__version__}")
    logger.debug(f"Command: creosote {' '.join(sys.argv[1:])}")
    logger.debug(f"Arguments: {args}")

    imports = parsers.get_module_names_from_code(args.paths)
    logger.debug("Imports found in code:")
    for imp in imports:
        logger.debug(f"- {imp}")

    logger.debug(f"Parsing {args.deps_file} for dependencies...")
    deps_reader = parsers.DependencyReader(
        deps_file=args.deps_file,
        sections=args.sections,
        exclude_deps=args.exclude_deps,
    )
    dependency_names = deps_reader.read()

    logger.debug(f"Dependencies found in {args.deps_file}:")
    for dep in dependency_names:
        logger.debug(f"- {dep}")

    deps_resolver = resolvers.DepsResolver(
        imports=imports, dependency_names=dependency_names, venv=args.venv
    )
    deps_resolver.resolve()

    logger.debug(
        "Dependencies with populated 'associated_import' attribute are used in code. "
        "End result of resolve:"
    )
    for dep_info in deps_resolver.dependencies:
        logger.debug(f"- {dep_info}")

    unused_dependency_names = sorted(
        deps_resolver.get_unused_dependency_names()
        + excluded_deps_not_installed(args.exclude_deps, args.venv)
    )
    formatters.print_results(
        unused_dependency_names=unused_dependency_names, format_=args.format
    )
    return 1 if unused_dependency_names else 0  # exit code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

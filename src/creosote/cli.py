import argparse
import glob
import sys

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
        help="one or more paths to Python files",
    )
    parser.add_argument(
        "-v",
        "--venv",
        dest="venv",
        default=".venv",
        help="path to the virtual environment you want to scan",
    )

    parser.add_argument(
        "-d",
        "--deps-file",
        dest="deps_file",
        metavar="PATH",
        default="pyproject.toml",
        help="path to the pyproject.toml, requirements[.txt|.in] file",
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

    parsed_args = parser.parse_args(args)

    return parsed_args


def main(args_=None):
    args = parse_args(args_)

    if args.version:
        print(__version__)
        sys.exit(0)

    formatters.configure_logger(verbose=args.verbose, format_=args.format)

    logger.debug(f"Creosote version: {__version__}")
    logger.debug(f"Command: creosote {' '.join(sys.argv[1:])}")
    logger.debug(f"Arguments: {args}")

    imports = parsers.get_modules_from_code(args.paths)
    logger.debug("Imports found in code:")
    for imp in imports:
        logger.debug(f"- {imp}")

    logger.debug(f"Parsing {args.deps_file} for packages...")
    deps_reader = parsers.PackageReader()
    deps_reader.read(args.deps_file, args.sections)

    logger.debug(f"Packages found in {args.deps_file}:")
    for package in deps_reader.packages:
        logger.debug(f"- {package}")

    deps_resolver = resolvers.DepsResolver(
        imports=imports, packages=deps_reader.packages or [], venv=args.venv
    )
    deps_resolver.resolve()

    logger.debug(
        "Packages with populated 'associated_import' attribute are used in code. "
        "End result of resolve:"
    )
    for package in deps_resolver.packages:
        logger.debug(f"- {package}")

    formatters.print_results(deps_resolver=deps_resolver, format_=args.format)


if __name__ == "__main__":
    main(sys.argv[1:])

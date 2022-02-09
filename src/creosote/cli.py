import argparse
import glob
import sys

from loguru import logger

from creosote import formatters, parsers, resolvers


def parse_args(args):
    parser = argparse.ArgumentParser(
        description=(
            "Prevent bloated virtual environments by identifing installed, "
            "but unused, dependencies."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Increase output verbosity.",
    )
    parser.add_argument(
        "-f",
        "--format",
        dest="format",
        default="logger",
        choices=["logger", "porcelain"],
        help="Output format.",
    )
    parser.add_argument(
        "-p",
        "--paths",
        dest="paths",
        default=glob.glob("src/**/*.py"),
        nargs="*",
        help=("One or more paths to Python files (glob pattern supported)."),
    )
    parser.add_argument(
        "-d",
        "--deps-file",
        dest="deps_file",
        default="pyproject.toml",
        choices=["pyproject.toml"],
        help="The file to read dependencies from.",
    )
    parser.add_argument(
        "-v",
        "--venv",
        dest="venv",
        default=".venv",
        help="Path to the virtual environment you want to scan.",
    )

    return parser.parse_args(args)


def main(args_=None):
    args = parse_args(args_)

    formatters.configure_logger(verbose=args.verbose, format_=args.format)

    imports = parsers.get_modules_from_code(args.paths)
    logger.debug("Imports found:")
    for imp in imports:
        logger.debug(imp)

    logger.info(f"Parsing {args.deps_file} for packages")
    deps_reader = parsers.PackageReader()
    deps_reader.read(args.deps_file)

    logger.info("Resolving...")

    deps_resolver = resolvers.DepsResolver(
        imports=imports, packages=deps_reader.packages or [], venv=args.venv
    )

    deps_resolver.resolve()

    logger.debug("Packages:")
    for package in deps_resolver.packages:
        logger.debug(package)

    formatters.print_results(deps_resolver=deps_resolver, format_=args.format)


if __name__ == "__main__":
    main(sys.argv[1:])

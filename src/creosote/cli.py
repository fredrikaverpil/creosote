import argparse
import glob
import sys

from loguru import logger

from creosote import formatters, parsers, resolvers


def parse_args(args):
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
        help=("one or more paths to Python files"),
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
        help="path to the pyproject.toml, *.txt or *.in dependencies file",
    )

    parser.add_argument(
        "--dev",
        dest="dev",
        action="store_true",
        help="scan dev dependencies instead of prod dependencies",
    )

    parsed_args = parser.parse_args(args)

    if "pyproject.toml" not in parsed_args.deps_file and parsed_args.dev:
        raise Exception("Option --dev must be used with pyproject.toml")

    return parsed_args


def main(args_=None):
    args = parse_args(args_)

    formatters.configure_logger(verbose=args.verbose, format_=args.format)

    imports = parsers.get_modules_from_code(args.paths)
    logger.debug("Imports found:")
    for imp in imports:
        logger.debug(imp)

    logger.info(f"Parsing {args.deps_file} for packages")
    deps_reader = parsers.PackageReader()
    deps_reader.read(args.deps_file, args.dev)

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

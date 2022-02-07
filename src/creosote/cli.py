import argparse
import glob
import sys

from loguru import logger

from creosote import parsers, resolvers


def parse_args():
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

    return parser.parse_args()


def configure_logger(verbose: bool):
    if not verbose:
        logger.remove()
        logger.add(sys.stderr, level="INFO")


def main():
    args = parse_args()

    configure_logger(args.verbose)

    imports = parsers.get_modules_from_code(args.paths)
    logger.debug("Imports found:")
    for imp in imports:
        logger.debug(imp)

    logger.info(f"Parsing {args.deps_file} for packages")
    deps_reader = parsers.PackageReader()
    deps_reader.read(args.deps_file)

    logger.info("Resolving...")
    if deps_reader.packages:
        deps_resolver = resolvers.DepsResolver(
            imports=imports,
            packages=deps_reader.packages,
            venv=args.venv,
        )

        deps_resolver.resolve()

        logger.debug("Packages:")
        for package in deps_resolver.packages:
            logger.debug(package)

        if unused_packages := deps_resolver.get_unused_package_names():
            logger.error(f"Unused packages found: {', '.join(unused_packages)}")
            sys.exit(1)
        else:
            logger.info("No unused packages found.")
    logger.info("No packages found.")


if __name__ == "__main__":
    main()

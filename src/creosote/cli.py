import argparse
import glob

from loguru import logger

from creosote import parsers
from creosote.depsreader import DepsReader
from creosote.resolvers import DepsResolver


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Prevent bloated virtual environments by identifing installed, "
            "but unused, dependencies."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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

    return parser.parse_args()


def main():
    args = parse_args()
    logger.debug(f"Arguments given: {args}")

    modules = parsers.get_modules_from_code(args.paths)
    logger.debug(f"Modules: {modules}")

    deps_reader = DepsReader()
    deps_reader.read(args.deps_file)
    logger.debug(f"Packages: {deps_reader.packages}")

    deps_resolver = DepsResolver()
    deps_resolver.resolve(modules=modules, packages=deps_reader.packages)
    logger.debug(f"Unused packages: {deps_resolver.unused_packages}")


if __name__ == "__main__":
    main()

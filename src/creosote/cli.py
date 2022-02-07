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
        "--paths",
        dest="paths",
        default=glob.glob("src/**/*.py"),
        nargs="*",
        help=("One or more paths to Python files (glob pattern supported)."),
    )
    parser.add_argument(
        "--deps-file",
        dest="deps_file",
        default="pyproject.toml",
        choices=["pyproject.toml"],
        help="The file to read dependencies from.",
    )
    parser.add_argument(
        "--venv",
        dest="venv",
        default=".venv",
        help="Path to the virtual environment you want to scan.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    imports = parsers.get_modules_from_code(args.paths)
    logger.debug("Imports found:")
    for imp in imports:
        logger.debug(imp)

    deps_reader = parsers.PackageReader()
    deps_reader.read(args.deps_file)

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

        unused_packages = [
            package.name
            for package in deps_resolver.packages
            if not package.associated_imports
        ]

        if unused_packages:
            logger.error(f"Unused packages found: {', '.join(unused_packages)}")
            sys.exit(1)
        else:
            logger.info("No unused packages found.")


if __name__ == "__main__":
    main()

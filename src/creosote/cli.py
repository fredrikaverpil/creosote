import argparse
import glob

from loguru import logger

from creosote import parsers


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
        "--dependencies",
        dest="dependencies",
        default="pyproject.toml",
        choices=["pyproject.toml"],
        help="The requirement file to use.",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    logger.debug(f"Arguments given: {args}")

    imports = parsers.get_modules_from_code(args.paths)
    logger.debug(f"Imports: {imports}")


if __name__ == "__main__":
    main()

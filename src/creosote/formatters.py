import sys
from typing import List

from loguru import logger


def configure_logger(verbose: bool, format_: str):
    logger.remove()

    if format_ == "porcelain":
        logger.add(sys.stderr, level="CRITICAL")
        return
    else:
        logger.add(
            sys.stderr,
            level="DEBUG" if verbose else "INFO",
            colorize=True,
            format="<level>{message}</level>",
        )


def print_results(unused_packages: List[str], format_: str) -> None:
    if unused_packages:
        if format_ == "porcelain":
            print("\n".join(unused_packages))
        else:
            logger.error(
                "Oh no, bloated venv! 🤢 🪣\n"
                f"Unused packages found: {', '.join(unused_packages)}"
            )
    else:
        logger.info("No unused packages found! ✨")

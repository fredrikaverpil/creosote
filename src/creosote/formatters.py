import sys
from typing import List

from loguru import logger


def configure_logger(verbose: bool, format_: str) -> None:
    logger.remove()

    if format_ == "porcelain":
        logger.add(sys.stderr, level="CRITICAL")
        return
    if format_ == "no-color":
        logger.add(
            sys.stderr,
            level="DEBUG" if verbose else "INFO",
            colorize=False,
            format="<level>{message}</level>",
        )
    else:
        # default
        logger.add(
            sys.stderr,
            level="DEBUG" if verbose else "INFO",
            colorize=True,
            format="<level>{message}</level>",
        )


def print_results(unused_dependency_names: List[str], format_: str) -> None:
    if unused_dependency_names:
        if format_ == "porcelain":
            print("\n".join(unused_dependency_names))
        else:
            logger.error(
                "Oh no, bloated venv! 🤢 🪣\n"
                f"Unused dependencies found: {', '.join(unused_dependency_names)}"
            )
    else:
        logger.info("No unused dependencies found! ✨")

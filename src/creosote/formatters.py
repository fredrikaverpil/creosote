import sys

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


def print_results(deps_resolver, format_: str):
    unused_packages = deps_resolver.get_unused_package_names()
    if unused_packages:
        if format_ == "porcelain":
            print("\n".join(unused_packages))
        else:
            logger.error(f"Unused packages found: {', '.join(unused_packages)}")
        # sys.exit(1)
    else:
        logger.info("No unused packages found.")

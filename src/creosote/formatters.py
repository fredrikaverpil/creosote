import sys

from loguru import logger


def configure_logger(verbose: bool, format_: str):
    if format_ == "porcelain":
        logger.remove()
        logger.add(sys.stderr, level="CRITICAL")
        return

    if not verbose:
        logger.remove()
        logger.add(sys.stderr, level="INFO")


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

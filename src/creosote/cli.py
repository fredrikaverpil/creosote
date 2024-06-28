import sys

from loguru import logger

from creosote import formatters, parsers, resolvers
from creosote.__about__ import __version__
from creosote.config import Features, fail_fast, parse_args


def main(args_=None):
    args, default_config = parse_args(args_)
    if fail_fast(args):
        return 1
    formatters.configure_logger(verbose=args.verbose, format_=args.format)

    logger.debug(f"Creosote version: {__version__}")
    logger.debug(f"Command: creosote {' '.join(sys.argv[1:])}")
    logger.debug(
        f"Default configuration (may have loaded pyproject.toml): {default_config}"
    )
    logger.debug(f"Arguments: {args}")

    if args.features:
        logger.info(f"Feature(s) enabled: {', '.join(args.features)}")

    # Get imports from source code
    imports = parsers.get_module_names_from_code(args.paths)

    # Read dependencies from pyproject.toml or requirements.txt
    deps_reader = parsers.DependencyReader(
        deps_file=args.deps_file,
        sections=args.sections,
        exclude_deps=args.exclude_deps,
    )
    dependency_names = deps_reader.read()

    # Warn if excluded dependencies are not installed
    excluded_deps_and_not_installed = parsers.get_excluded_deps_which_are_not_installed(
        excluded_deps=args.exclude_deps, venvs=args.venvs
    )

    # Resolve
    deps_to_scan_for = list(set(dependency_names) - set(args.exclude_deps))
    deps_resolver = resolvers.DepsResolver(
        imports=imports,
        dependency_names=deps_to_scan_for,
        venvs=args.venvs,
    )
    unused_dependency_names = deps_resolver.resolve_unused_dependency_names()

    # Print final results
    formatters.print_results(
        unused_dependency_names=unused_dependency_names, format_=args.format
    )

    # Return with exit code
    if unused_dependency_names:
        return 1
    elif excluded_deps_and_not_installed:  # noqa: SIM102
        if Features.FAIL_EXCLUDED_AND_NOT_INSTALLED.value in args.features:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

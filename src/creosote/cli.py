import sys
from collections.abc import Sequence

from loguru import logger

from creosote import formatters, models, parsers, resolvers
from creosote.__about__ import __version__
from creosote.config import Features, fail_fast, parse_args


def get_unnecessary_excludes(
    deps_reader: parsers.DependencyReader,
    imports: list[models.ImportInfo],
    exclude_deps: list[str],
    venvs: list[str],
    deps_file: str,
) -> list[str]:
    """Return excluded deps that don't need to be excluded, with a warning per entry."""
    unnecessary: list[str] = []
    all_dep_names = deps_reader.read_unfiltered()
    excluded_direct_deps = [d for d in exclude_deps if d in all_dep_names]
    excluded_unused = set(
        resolvers.DepsResolver(
            imports=imports,
            dependency_names=excluded_direct_deps,
            venvs=venvs,
        ).resolve_unused_dependency_names()
    )
    for d in exclude_deps:
        if d not in all_dep_names:
            unnecessary.append(d)
            logger.warning(
                f"Unnecessary exclusion '{d}': not found in {deps_file} "
                "(transitive dependency or typo)"
            )
        elif d not in excluded_unused:
            unnecessary.append(d)
            logger.warning(
                f"Unnecessary exclusion '{d}': import detected in source code"
            )
    return unnecessary


def main(args_: Sequence[str] | None = None) -> int:
    args = parse_args(args_)
    if fail_fast(args):
        return 1
    formatters.configure_logger(verbose=args.verbose, format_=args.format)

    logger.debug(f"Creosote version: {__version__}")
    logger.debug(f"Command: creosote {' '.join(sys.argv[1:])}")
    logger.debug(f"Arguments: {args}")

    if args.features:
        logger.info(f"Feature(s) enabled: {', '.join(args.features)}")

    # Get imports from source code
    imports = parsers.get_module_names_from_code(
        args.paths, include_deferred=args.include_deferred
    )

    # Get imports from Django settings file
    if args.django_settings:
        django_imports = parsers.get_modules_from_django_settings(args.django_settings)
        imports.extend(
            [
                models.ImportInfo.from_module_name(django_import)
                for django_import in django_imports
            ]
        )

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

    # Check for unnecessary excludes (experimental feature)
    unnecessary_excludes = (
        get_unnecessary_excludes(
            deps_reader=deps_reader,
            imports=imports,
            exclude_deps=args.exclude_deps,
            venvs=args.venvs,
            deps_file=args.deps_file,
        )
        if args.exclude_deps
        else []
    )

    # Print final results
    formatters.print_results(
        unused_dependency_names=unused_dependency_names, format_=args.format
    )

    # Return with exit code
    if unused_dependency_names:
        return 1
    elif excluded_deps_and_not_installed:
        if Features.FAIL_EXCLUDED_AND_NOT_INSTALLED.value in args.features:
            return 1
    elif unnecessary_excludes:  # noqa: SIM102
        if Features.FAIL_UNNECESSARY_EXCLUDES.value in args.features:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

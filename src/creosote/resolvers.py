import pathlib
import re
from pathlib import Path

from loguru import logger

from creosote.models import DependencyInfo, ImportInfo

# Define the PEP 440 compliant version pattern (non-capturing)
# https://packaging.python.org/en/latest/specifications/version-specifiers/
VERSION_PATTERN_STR = (
    r"v?(?:(?:[0-9]+!)?"  # epoch
    r"(?:[0-9]+(?:\.[0-9]+)*)"  # release
    r"(?:(?:[-_\.]?(?:a|b|c|rc|alpha|beta|pre|preview)[-_\.]?(?:[0-9]+)?))?"  # pre
    r"(?:(?:-(?:[0-9]+))|(?:[-_\.]?(?:post|rev|r)[-_\.]?(?:[0-9]+)?))?"  # post
    r"(?:(?:[-_\.]?(?:dev)[-_\.]?(?:[0-9]+)?))?)"  # dev
    r"(?:\+[a-z0-9]+(?:[-_\.][a-z0-9]+)*)?"  # local
)


class DepsResolver:
    def __init__(
        self,
        imports: list[ImportInfo],
        dependency_names: list[str],
        venvs: list[str],
    ):
        # full import path -> imports with exactly that path / starting with it
        self.imports_by_path: dict[tuple[str, ...], list[ImportInfo]] = {}
        self.imports_by_prefix: dict[tuple[str, ...], list[ImportInfo]] = {}
        for imp in imports:
            full = imp.module + imp.name
            self.imports_by_path.setdefault(full, []).append(imp)
            for i in range(1, len(full) + 1):
                self.imports_by_prefix.setdefault(full[:i], []).append(imp)
        self.dependencies: list[DependencyInfo] = [
            DependencyInfo(name=dep) for dep in dependency_names
        ]
        self.venvs: list[str] = venvs

        # Capture package names before PEP 440 compliant versions.
        # Package name allows letters, numbers, underscore, dot, hyphen.
        # Version part uses the non-capturing pattern defined above.
        # re.IGNORECASE handles version specifier case (e.g., rc vs RC).
        self.top_level_txt_pattern: re.Pattern[str] = re.compile(
            rf"\/([\w\.-]+)-(?:{VERSION_PATTERN_STR})\.dist-info\/top_level\.txt",
            re.IGNORECASE,
        )
        self.record_pattern: re.Pattern[str] = re.compile(
            rf"\/([\w\.-]+)-(?:{VERSION_PATTERN_STR})\.dist-info\/RECORD", re.IGNORECASE
        )

        self.top_level_filepaths: list[pathlib.Path] = []
        self.record_filepaths: list[pathlib.Path] = []
        self.unused_deps: list[DependencyInfo] = []

    @staticmethod
    def canonicalize_module_name(module_name: str) -> str:
        return module_name.replace("-", "_").replace(".", "_").strip()

    def is_importable(self, module_name: str) -> bool:
        try:
            __import__(self.canonicalize_module_name(module_name))
            return True
        except ImportError:
            return False

    def gather_filepaths(self, venv: str, glob_str: str) -> list[Path]:
        logger.debug(f"Gathering all top_level.txt files in venv {venv}...")
        venv_path = pathlib.Path(venv)
        filepaths = list(venv_path.glob(glob_str))
        for filepath in filepaths:
            logger.debug(f"Found {filepath}")
        return sorted(set(filepaths))

    def gather_top_level_filepaths(self, venv: str) -> None:
        """Gathers all top_level.txt filepaths in the venv.

        Note:
            The path may contain case sensitive variations of the
            dependency name, like e.g. GitPython for gitpython.
        """

        glob_str = "**/*.dist-info/top_level.txt"
        self.top_level_filepaths = self.gather_filepaths(venv=venv, glob_str=glob_str)

    def gather_record_filepaths(self, venv: str) -> None:
        """Gathers all RECORD filepaths in the venv.

        Note:
            The path may contain case sensitive variations of the
            dependency name, like e.g. GitPython for gitpython.
        """
        glob_str = "**/*.dist-info/RECORD"
        self.record_filepaths = self.gather_filepaths(venv=venv, glob_str=glob_str)

    def map_dep_to_import_via_top_level_txt_file(
        self, dep_info: DependencyInfo
    ) -> bool:
        """Map dependency to import via top_level.txt file.

        Return True if import name was found in the top_level.txt,
        otherwise return False.
        """

        for top_level_filepath in self.top_level_filepaths:
            normalized_top_level_filepath = top_level_filepath.as_posix()
            matches: list[str] = self.top_level_txt_pattern.findall(
                normalized_top_level_filepath
            )
            for name_from_top_level in matches:
                if (
                    self.canonicalize_module_name(name_from_top_level).lower()
                    == self.canonicalize_module_name(dep_info.name).lower()
                ):
                    with open(
                        top_level_filepath, encoding="utf-8", errors="replace"
                    ) as infile:
                        lines = infile.readlines()
                    dep_info.top_level_import_names = [line.strip() for line in lines]
                    import_names = ", ".join(dep_info.top_level_import_names)
                    logger.debug(
                        f"[{dep_info.name}] found import name(s) "
                        + f"via top_level.txt: {import_names} ⭐️"
                    )
                    return True
        logger.debug(f"[{dep_info.name}] did not find dep in a top_level.txt file")
        return False

    def map_dep_to_import_via_record_file(self, dep_info: DependencyInfo) -> bool:
        for record_filepath in self.record_filepaths:
            normalized_record_filepath = record_filepath.as_posix()
            matches: list[str] = self.record_pattern.findall(normalized_record_filepath)
            for name_from_record in matches:
                if (
                    self.canonicalize_module_name(name_from_record).lower()
                    == self.canonicalize_module_name(dep_info.name).lower()
                ):
                    with open(
                        record_filepath, encoding="utf-8", errors="replace"
                    ) as infile:
                        lines = infile.readlines()

                    import_names_found = self.import_names_from_record_lines(lines)
                    if import_names_found:
                        dep_info.record_import_names = import_names_found

                        import_names = ",".join(dep_info.record_import_names)
                        logger.debug(
                            f"[{dep_info.name}] found import name "
                            + f"via RECORD: {import_names} ⭐️"
                        )
                        return True

        logger.debug(f"[{dep_info.name}] did not find dep in a RECORD file")
        return False

    @staticmethod
    def import_names_from_record_lines(lines: list[str]) -> list[str]:
        """Return the topmost regular packages listed in a RECORD file.

        Directories without an __init__ module are treated as PEP 420
        namespace packages, so e.g. google/cloud/storage/__init__.py
        yields "google.cloud.storage" rather than "google". Modules
        directly inside a namespace package yield their own path, e.g.
        opentelemetry/propagators/textmap.py yields
        "opentelemetry.propagators.textmap".
        """
        modules: list[tuple[tuple[str, ...], str]] = []
        for line in lines:
            *path_dirs, filename = line.split(",")[0].replace("\\", "/").split("/")
            stem = filename[:-3] if filename.endswith(".py") else filename.split(".")[0]
            if (
                path_dirs
                and all(d.isidentifier() for d in path_dirs)
                and filename.endswith((".py", ".so", ".pyd"))
                and stem.isidentifier()
            ):
                modules.append((tuple(path_dirs), stem))
        init_dirs = {dirs for dirs, stem in modules if stem == "__init__"}
        import_names_found: dict[str, None] = {}
        for dirs, stem in modules:
            parts = dirs if stem == "__init__" else (*dirs, stem)
            topmost = next(
                (parts[:i] for i in range(1, len(parts)) if parts[:i] in init_dirs),
                parts,
            )
            import_names_found[".".join(topmost)] = None
        return list(import_names_found)

    def map_dep_to_canonical_name(self, dep_info: DependencyInfo) -> str:
        return self.canonicalize_module_name(dep_info.name)

    def populate_dependency_info(self) -> None:
        """Populate DependencyInfo object with import naming info.

        There are three strategies from where the import name can be
        found:
            1. In the top_level.txt file in the venv.
            2. From the RECORD file in the venv.
            3. Guess the import name by canonicalizing the dep name.

        Later, these gathered import names will be compared against the
        imports found in the source code by the AST parser.
        """
        logger.debug("Attempting to find import names...")

        for dep_info in self.dependencies:
            # find the import name in the top_level.txt file
            found_via_top_level_txt = self.map_dep_to_import_via_top_level_txt_file(
                dep_info
            )

            # find the import name in the RECORD file
            found_via_record = self.map_dep_to_import_via_record_file(dep_info)

            # this is really just guessing, but it's better than nothing
            dep_info.canonicalized_dep_name = self.map_dep_to_canonical_name(dep_info)

            if not found_via_top_level_txt and not found_via_record:
                logger.debug(
                    f"[{dep_info.name}] relying on canonicalization "
                    + f"fallback: {dep_info.canonicalized_dep_name} 🤞"
                )

    def associate_dep_with_import(
        self, dep_info: DependencyInfo, import_name: str
    ) -> None:
        parts = tuple(import_name.split("."))
        # imports at or below import_name, e.g. google.cloud.storage.Client
        dep_info.associated_imports.extend(self.imports_by_prefix.get(parts, []))
        # imports of a parent namespace, e.g. google.cloud
        for i in range(1, len(parts)):
            dep_info.associated_imports.extend(self.imports_by_path.get(parts[:i], []))

    def resolve(self) -> None:
        """Associate dependency name with import (module) name.

        The AST has found imports from the source code. This function
        will now attempt to associate these imports with the
        DependencyInfo data, gathered from the venv's top_level.txt,
        the RECORD and a best-guess.
        """
        for dep_info in self.dependencies:
            record_names = dep_info.record_import_names or []
            fallback_names = list(dep_info.top_level_import_names or [])
            if dep_info.canonicalized_dep_name:
                fallback_names.append(dep_info.canonicalized_dep_name)

            import_names = dict.fromkeys(
                [
                    *record_names,
                    *(
                        name
                        for name in fallback_names
                        if not any(r.startswith(f"{name}.") for r in record_names)
                    ),
                ]
            )
            for import_name in import_names:
                self.associate_dep_with_import(dep_info, import_name)

    def get_unused_dependencies(self) -> None:
        self.unused_deps = [
            dep_info
            for dep_info in self.dependencies
            if not dep_info.associated_imports
        ]

    def resolve_unused_dependency_names(self) -> list[str]:
        for venv in self.venvs:
            if not Path(venv).exists():
                logger.warning(
                    f"Virtual environment(s) '{', '.join(self.venvs)}' does not exist, "
                    + "cannot resolve top-level names. "
                    + "This may lead to incorrect results."
                )
            self.gather_top_level_filepaths(venv=venv)
            self.gather_record_filepaths(venv=venv)

        self.populate_dependency_info()
        self.resolve()
        self.get_unused_dependencies()

        logger.debug(
            "Dependencies with populated 'associated_import' attribute are used in "
            + "code. End result of resolve:"
        )
        for dep_info in self.dependencies:
            logger.debug(f"- {dep_info}")

        unused_dependency_names = sorted(
            [dep_info.name for dep_info in self.unused_deps]
        )

        return unused_dependency_names

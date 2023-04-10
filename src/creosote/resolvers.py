import os
import pathlib
import re
from pathlib import Path
from typing import List

from loguru import logger

from creosote.models import DependencyInfo, ImportInfo


class DepsResolver:
    def __init__(
        self,
        imports: List[ImportInfo],
        dependency_names: List[str],
        venvs: List[str],
    ):
        self.imports: List[ImportInfo] = imports
        self.dependencies: List[DependencyInfo] = [
            DependencyInfo(name=dep) for dep in dependency_names
        ]
        self.venvs: List[str] = venvs

        self.top_level_txt_pattern = re.compile(
            r"\/([\w]*).[\d\.]*.dist-info\/top_level.txt"
        )
        self.record_pattern = re.compile(r"\/([\w]*).[\d\.]*.dist-info\/RECORD")

        self.top_level_filepaths: List[pathlib.Path] = []
        self.record_filepaths: List[pathlib.Path] = []
        self.unused_deps: List[DependencyInfo] = []

    @staticmethod
    def canonicalize_module_name(module_name: str) -> str:
        return module_name.replace("-", "_").replace(".", "_").strip()

    def is_importable(self, module_name: str) -> bool:
        try:
            __import__(self.canonicalize_module_name(module_name))
            return True
        except ImportError:
            return False

    def gather_filepaths(self, venv: str, glob_str: str) -> List[Path]:
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
        dep_name = self.canonicalize_module_name(dep_info.name)

        for top_level_filepath in self.top_level_filepaths:
            normalized_top_level_filepath = top_level_filepath.as_posix()
            matches = self.top_level_txt_pattern.findall(normalized_top_level_filepath)
            for import_name_from_top_level in matches:
                if import_name_from_top_level.lower() == dep_name.lower():
                    with open(top_level_filepath, "r", encoding="utf-8") as infile:
                        lines = infile.readlines()
                    dep_info.top_level_import_names = [line.strip() for line in lines]
                    import_names = ", ".join(dep_info.top_level_import_names)
                    logger.debug(
                        f"[{dep_info.name}] found import name(s) "
                        f"via top_level.txt: {import_names} ⭐️"
                    )
                    return True
        logger.debug(f"[{dep_info.name}] did not find top_level.txt in venv")
        return False

    def map_dep_to_import_via_record_file(self, dep_info: DependencyInfo) -> bool:
        dep_name = self.canonicalize_module_name(dep_info.name)

        for record_filepath in self.record_filepaths:
            normalized_record_filepath = record_filepath.as_posix()
            matches = self.record_pattern.findall(normalized_record_filepath)
            for import_name_from_record in matches:
                if import_name_from_record.lower() == dep_name.lower():
                    with open(record_filepath, "r", encoding="utf-8") as infile:
                        lines = infile.readlines()

                    import_names_found = []
                    for line in lines:
                        candidate, _hash, _size = line.split(",")
                        if candidate.endswith(".py") and "__init__" in candidate:
                            import_name = candidate.split(os.sep)[0]
                            if import_name not in import_names_found:
                                import_names_found.append(import_name)

                            dep_info.record_import_names = import_names_found

                            import_names = ",".join(dep_info.record_import_names)
                            logger.debug(
                                f"[{dep_info.name}] found import name "
                                f"via RECORD: {import_names} ⭐️"
                            )
                            return True

        logger.debug(f"[{dep_info.name}] did not find RECORD in venv")
        return False

    def map_dep_to_canonical_name(self, dep_info: DependencyInfo) -> str:
        return self.canonicalize_module_name(dep_info.name)

    def populate_dependency_info(self):
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
                    f"fallback: {dep_info.canonicalized_dep_name } 🤞"
                )

    def associate_dep_with_import(self, dep_info: DependencyInfo, import_name: str):
        for imp in self.imports.copy():
            if not imp.module and import_name in imp.name:  # noqa: SIM114
                # import <imp.name>
                dep_info.associated_imports.append(imp)

            elif imp.name and import_name in imp.module:
                # from <imp.name> import ...
                dep_info.associated_imports.append(imp)

    def resolve(self):
        """Associate dependency name with import (module) name.

        The AST has found imports from the source code. This function
        will now attempt to associate these imports with the
        DependencyInfo data, gathered from the venv's top_level.txt,
        the RECORD and a best-guess.
        """
        for dep_info in self.dependencies:
            if dep_info.top_level_import_names:
                for top_level_import_name in dep_info.top_level_import_names:
                    self.associate_dep_with_import(dep_info, top_level_import_name)
            if dep_info.record_import_names:
                for record_import_name in dep_info.record_import_names:
                    self.associate_dep_with_import(dep_info, record_import_name)
            if dep_info.canonicalized_dep_name:
                self.associate_dep_with_import(
                    dep_info, dep_info.canonicalized_dep_name
                )

    def get_unused_dependencies(self) -> None:
        self.unused_deps = [
            dep_info
            for dep_info in self.dependencies
            if not dep_info.associated_imports
        ]

    def resolve_unused_dependency_names(self) -> List[str]:
        for venv in self.venvs:
            if not Path(venv).exists():
                logger.warning(
                    f"Virtual environment(s) '{', '.join(self.venvs)}' does not exist, "
                    "cannot resolve top-level names. "
                    "This may lead to incorrect results."
                )
            self.gather_top_level_filepaths(venv=venv)
            self.gather_record_filepaths(venv=venv)

        self.populate_dependency_info()
        self.resolve()
        self.get_unused_dependencies()

        logger.debug(
            "Dependencies with populated 'associated_import' attribute are used in "
            "code. End result of resolve:"
        )
        for dep_info in self.dependencies:
            logger.debug(f"- {dep_info}")

        unused_dependency_names = sorted(
            [dep_info.name for dep_info in self.unused_deps]
        )

        return unused_dependency_names

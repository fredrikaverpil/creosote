import ast
import re
from pathlib import Path
from typing import Any, Dict, Generator, List, Union, cast

import toml
from dotty_dict import Dotty, dotty
from loguru import logger
from pip_requirements_parser import RequirementsFile

from creosote.models import ImportInfo


class DependencyReader:
    """Read dependencies from various dependency file formats."""

    def __init__(
        self,
        deps_file: str,
        sections: List[str],
        exclude_deps: List[str],
    ) -> None:
        always_excluded_deps = ["python"]  # occurs in Poetry setup

        self.deps_file = deps_file
        self.sections = sections
        self.exclude_deps = exclude_deps + always_excluded_deps

    def read(self) -> List[str]:
        logger.debug(f"Parsing {self.deps_file} for dependencies...")

        if not Path(self.deps_file).exists():
            raise Exception(f"File {self.deps_file} does not exist")

        dep_names = []
        always_excluded_deps = ["python"]  # occurs in Poetry setup
        deps_to_exclude = always_excluded_deps + self.exclude_deps

        if self.deps_file.endswith(".toml") or self.deps_file.endswith(
            "Pipfile"
        ):  # pyproject.toml or Pipfile expected
            for dep_name in self.read_toml(self.deps_file, self.sections):
                if dep_name not in deps_to_exclude:
                    dep_names.append(dep_name)
        elif self.deps_file.endswith(".txt") or self.deps_file.endswith(".in"):
            for dep_name in self.read_requirements(self.deps_file):
                if dep_name not in deps_to_exclude:
                    dep_names.append(dep_name)
        else:
            raise NotImplementedError(
                f"Dependency specs file {self.deps_file} is not supported."
            )

        logger.info(
            f"Found dependencies in {self.deps_file}: " f"{', '.join(dep_names)}"
        )

        return dep_names

    def get_deps_from_pep621_toml(
        self, section_contents: Union[List[str], Dict[str, List[str]]]
    ) -> List[str]:
        """Get dependency names from toml file using the PEP621 spec.

        The dependency strings are expected to follow PEP508.
        """

        dep_strings = []
        if isinstance(section_contents, list):
            for dep_string in section_contents:
                dep_strings.append(dep_string)
        elif isinstance(section_contents, dict):
            for _, dep_string_list in section_contents.items():
                for dep_string in dep_string_list:
                    dep_strings.append(dep_string)
        else:
            raise TypeError("Unexpected dependency format, list expected.")

        section_deps = []
        for dep_string in dep_strings:
            parsed_dep = self.parse_dep_string(dep_string)
            if parsed_dep:
                section_deps.append(parsed_dep)
            else:
                logger.warning(f"Could not parse dependency string: {dep_string}")

        return section_deps

    def get_deps_from_toml_section_keys(
        self,
        section_contents: Dict[str, Any],
    ):
        """Get dependency names from toml section's dict keys."""
        if not isinstance(section_contents, dict):
            raise TypeError("Unexpected dependency format, dict expected.")
        return section_contents.keys()

    def read_toml(self, deps_file: str, sections: List[str]) -> List[str]:
        """Read dependency names from toml spec file."""
        with open(deps_file, "r", encoding="utf-8", errors="replace") as infile:
            contents = toml.loads(infile.read())

        dotty_contents: Dotty = dotty(contents)
        dep_names = []

        for section in sections:
            try:
                section_contents = dotty_contents[section]
            except KeyError as err:
                raise KeyError(f"Could not find toml section {section}.") from err

            logger.debug(f"{sections}: {section_contents}")

            section_dep_names = []
            if section.startswith("project"):
                logger.debug(f"Detected PEP-621 toml section in {deps_file}")
                section_dep_names = self.get_deps_from_pep621_toml(section_contents)
            elif section.startswith("tool.pdm"):
                logger.debug(f"Detected PDM toml section in {deps_file}")
                section_dep_names = self.get_deps_from_pep621_toml(section_contents)
            elif section.startswith("tool.poetry"):
                logger.debug(f"Detected Poetry toml section in {deps_file}")
                section_dep_names = self.get_deps_from_toml_section_keys(
                    cast(dict, section_contents)
                )
            elif section.startswith("packages") or section.startswith("dev-packages"):
                logger.debug(f"Detected pipenv/Pipfile toml section in {deps_file}")
                section_dep_names = self.get_deps_from_toml_section_keys(
                    cast(dict, section_contents)
                )
            else:
                raise TypeError("Unsupported dependency format.")

            if not section_dep_names:
                logger.warning(f"No dependencies found in section {section}")
            else:
                dep_names.extend(section_dep_names)

        return sorted(dep_names)

    def read_requirements(self, deps_file: str) -> List[str]:
        """Read dependency names from requirements.txt-format file."""
        dep_from_req = RequirementsFile.from_file(deps_file).requirements
        return sorted([dep.name for dep in dep_from_req if dep.name is not None])

    @staticmethod
    def parse_dep_string(dep: str) -> Union[str, None]:
        if "@" in dep:
            return DependencyReader.dependency_without_direct_reference(dep)
        else:
            return DependencyReader.dependency_without_version_constraint(dep)

    @staticmethod
    def dependency_without_version_constraint(
        dependency_string: str,
    ) -> Union[str, None]:
        """Return dependency name without version constraint.

        See PEP-404 for variations.
        """
        match = re.match(r"([\w\-\_\.]*)[>|=|<|~]*", dependency_string)
        if match and match.groups():
            dep_name = match.groups()[0]
            return dep_name
        return None

    @staticmethod
    def dependency_without_direct_reference(
        dependency_string: str,
    ) -> Union[str, None]:
        """Return dependency name without direct reference.

        See PEP-508 for variations.
        """
        match = re.match(r"([\w\-\_\.]*)\s*@\s*", dependency_string)
        if match and match.groups():
            dep_name = match.groups()[0]
            return dep_name
        return None


def get_module_info_from_python_file(path: str) -> Generator[ImportInfo, None, None]:
    """Get imports, based on given filepath.

    Credit:
        https://stackoverflow.com/a/9049549/2448495
    """

    root = None
    with open(path, encoding="utf-8", errors="replace") as fh:
        try:
            root = ast.parse(fh.read(), path)
        except SyntaxError as e:
            logger.warning(f"Syntax error, cannot AST-parse {path}: {e}")

    if root:
        for node in ast.iter_child_nodes(root):  # or potentially ast.walk ?
            if isinstance(node, ast.Import):
                module = []
            elif isinstance(node, ast.ImportFrom):
                module = node.module.split(".") if node.module else []
            else:
                continue

            if hasattr(node, "names"):
                for n in node.names:
                    yield ImportInfo(
                        module=module,
                        name=n.name.split("."),
                        alias=n.asname,
                    )


def get_module_names_from_code(paths: List[str]) -> List[ImportInfo]:
    resolved_paths: List[Path] = []
    imports = []

    for path in paths:
        if Path(path).is_dir():
            resolved_paths.extend(list(Path(path).glob("**/*.py")))
        else:
            resolved_paths.append(Path(path).resolve())

    for resolved_path in resolved_paths:
        logger.debug(f"Parsing {resolved_path}")
        for import_info in get_module_info_from_python_file(path=str(resolved_path)):
            imports.append(import_info)

    imports_with_dupes_removed = []
    for import_info in imports:
        if import_info not in imports_with_dupes_removed:
            imports_with_dupes_removed.append(import_info)

    logger.debug("Imports found in code:")
    for imp in imports_with_dupes_removed:
        logger.debug(f"- {imp}")

    return imports_with_dupes_removed


def get_installed_dependency_names(venv: str) -> List[str]:
    dep_names = []
    for path in Path(venv).glob("**/*.dist-info"):
        dep_names.append(path.name.split("-")[0])
    return dep_names


def get_excluded_deps_which_are_not_installed(
    excluded_deps: List[str], venvs: List[str]
) -> List[str]:
    dependency_names: List[str] = []
    if not excluded_deps:
        return dependency_names

    excluded_deps_canonicalized = [
        canonicalize_module_name(arg) for arg in excluded_deps
    ]

    for excluded_dep_name in excluded_deps_canonicalized:
        for venv in venvs:
            if excluded_dep_name not in get_installed_dependency_names(venv):
                dependency_names.append(excluded_dep_name)

    dependency_names = list(set(dependency_names))

    if dependency_names:
        logger.warning(
            "Excluded dependencies not found in virtual environment: "
            f"{', '.join(dependency_names)}"
        )
    return dependency_names


def canonicalize_module_name(module_name: str) -> str:
    return module_name.replace("-", "_").replace(".", "_").strip()

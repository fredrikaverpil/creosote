import ast
import re
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Union, cast

import nbformat
from typing_extensions import TypeGuard

if sys.version_info >= (3, 11):
    import tomllib  # pyright: ignore[reportUnreachable]
else:
    import tomli as tomllib

import dotty_dict  # pyright: ignore[reportMissingTypeStubs]
from loguru import logger
from nbconvert import PythonExporter
from pip_requirements_parser import (  # pyright: ignore[reportMissingTypeStubs]
    RequirementsFile,
)

from creosote.models import ImportInfo

GroupName = str
PackageName = str
PEP621Type1 = list[PackageName]
PEP621Type2 = dict[GroupName, list[PackageName]]
PEP621Types = Union[PEP621Type1, PEP621Type2]
PEP735Type1 = dict[GroupName, list[PackageName]]
PEP735Type2 = dict[GroupName, list[Union[dict[str, PackageName], str]]]
PEP735Types = Union[PEP735Type1, PEP735Type2]
PoetryType1 = dict[PackageName, str]
PoetryType2 = dict[PackageName, dict[str, str]]
PoetryType3 = dict[PackageName, Union[str, dict[str, str]]]
PoetryType4 = dict[PackageName, list[dict[str, str]]]
PoetryTypes = Union[PoetryType1, PoetryType2, PoetryType3, PoetryType4]
PipfileType1 = dict[PackageName, str]
PipfileType2 = dict[PackageName, dict[str, str]]
PipfileType3 = dict[PackageName, Union[str, dict[str, str]]]
PipfileTypes = Union[PipfileType1, PipfileType2, PipfileType3]
AllSupportedTypes = Union[
    PEP621Type1,
    PEP621Type2,
    PEP735Type1,
    PEP735Type2,
    PoetryType1,
    PoetryType2,
    PoetryType3,
    PoetryType4,
    PipfileType1,
    PipfileType2,
    PipfileType3,
]


def is_list_type(var: AllSupportedTypes) -> TypeGuard[PEP621Type1]:
    return isinstance(var, list)


def is_dict_of_strings(
    var: AllSupportedTypes,
) -> TypeGuard[Union[PoetryType1, PipfileType1]]:
    return isinstance(var, dict) and all(isinstance(v, str) for v in var.values())


def is_dict_of_lists(
    var: AllSupportedTypes,
) -> TypeGuard[Union[PEP621Type2, PEP735Type1, PEP735Type2, PoetryType4]]:
    return isinstance(var, dict) and all(isinstance(v, list) for v in var.values())


def is_pep621_dict_of_lists(
    var: AllSupportedTypes,
) -> TypeGuard[PEP621Type2]:
    """Type guard specifically for PEP621Type2."""
    return (
        isinstance(var, dict)
        and all(isinstance(v, list) for v in var.values())
        and all(all(isinstance(item, str) for item in v) for v in var.values())
    )


def is_dict_of_dicts(
    var: AllSupportedTypes,
) -> TypeGuard[Union[PoetryType2, PipfileType2]]:
    return isinstance(var, dict) and all(isinstance(v, dict) for v in var.values())


def is_dict_of_union(
    var: AllSupportedTypes,
) -> TypeGuard[Union[PoetryType3, PipfileType3]]:
    if not isinstance(var, dict):
        return False
    return all(isinstance(v, (str, dict)) for v in var.values())


class DependencyReader:
    """Read dependencies from various dependency file formats."""

    def __init__(
        self,
        deps_file: str,
        sections: list[str],
        exclude_deps: list[str],
    ) -> None:
        always_excluded_deps = ["python"]  # occurs in Poetry setup

        self.deps_file: str = deps_file
        self.sections: list[str] = sections
        self.exclude_deps: list[str] = exclude_deps + always_excluded_deps

    def read(self) -> list[str]:
        logger.debug(f"Parsing {self.deps_file} for dependencies...")

        if not Path(self.deps_file).exists():
            raise Exception(f"File {self.deps_file} does not exist")

        dep_names: list[str] = []
        always_excluded_deps: list[str] = ["python"]  # occurs in Poetry setup
        deps_to_exclude: list[str] = always_excluded_deps + self.exclude_deps

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

        found = ", ".join(dep_names)
        logger.info(f"Found dependencies in {self.deps_file}: {found}")

        return dep_names

    def get_deps_from_pep621_toml(
        self, section_contents: PEP621Types
    ) -> list[PackageName]:
        """Get dependency names from toml file using the PEP621 spec.

        The dependency strings are expected to follow PEP508.
        """

        dep_strings: list[str] = []
        if is_list_type(section_contents):
            for dep_string in section_contents:
                dep_strings.append(dep_string)
        elif is_pep621_dict_of_lists(section_contents):
            for _, dep_string_list in section_contents.items():
                for dep_string in dep_string_list:
                    dep_strings.append(dep_string)
        else:
            raise TypeError("Unexpected dependency format, list expected.")

        section_deps: list[PackageName] = []
        for dep_string in dep_strings:
            parsed_dep = self.parse_dep_string(dep_string)
            if parsed_dep:
                section_deps.append(parsed_dep)
            else:
                logger.warning(f"Could not parse dependency string: {dep_string}")

        return section_deps

    def get_deps_from_pep735_toml(
        self, section_contents: PEP735Types
    ) -> list[PackageName]:
        """Get dependency names from toml file using the PEP735 spec.

        The dependency strings are expected to follow PEP508.
        """

        dep_strings: list[str] = []
        if is_dict_of_lists(section_contents):
            for _, dep_string_list in section_contents.items():
                for dep_string in dep_string_list:
                    if type(dep_string) is not str:
                        logger.debug(f"Skipping non-string entry: {dep_string}")
                        continue
                    dep_strings.append(dep_string)
        else:
            raise TypeError("Unexpected dependency format, list expected.")

        section_deps: list[PackageName] = []
        for dep_string in dep_strings:
            parsed_dep = self.parse_dep_string(dep_string)
            if parsed_dep:
                section_deps.append(parsed_dep)
            else:
                logger.warning(f"Could not parse dependency string: {dep_string}")

        return section_deps

    def assert_is_dict(self, obj: object) -> None:
        if not isinstance(obj, dict):
            raise TypeError("Unexpected dependency format, dict expected.")

    def get_deps_from_toml_section_keys(
        self,
        section_contents: Union[PoetryTypes, PipfileTypes],
    ) -> list[PackageName]:
        """Get dependency names from toml section's dict keys."""
        self.assert_is_dict(section_contents)
        return list(section_contents.keys())

    def read_toml(self, deps_file: str, sections: list[str]) -> list[str]:
        """Read dependency names from toml spec file."""
        with open(deps_file, "rb") as infile:
            contents = tomllib.load(infile)

        dotty_contents = dotty_dict.dotty(contents)  # pyright: ignore[reportUnknownMemberType]
        dep_names: list[str] = []

        for section in sections:
            try:
                section_contents = cast(AllSupportedTypes, dotty_contents[section])
            except KeyError as err:
                raise KeyError(f"Could not find toml section {section}.") from err

            logger.debug(f"{sections}: {section_contents}")

            section_dep_names: list[str] = []
            if section.startswith("project."):
                logger.debug(f"Detected PEP-621 toml section in {deps_file}")
                section_dep_names = self.get_deps_from_pep621_toml(
                    cast(PEP621Types, section_contents)
                )
            elif section.startswith("tool.pdm"):
                logger.debug(f"Detected PDM toml section in {deps_file}")
                section_dep_names = self.get_deps_from_pep621_toml(
                    cast(PEP621Types, section_contents)
                )
            elif section.startswith("dependency-groups"):
                logger.debug(f"Detected PEP-735 toml section in {deps_file}")
                section_dep_names = self.get_deps_from_pep735_toml(
                    cast(PEP735Types, section_contents)
                )
            elif section.startswith("tool.poetry"):
                logger.debug(f"Detected Poetry toml section in {deps_file}")
                section_dep_names = self.get_deps_from_toml_section_keys(
                    cast(PoetryTypes, section_contents)
                )
            elif section.startswith("packages") or section.startswith("dev-packages"):
                logger.debug(f"Detected pipenv/Pipfile toml section in {deps_file}")
                section_dep_names = self.get_deps_from_toml_section_keys(
                    cast(PipfileType1, section_contents)
                )
            else:
                raise TypeError("Unsupported dependency format.")

            if not section_dep_names:
                logger.warning(f"No dependencies found in section {section}")
            else:
                dep_names.extend(section_dep_names)

        return sorted(dep_names)

    def read_requirements(self, deps_file: str) -> list[str]:
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
    is_notebook = False
    if Path(path).suffix == ".ipynb":
        with open(path) as f:
            notebook_content = nbformat.read(  # type: ignore[no-untyped-call]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                f,
                as_version=4,
            )
        # Convert the notebook to a temporary .py file
        body, _ = PythonExporter().from_notebook_node(  # type: ignore[no-untyped-call]
            notebook_content  # pyright: ignore[reportUnknownArgumentType]
        )

        # delete_on_close parameter only supported in Python 3.12+
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
            _ = temp_file.write(body.encode("utf-8"))
            path = temp_file.name
            is_notebook = True

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
    if is_notebook:
        Path(path).unlink()


def get_module_names_from_code(paths: list[str]) -> list[ImportInfo]:
    resolved_paths: list[Path] = []
    imports: list[ImportInfo] = []

    for path in paths:
        if Path(path).is_dir():
            resolved_paths.extend(list(Path(path).glob("**/*.py")))
            resolved_paths.extend(list(Path(path).glob("**/*.ipynb")))
        else:
            resolved_paths.append(Path(path).resolve())

    for resolved_path in resolved_paths:
        logger.debug(f"Parsing {resolved_path}")
        for import_info in get_module_info_from_python_file(path=str(resolved_path)):
            imports.append(import_info)

    imports_with_dupes_removed: list[ImportInfo] = []
    for import_info in imports:
        if import_info not in imports_with_dupes_removed:
            imports_with_dupes_removed.append(import_info)

    logger.debug("Imports found in code:")
    for imp in imports_with_dupes_removed:
        logger.debug(f"- {imp}")

    return imports_with_dupes_removed


def get_installed_dependency_names(venv: str) -> list[str]:
    dep_names: list[str] = []
    for path in Path(venv).glob("**/*.dist-info"):
        dep_names.append(path.name.split("-")[0])
    return dep_names


def get_excluded_deps_which_are_not_installed(
    excluded_deps: list[str], venvs: list[str]
) -> list[str]:
    dependency_names: list[str] = []
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
            + f"{', '.join(dependency_names)}"
        )
    return dependency_names


def canonicalize_module_name(module_name: str) -> str:
    return module_name.replace("-", "_").replace(".", "_").strip()

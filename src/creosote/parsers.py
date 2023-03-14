import ast
import pathlib
import re
from typing import Any, Dict, List, cast

import toml
from dotty_dict import Dotty, dotty
from loguru import logger
from pip_requirements_parser import RequirementsFile

from creosote.models import Import, Package


class PackageReader:
    """Read dependencies from various dependency file formats.

    The dependency names read will be converted into a list of internal Package
    objects.
    """

    def __init__(
        self,
        deps_file: str,
        sections: List[str],
        exclude_packages: List[str],
    ) -> None:
        always_excluded_packages = ["python"]  # occurs in Poetry setup

        self.deps_file = deps_file
        self.sections = sections
        self.exclude_packages = exclude_packages + always_excluded_packages
        self.packages: List[Package] = []

    def build(self):
        if not pathlib.Path(self.deps_file).exists():
            raise Exception(f"File {self.deps_file} does not exist")

        always_excluded_packages = ["python"]  # occurs in Poetry setup
        packages_to_exclude = always_excluded_packages + self.exclude_packages

        if self.deps_file.endswith(".toml"):  # pyproject.toml expected
            for dependency_name in self.load_pyproject(self.deps_file, self.sections):
                if dependency_name not in packages_to_exclude:
                    self.add_package(dependency_name)

        elif self.deps_file.endswith(".txt") or self.deps_file.endswith(".in"):
            for dependency_name in self.load_requirements(self.deps_file):
                if dependency_name not in packages_to_exclude:
                    self.add_package(dependency_name)

        else:
            raise NotImplementedError(
                f"Dependency specs file {self.deps_file} is not supported."
            )

        found_packages = [
            package.dependency_name
            for package in self.packages
            if package.dependency_name
        ]
        logger.info(
            f"Found packages in {self.deps_file}: " f"{', '.join(found_packages)}"
        )

    def load_pyproject_pep621(self, section_contents: List[str]):
        if not isinstance(section_contents, list):
            raise TypeError("Unexpected dependency format, list expected.")

        section_deps = []
        for dep in section_contents:
            parsed_dep = self.parse_dep_string(dep)
            section_deps.append(parsed_dep)
        return section_deps

    def load_pyproject_poetry(self, section_contents: Dict[str, Any]):
        if not isinstance(section_contents, dict):
            raise TypeError("Unexpected dependency format, dict expected.")
        return section_contents.keys()

    def load_pyproject(self, deps_file: str, sections: List[str]):
        """Read dependency names from pyproject.toml."""
        with open(deps_file, "r", encoding="utf-8") as infile:
            contents = toml.loads(infile.read())

        dotty_contents: Dotty = dotty(contents)
        deps = []

        for section in sections:
            try:
                section_contents = dotty_contents[section]
            except KeyError as err:
                raise KeyError(f"Could not find toml section {section}.") from err

            logger.debug(f"{sections}: {section_contents}")

            section_deps = []
            if section.startswith("project"):
                logger.debug(f"Detected PEP-621 toml section in {deps_file}")
                section_deps = self.load_pyproject_pep621(section_contents)
            elif section.startswith("packages") or section.startswith("dev-packages"):
                logger.debug(f"Detected pipenv/Pipfile toml section in {deps_file}")
                section_deps = self.load_pyproject_pep621(section_contents)
            elif section.startswith("tool.pdm"):
                logger.debug(f"Detected PDM toml section in {deps_file}")
                section_deps = self.load_pyproject_pep621(section_contents)
            elif section.startswith("tool.poetry"):
                logger.debug(f"Detected Poetry toml section in {deps_file}")
                section_deps = self.load_pyproject_poetry(cast(dict, section_contents))
            else:
                raise TypeError("Unsupported dependency format.")

            if not section_deps:
                logger.warning(f"No dependencies found in section {section}")
            else:
                deps.extend(section_deps)

        return sorted(deps)

    def load_requirements(self, deps_file: str) -> List[str]:
        """Read dependency names from requirements.txt-format file."""
        deps = RequirementsFile.from_file(deps_file).requirements
        return sorted([dep.name for dep in deps if dep.name is not None])

    def add_package(self, dependency_name: str) -> Package:
        if dependency_name not in [
            package.dependency_name for package in self.packages
        ]:
            package = Package(dependency_name=dependency_name)
            self.packages.append(package)
            return package
        raise Exception(f"Package {dependency_name} already exists.")

    @staticmethod
    def parse_dep_string(dep: str):
        if "@" in dep:
            return PackageReader.dependency_without_direct_reference(dep)
        else:
            return PackageReader.dependency_without_version_constraint(dep)

    @staticmethod
    def dependency_without_version_constraint(dependency_string: str):
        """Return dependency name without version constraint.

        See PEP-404 for variations.
        """
        match = re.match(r"([\w\-\_\.]*)[>|=|<|~]*", dependency_string)
        if match and match.groups():
            dep = match.groups()[0]
            return dep

    @staticmethod
    def dependency_without_direct_reference(dependency_string: str):
        """Return dependency name without direct reference.

        See PEP-508 for variations.
        """
        match = re.match(r"([\w\-\_\.]*)\s*@\s*", dependency_string)
        if match and match.groups():
            dep = match.groups()[0]
            return dep


def get_module_info_from_code(path):
    """Get imports, based on given filepath.

    Credit:
        https://stackoverflow.com/a/9049549/2448495
    """
    with open(path, encoding="utf-8") as fh:
        root = ast.parse(fh.read(), path)

    for node in ast.iter_child_nodes(root):  # or potentially ast.walk ?
        if isinstance(node, ast.Import):
            module = []
        elif isinstance(node, ast.ImportFrom):
            module = node.module.split(".") if node.module else []
        else:
            continue

        for n in node.names:
            yield Import(module, n.name.split("."), n.asname)


def get_modules_from_code(paths):
    resolved_paths = []
    imports = []

    for path in paths:
        if pathlib.Path(path).is_dir():
            resolved_paths.extend(iter(pathlib.Path(path).glob("**/*.py")))
        else:
            resolved_paths.append(pathlib.Path(path).resolve())

    for resolved_path in resolved_paths:
        logger.debug(f"Parsing {resolved_path}")
        for imp in get_module_info_from_code(resolved_path):
            imports.append(imp)

    dupes_removed = []
    for imp in imports:
        if imp not in dupes_removed:
            dupes_removed.append(imp)

    return dupes_removed

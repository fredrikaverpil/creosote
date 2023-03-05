import ast
import pathlib
import re
from functools import lru_cache

import toml
from dotty_dict import dotty
from loguru import logger

from creosote.models import Import, Package


class PackageReader:
    def __init__(self):
        self.packages = None

    def pyproject_pep621(self, section_contents: dict):
        if not isinstance(section_contents, list):
            raise TypeError("Unexpected dependency format, list expected.")

        section_deps = []
        for dep in section_contents:
            parsed_dep = self.parse_dep_string(dep)
            section_deps.append(parsed_dep)
        return section_deps

    def pyproject_poetry(self, section_contents: dict):
        if not isinstance(section_contents, dict):
            raise TypeError("Unexpected dependency format, dict expected.")
        return section_contents.keys()

    def pyproject(self, deps_file: str, sections: list):
        """Return dependencies from pyproject.toml."""
        with open(deps_file, "r") as infile:
            contents = toml.loads(infile.read())

        dotty_contents = dotty(contents)
        deps = []

        for section in sections:
            try:
                section_contents = dotty_contents[section]
            except KeyError as err:
                raise KeyError(f"Could not find toml section {section}.") from err
            section_deps = []

            if section.startswith("project"):
                section_deps = self.pyproject_pep621(section_contents)
            elif section.startswith("tool.poetry"):
                section_deps = self.pyproject_poetry(section_contents)
            else:
                raise TypeError("Unsupported dependency format.")

            if not section_deps:
                logger.warning(f"No dependencies found in section {section}")
            else:
                deps.extend(section_deps)

        return sorted(deps)

    def requirements(self, deps_file: str):
        """Return dependencies from requirements.txt-format file."""
        deps = []
        with open(deps_file, "r") as infile:
            contents = infile.readlines()

        for line in contents:
            if line.startswith("#") or line.startswith(" "):
                continue
            parsed_dep = self.parse_dep_string(line)
            deps.append(parsed_dep)

        return sorted(deps)

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

    @lru_cache(maxsize=None)  # noqa: B019
    def ignore_packages(self):
        return ["python"]

    def filter_ignored_dependencies(self, deps):
        packages = []
        for dep in deps:
            if dep not in self.ignore_packages():
                packages.append(Package(name=dep))
        return packages

    def read(self, deps_file: str, sections: list):
        if not pathlib.Path(deps_file).exists():
            raise Exception(f"File {deps_file} does not exist")

        if "pyproject.toml" in deps_file:
            self.packages = self.filter_ignored_dependencies(
                self.pyproject(deps_file, sections)
            )
        elif deps_file.endswith(".txt") or deps_file.endswith(".in"):
            self.packages = self.filter_ignored_dependencies(
                self.requirements(deps_file)
            )
        else:
            raise NotImplementedError(
                f"Dependency specs file {deps_file} is not supported."
            )

        logger.info(
            f"Found packages in {deps_file}: "
            f"{', '.join([pkg.name for pkg in self.packages])}"
        )


def get_module_info_from_code(path):
    """Get imports, based on given filepath.

    Credit:
        https://stackoverflow.com/a/9049549/2448495
    """
    with open(path) as fh:
        root = ast.parse(fh.read(), path)

    for node in ast.iter_child_nodes(root):  # or potentially ast.walk ?
        if isinstance(node, ast.Import):
            module = []
        elif isinstance(node, ast.ImportFrom):
            module = node.module.split(".")
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
        logger.info(f"Parsing {resolved_path}")
        for imp in get_module_info_from_code(resolved_path):
            imports.append(imp)

    dupes_removed = []
    for imp in imports:
        if imp not in dupes_removed:
            dupes_removed.append(imp)

    return dupes_removed

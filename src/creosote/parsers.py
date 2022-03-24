import ast
import pathlib
from functools import lru_cache

import toml
from loguru import logger

from creosote.models import Import, Package


class PackageReader:
    def __init__(self):
        self.packages = None

    def _pyproject(self, deps_file: str, dev: bool):
        """Return dependencies from pyproject.toml."""
        with open(deps_file, "r") as infile:
            contents = toml.loads(infile.read())

        try:
            if dev:
                deps = contents["tool"]["poetry"]["dev-dependencies"]
            else:
                deps = contents["tool"]["poetry"]["dependencies"]
        except KeyError as e:
            raise Exception("Could not find expected toml property.") from e

        return sorted(deps.keys())

    def _requirements(self, deps_file: str):
        """Return dependencies from requirements.txt-format file."""
        deps = []
        with open(deps_file, "r") as infile:
            contents = infile.readlines()

        for line in contents:
            if not line.startswith(" "):
                deps.append(line[: line.find("=")])

        return sorted(deps)

    @lru_cache(maxsize=None)
    def ignore_packages(self):
        return ["python"]

    def packages_sans_ignored(self, deps):
        packages = []
        for dep in deps:
            if dep not in self.ignore_packages():
                packages.append(Package(name=dep))
        return packages

    def read(self, deps_file: str, dev: bool):
        if not pathlib.Path(deps_file).exists():
            raise Exception(f"File {deps_file} does not exist")

        if "pyproject.toml" in deps_file:
            self.packages = self.packages_sans_ignored(self._pyproject(deps_file, dev))
        elif deps_file.endswith(".txt") or deps_file.endswith(".in"):
            self.packages = self.packages_sans_ignored(self._requirements(deps_file))
        else:
            raise NotImplementedError(
                f"Dependency specs file {deps_file} is not supported."
            )

        logger.info(
            f"Found packages in {deps_file}: "
            f"{', '.join([pkg.name for pkg in self.packages])}"
        )


class ImportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports = set()
       
    def visit_Import(self, node: ast.Import) -> None:
        self._add_import(node.names, node.asname, module=[])
        
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self._add_import(node.names, node.asname, module=node.module.split("."))
        
    def _add_import(self, names: list[ast.Name], asname: str, module: list[str]) -> None:
        for name in names:
            self.imports.add(Import(module, name.name, asname))


def get_module_info_from_code(path) -> Set[Import]:
    """Get imports, based on given filepath.

    Credit:
        https://stackoverflow.com/a/9049549/2448495
    """
    with open(path) as fh:
        root = ast.parse(fh.read(), path)

    visitor = ImportVisitor()
    visitor.visit(root)
    return visitor.imports


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

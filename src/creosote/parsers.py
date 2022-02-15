import ast
import pathlib
from functools import lru_cache

from loguru import logger

from creosote.models import Import, Package


class PackageReader:
    def __init__(self):
        self.packages = None

    @staticmethod
    def _pyproject():
        """Return production dependencies from pyproject.toml."""
        found_dependencies = []
        with open("pyproject.toml", "r") as infile:
            contents = infile.readlines()

        record = False
        for line in contents:
            if "poetry.dependencies" in line:
                record = True
                continue
            elif line.startswith("["):
                record = False

            if record is True and "=" in line:
                entry = line[: line.find("=")].strip()
                found_dependencies.append(entry)

        return sorted(found_dependencies)

    @lru_cache(maxsize=None)
    def ignore_packages(self):
        return ["python"]

    def wrap_in_obj(self, deps):
        packages = []
        for dep in deps:
            if dep not in self.ignore_packages():
                packages.append(Package(name=dep))
        return packages

    def read(self, deps_file):
        if deps_file == "pyproject.toml":
            self.packages = self.wrap_in_obj(self._pyproject())
        else:
            raise NotImplementedError(
                f"Dependency specs file {deps_file} is not supported."
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
    imports = []

    for path in paths:
        resolved_paths = pathlib.Path(".").glob(path)
        for resolved_path in resolved_paths:
            logger.info(f"Parsing {resolved_path}")
            for imp in get_module_info_from_code(resolved_path):
                imports.append(imp)

    dupes_removed = []
    for imp in imports:
        if imp not in dupes_removed:
            dupes_removed.append(imp)

    return dupes_removed

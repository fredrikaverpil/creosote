import os
import pathlib
import re
from pathlib import Path
from typing import List, Optional

from distlib import database
from loguru import logger

from creosote.models import Import, Package


class DepsResolver:
    def __init__(
        self,
        imports: List[Import],
        packages: List[Package],
        venv: str,
    ):
        self.imports = imports
        self.packages = packages
        self.venv = venv

        self.map_package_name_to_top_level_import
        self.top_level_package_pattern = re.compile(
            r"\/([\w]*).[\d\.]*.dist-info\/top_level.txt"
        )

        self.unused_packages: Optional[List[Package]] = None

    @staticmethod
    def canonicalize_module_name(module_name: str):
        return module_name.replace("-", "_").replace(".", "_").strip()

    def is_importable(self, module_name: str):
        try:
            __import__(self.canonicalize_module_name(module_name))
            return True
        except ImportError:
            return False

    def gather_top_level_filepaths(self):
        """Gathers all top_level.txt filepaths in the venv.

        Note:
            The path may contain case sensitive variations of the
            package name, like e.g. GitPython for gitpython.
        """
        logger.debug("Gathering all top_level.txt files in venv...")
        venv_path = pathlib.Path(self.venv)
        glob_str = "**/*.dist-info/top_level.txt"
        top_level_filepaths = venv_path.glob(glob_str)
        self.top_level_filepaths = list(top_level_filepaths)
        for top_level_filepath in self.top_level_filepaths:
            logger.debug(f"Found {top_level_filepath}")

    def map_package_name_to_top_level_import(self, package: Package):
        package_name = self.canonicalize_module_name(package.name)

        for top_level_filepath in self.top_level_filepaths:
            matches = self.top_level_package_pattern.findall(str(top_level_filepath))
            for top_level_package in matches:
                if top_level_package.lower() == package_name.lower():
                    with open(top_level_filepath, "r") as infile:
                        lines = infile.readlines()
                    package.top_level_import_names = [line.strip() for line in lines]
                    import_names = ",".join(package.top_level_import_names)
                    logger.debug(
                        f"Mapped package/import: {package_name}/{import_names}"
                    )
                    return
        logger.debug(f"Did not find a top_level.txt file for package {package_name}")

    def map_package_to_module_via_distlib(self, package: Package):
        """Fallback to distlib if we can't find the top_level.txt file.

        Note:
            It's possible that this function is completely redundant
            and can be removed...
        """
        logger.debug("Performing fallback module name resolution...")

        dp = database.DistributionPath(include_egg=True)
        dist = dp.get_distribution(package.name)

        if dist is None:
            # raise ModuleNotFoundError
            return
        module = package.name  # until we figure out something better
        for filename, _, _ in dist.list_installed_files():
            if filename.endswith((".py")):
                parts = os.path.splitext(filename)[0].split(os.sep)
                if len(parts) == 1:  # windows sep varies with distribution type
                    parts = os.path.splitext(filename)[0].split("/")
                if parts[-1].startswith("_") and not parts[-1].startswith("__"):
                    continue  # ignore internals
                elif filename.endswith(".py") and parts[-1] == "__init__":
                    module = parts[-2]
                    break

        logger.debug(f"Found module name for {package.name}: {module}")
        package.module_name = module

    def associate_imports_with_package(self, package: Package, name: str):
        for imp in self.imports.copy():
            if not imp.module and name in imp.name:  # noqa: SIM114
                # import <imp.name>
                package.associated_imports.append(imp)
            elif imp.name and name in imp.module:
                # from <imp.name> import ...
                package.associated_imports.append(imp)

    def populate_packages(self):
        venv_exists = Path(self.venv).exists()

        if not venv_exists:
            logger.warning(
                f"Virtual environment '{self.venv}' does not exist, "
                "cannot resolve top-level names. This may lead to incorrect results."
            )

        for package in self.packages:
            if venv_exists:
                self.map_package_name_to_top_level_import(package)
            self.map_package_to_module_via_distlib(package)

    def associate(self):
        """Associate package name with import (module) name"""
        for package in self.packages:
            self.associate_imports_with_package(package, package.name)
            if package.top_level_import_names:
                for import_name in package.top_level_import_names:
                    self.associate_imports_with_package(package, import_name)
            if package.module_name:
                # fallback to module name
                self.associate_imports_with_package(package, package.module_name)

    def get_unused_packages(self):
        self.unused_packages = [
            package for package in self.packages if not package.associated_imports
        ]

    def get_unused_package_names(self):
        if self.unused_packages:
            return [package.name for package in self.unused_packages]
        return None

    def resolve(self):
        self.gather_top_level_filepaths()
        self.populate_packages()
        self.associate()
        self.get_unused_packages()
        self.get_unused_packages()

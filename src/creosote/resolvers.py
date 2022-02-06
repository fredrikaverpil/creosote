import os
import pathlib
import site

from distlib import database
from loguru import logger


class DepsResolver:
    def __init__(self):
        self.imports_to_validate = []
        self.unused_packages = []
        self.map = {}

    @staticmethod
    def canonicalize_dep(dep):
        return dep.replace("-", "_").replace(".", "_").strip()

    def is_importable(self, dep):
        try:
            __import__(self.canonicalize_dep(dep))
            return True
        except ImportError:
            return False

    def ignored_packages(self):
        return ["python", "pip", "setuptools", "wheel"]

    def remove_ignored_from_imports(self, imports, deps):
        return [
            pkg
            for pkg in deps
            if pkg not in imports and pkg not in self.ignored_packages()
        ]

    # def package_to_module(self, package):
    #     dp = database.DistributionPath(include_egg=True)
    #     dist = dp.get_distribution(package)
    #     if dist is None:
    #         raise ModuleNotFoundError
    #     module = package  # until we figure out something better
    #     for filename, _, _ in dist.list_installed_files():
    #         if filename.endswith((".py")):
    #             parts = os.path.splitext(filename)[0].split(os.sep)
    #             if len(parts) == 1:  # windows sep varies with distribution type
    #                 parts = os.path.splitext(filename)[0].split("/")
    #             if parts[-1].startswith("_") and not parts[-1].startswith("__"):
    #                 continue  # ignore internals
    #             elif filename.endswith(".py") and parts[-1] == "__init__":
    #                 module = parts[-2]
    #                 break

    #     return module

    def validate_through_import(self, deps):
        for dep in deps:
            logger.debug(f"Attempting to import {self.canonicalize_dep(dep)}")
            if self.is_importable(dep):
                self.unused_packages.append(dep)
                self.imports_to_validate.remove(dep)
                logger.debug(f"Successfully imported {dep}, meaning is is unused")
            else:
                logger.debug(f"Could not import {self.canonicalize_dep(dep)}")

    def validate_through_top_level(self, deps):
        for dep in deps:
            logger.debug(f"Trying to find importable name for {dep}")
            for site_packages in site.getsitepackages():
                site_path = pathlib.Path(site_packages)
                glob_str = f"{dep}*.dist-info/top_level.txt"
                top_levels = site_path.glob(glob_str)
                for t in top_levels:
                    with open(t, "r") as infile:
                        lines = infile.readlines()

                    stripped_lines = []
                    for line in lines:
                        stripped_lines.append(line.strip())

                    self.imports_to_validate.remove(dep)
                    for line in stripped_lines:
                        self.imports_to_validate.append(line)
                    logger.debug(self.imports_to_validate)
                    self.validate_through_import(stripped_lines)

    # def validate_through_package_to_module_conversion(self, deps):
    #     for dep in deps:
    #         module = self.package_to_module(dep)
    #         self.validate_through_import(module)

    def resolve(self, modules, packages):
        self.imports_to_validate = self.remove_ignored_from_imports(
            imports=modules, deps=packages
        )
        logger.debug(
            f"After ignoring, these are the suspicious deps: {self.imports_to_validate}"
        )
        self.validate_through_import(deps=self.imports_to_validate.copy())

        self.validate_through_top_level(deps=self.imports_to_validate.copy())

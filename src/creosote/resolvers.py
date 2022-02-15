import os
import pathlib
from typing import List, Optional

from distlib import database

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

    def top_level_names(self, package):
        package_name = package.name.replace("-", "_")
        site_path = pathlib.Path(".")
        glob_str = f"{self.venv}/**/{package_name}*.dist-info/top_level.txt"
        top_levels = site_path.glob(glob_str)
        for top_level in top_levels:
            with open(top_level, "r") as infile:
                lines = infile.readlines()
            package.top_level_names = [line.strip() for line in lines]

    def package_to_module(self, package: Package):
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

        package.module_name = module

    def associate_imports_with_package(self, package: Package, name: str):
        for imp in self.imports.copy():
            if not imp.module and name in imp.name:
                # import <imp.name>
                package.associated_imports.append(imp)
            elif imp.name and name in imp.module:
                # from <imp.name> import ...
                package.associated_imports.append(imp)

    def populate_packages(self):
        for package in self.packages:
            self.top_level_names(package)
            self.package_to_module(package)

    def associate(self):
        for package in self.packages:
            self.associate_imports_with_package(package, package.name)
            if package.top_level_names:
                for t in package.top_level_names:
                    self.associate_imports_with_package(package, t)
            if package.module_name:
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
        self.populate_packages()
        self.associate()
        self.get_unused_packages()

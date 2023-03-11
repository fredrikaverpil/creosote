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

        self.map_package_to_import_via_top_level_txt_file
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
        self.top_level_filepaths = sorted(top_level_filepaths)
        for top_level_filepath in self.top_level_filepaths:
            logger.debug(f"Found {top_level_filepath}")

    def map_package_to_import_via_top_level_txt_file(self, package: Package) -> bool:
        """Return True if import name was found in the top_level.txt."""
        package_name = self.canonicalize_module_name(package.name)

        for top_level_filepath in self.top_level_filepaths:
            matches = self.top_level_package_pattern.findall(str(top_level_filepath))
            for top_level_package in matches:
                if top_level_package.lower() == package_name.lower():
                    with open(top_level_filepath, "r", encoding="utf-8") as infile:
                        lines = infile.readlines()
                    package.top_level_import_names = [line.strip() for line in lines]
                    import_names = ",".join(package.top_level_import_names)
                    logger.debug(
                        f"[{package.name}] found import name via top_level.txt: "
                        f"{import_names} ⭐️"
                    )
                    return True
        logger.debug(f"[{package.name}] did not find top_level.txt in venv")
        return False

    def map_package_to_module_via_distlib(self, package: Package) -> bool:
        """Fallback to distlib if we can't find the top_level.txt file.

        It seems this brings very little value right now, but I'll
        leave it in for now...
        """
        dp = database.DistributionPath(include_egg=True)
        dist = dp.get_distribution(package.name)

        if dist is None:
            # raise ModuleNotFoundError
            logger.debug(f"[{package.name}] did not find package in distlib.database")
            return False

        # until we figure out something better... (not great)
        module = self.canonicalize_module_name(package.name)

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

        logger.debug(
            f"[{package.name}] found import name via distlib.database: {module} 🤞"
        )
        package.distlib_db_import_name = module
        return True

    def gather_import_info(self):
        """Populate Package object with import naming info.

        There are three strategies from where the import name can be
        found:
            1. In the top_level.txt file in the venv.
            2. From the distlib database.
            3. Guess the import name by canonicalizing the package name.

        Later, these gathered import names will be compared against the
        imports found in the source code by the AST parser.
        """
        logger.debug("Attempting to find import names...")
        venv_exists = Path(self.venv).exists()
        found_import_name = False

        if not venv_exists:
            logger.warning(
                f"Virtual environment '{self.venv}' does not exist, "
                "cannot resolve top-level names. This may lead to incorrect results."
            )

        for package in self.packages:
            if venv_exists:
                # best chance to get the import name
                found_import_name = self.map_package_to_import_via_top_level_txt_file(
                    package
                )

            if not found_import_name:
                # fallback to distlib
                found_import_name = self.map_package_to_module_via_distlib(package)

            # this is really just guessing, but it's better than nothing
            package.canonicalized_package_name = self.canonicalize_module_name(
                package.name
            )
            if not found_import_name:
                logger.debug(
                    f"[{package.name}] relying on canonicalization fallback: "
                    f"{package.canonicalized_package_name } 🤞"
                )

    def associate_package_with_import(self, package: Package, import_name: str):
        for imp in self.imports.copy():
            if not imp.module and import_name in imp.name:  # noqa: SIM114
                # import <imp.name>
                package.associated_imports.append(imp)
            elif imp.name and import_name in imp.module:
                # from <imp.name> import ...
                package.associated_imports.append(imp)

    def associate_packages_with_imports(self):
        """Associate package name with import (module) name.

        The AST has found imports from the source code. This function
        will now attempt to associate these imports with the Package
        data, gathered from the venv, distlib, or canonicalization.
        """
        for package in self.packages:
            if package.top_level_import_names:
                for top_level_import_name in package.top_level_import_names:
                    self.associate_package_with_import(package, top_level_import_name)
            elif package.distlib_db_import_name:
                self.associate_package_with_import(
                    package, package.distlib_db_import_name
                )
            elif package.canonicalized_package_name:
                self.associate_package_with_import(
                    package, package.canonicalized_package_name
                )

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
        self.gather_import_info()
        self.associate_packages_with_imports()
        self.get_unused_packages()

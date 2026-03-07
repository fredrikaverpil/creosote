import ast
import re
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import TypeGuard, cast

import nbformat

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
PEP621Types = PEP621Type1 | PEP621Type2
PEP735Type1 = dict[GroupName, list[PackageName]]
PEP735Type2 = dict[GroupName, list[dict[str, PackageName] | str]]
PEP735Type3 = list[dict[str, PackageName] | str]
PEP735Types = PEP735Type1 | PEP735Type2 | PEP735Type3
PoetryType1 = dict[PackageName, str]
PoetryType2 = dict[PackageName, dict[str, str]]
PoetryType3 = dict[PackageName, str | dict[str, str]]
PoetryType4 = dict[PackageName, list[dict[str, str]]]
PoetryTypes = PoetryType1 | PoetryType2 | PoetryType3 | PoetryType4
PipfileType1 = dict[PackageName, str]
PipfileType2 = dict[PackageName, dict[str, str]]
PipfileType3 = dict[PackageName, str | dict[str, str]]
PipfileTypes = PipfileType1 | PipfileType2 | PipfileType3
AllSupportedTypes = (
    PEP621Type1
    | PEP621Type2
    | PEP735Type1
    | PEP735Type2
    | PEP735Type3
    | PoetryType1
    | PoetryType2
    | PoetryType3
    | PoetryType4
    | PipfileType1
    | PipfileType2
    | PipfileType3
)


def is_list_type(var: AllSupportedTypes) -> TypeGuard[PEP621Type1]:
    return isinstance(var, list)


def is_dict_of_strings(
    var: AllSupportedTypes,
) -> TypeGuard[PoetryType1 | PipfileType1]:
    return isinstance(var, dict) and all(isinstance(v, str) for v in var.values())


def is_dict_of_lists(
    var: AllSupportedTypes,
) -> TypeGuard[PEP621Type2 | PEP735Type1 | PEP735Type2 | PoetryType4]:
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
) -> TypeGuard[PoetryType2 | PipfileType2]:
    return isinstance(var, dict) and all(isinstance(v, dict) for v in var.values())


def is_dict_of_union(
    var: AllSupportedTypes,
) -> TypeGuard[PoetryType3 | PipfileType3]:
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
        if is_list_type(section_contents):
            for item in section_contents:
                if type(item) is not str:
                    logger.debug(f"Skipping non-string entry: {item}")
                    continue
                dep_strings.append(item)
        elif is_dict_of_lists(section_contents):
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
        section_contents: PoetryTypes | PipfileTypes,
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
            except KeyError:
                logger.warning(f"Ignoring non-existing section: {section}")
                continue

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
    def parse_dep_string(dep: str) -> str | None:
        if "@" in dep:
            return DependencyReader.dependency_without_direct_reference(dep)
        else:
            return DependencyReader.dependency_without_version_constraint(dep)

    @staticmethod
    def dependency_without_version_constraint(
        dependency_string: str,
    ) -> str | None:
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
    ) -> str | None:
        """Return dependency name without direct reference.

        See PEP-508 for variations.
        """
        match = re.match(r"([\w\-\_\.]*)\s*@\s*", dependency_string)
        if match and match.groups():
            dep_name = match.groups()[0]
            return dep_name
        return None


def get_module_info_from_python_file(
    path: str, *, include_deferred: bool = False
) -> Generator[ImportInfo, None, None]:
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
        # TODO(v6): always use ast.walk and make --include-deferred flag a no-op
        iter_nodes = ast.walk if include_deferred else ast.iter_child_nodes
        for node in iter_nodes(root):
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


def get_module_names_from_code(
    paths: list[str], *, include_deferred: bool = False
) -> list[ImportInfo]:
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
        for import_info in get_module_info_from_python_file(
            path=str(resolved_path), include_deferred=include_deferred
        ):
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


class DjangoSettingsVisitor(ast.NodeVisitor):
    """Visit `ast` nodes and extract module names from Django settings."""

    def __init__(self) -> None:
        self.found_modules: set[str] = set()
        self.variable_assignments: dict[str, list[str]] = {}

    def _resolve_value(self, node: ast.expr) -> list[str]:
        """Recursively resolve an expression node to a list of module names.

        This method traverses an AST expression, resolving it into a list of
        strings. It handles lists, tuples, and addition operations (`+`).

        The recursion is structural on the AST of binary operations, which is
        guaranteed to terminate as it only descends into the expression tree.

        Variable lookups are handled by checking a pre-populated dictionary
        (`self.variable_assignments`), which acts as a base case for the
        recursion. This prevents infinite loops in cases of circular
        variable references (e.g., `A = B; B = A`), as the variable's value
        is returned directly instead of re-triggering resolution.
        """
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return [node.value.split(".")[0]]

        if isinstance(node, (ast.List, ast.Tuple)):
            apps = []
            for element in node.elts:
                apps.extend(self._resolve_value(element))
            return apps

        if isinstance(node, ast.Name) and node.id in self.variable_assignments:
            return self.variable_assignments[node.id]

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._resolve_value(node.left)
            right = self._resolve_value(node.right)
            return left + right

        return []

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit `ast.Assign` nodes to track variables and find modules.

        This method is called for each assignment in the settings file. It
        has two main purposes:

        1.  It identifies assignments of literal lists/tuples to variables
            and stores the resolved module names in `self.variable_assignments`.
            This tracking is order-dependent and only works for literal
            assignments, not for variables assigned from other expressions.

        2.  It checks if the assignment is to `INSTALLED_APPS` or `MIDDLEWARE`.
            If so, it calls `_resolve_value` to resolve the expression into
            a list of module names.
        """
        # Populate `variable_assignments` for any literal list/tuple so it
        # can be resolved later if used in INSTALLED_APPS/MIDDLEWARE.
        if isinstance(node.value, (ast.List, ast.Tuple)):
            apps = []
            for element in node.value.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    apps.append(element.value.split(".")[0])
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.variable_assignments[target.id] = apps

        # If this is an assignment to INSTALLED_APPS or MIDDLEWARE, resolve
        # its value and add the found modules to our list.
        for target in node.targets:
            if (
                isinstance(target, ast.Name)
                and target.id in ["INSTALLED_APPS", "MIDDLEWARE"]
                and isinstance(node.value, (ast.List, ast.Tuple, ast.BinOp, ast.Name))
            ):
                # Guard against invalid assignments like `INSTALLED_APPS = "foo"`.
                # While `_resolve_value` can handle a single string (for `.append()`
                # support), a direct assignment to INSTALLED_APPS must be a
                # list-like expression (List, Tuple, BinOp, or Name).
                self.found_modules.update(self._resolve_value(node.value))

        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Visit `ast.AugAssign` to handle `INSTALLED_APPS += [...]`."""
        if isinstance(node.target, ast.Name) and node.target.id in [
            "INSTALLED_APPS",
            "MIDDLEWARE",
        ]:
            self.found_modules.update(self._resolve_value(node.value))
        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> None:
        """Visit `ast.Expr` to handle `INSTALLED_APPS.append(...)` etc."""
        if isinstance(node.value, ast.Call):
            call = node.value
            if (
                isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id in ["INSTALLED_APPS", "MIDDLEWARE"]
                and call.func.attr in ["append", "extend"]
            ):
                for arg in call.args:
                    self.found_modules.update(self._resolve_value(arg))
        self.generic_visit(node)


def get_modules_from_django_settings(settings_file: str | Path) -> list[str]:
    """Parse a Django settings file and extract modules from INSTALLED_APPS."""
    settings_path = Path(settings_file)
    if not settings_path.is_file():
        logger.warning(f"Django settings file not found: {settings_path}")
        return []

    logger.debug(f"Parsing Django settings file: {settings_path}")
    content = settings_path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(settings_path))

    visitor = DjangoSettingsVisitor()
    visitor.visit(tree)

    if not visitor.found_modules:
        if any(
            var in visitor.variable_assignments
            for var in ["INSTALLED_APPS", "MIDDLEWARE"]
        ):
            logger.info(
                f"Found INSTALLED_APPS/MIDDLEWARE in {settings_path} but empty."
            )
        else:
            logger.warning(
                f"Could not find INSTALLED_APPS or MIDDLEWARE in {settings_path}."
            )
    else:
        module_count = len(visitor.found_modules)
        logger.info(f"Found {module_count} Django modules in {settings_path}.")

    return list(visitor.found_modules)

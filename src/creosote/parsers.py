import ast
import pathlib
from collections import namedtuple

from loguru import logger

Import = namedtuple("Import", ["module", "name", "alias"])


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
            logger.debug(resolved_path)
            for imp in get_module_info_from_code(resolved_path):
                imports.append(imp)

    modules = []
    for imp in imports:
        if not imp.module and imp.name and imp.name[0] not in modules:
            # name equals "import something"
            modules.append(imp.name[0])
        if imp.module and imp.module[0] not in modules:
            # module equals "from something"
            modules.append(imp.module[0])

    return sorted(modules)

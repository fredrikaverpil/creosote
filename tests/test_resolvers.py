import pytest

from creosote.models import DependencyInfo, ImportInfo
from creosote.resolvers import DepsResolver


@pytest.mark.parametrize(
    ["imp", "import_name", "want_match"],
    [
        pytest.param(
            ImportInfo(module=(), name=("requests",)),
            "requests",
            True,
            id="import module",
        ),
        pytest.param(
            ImportInfo(module=(), name=("requests", "api")),
            "requests",
            True,
            id="import submodule",
        ),
        pytest.param(
            ImportInfo(module=("requests",), name=("Session",)),
            "requests",
            True,
            id="from module import symbol",
        ),
        pytest.param(
            ImportInfo(module=("requests", "auth"), name=("HTTPBasicAuth",)),
            "requests",
            True,
            id="from submodule import symbol",
        ),
        pytest.param(
            ImportInfo(module=("requests",), name=("*",)),
            "requests",
            True,
            id="star import",
        ),
        pytest.param(
            ImportInfo(module=(), name=("utils",)),
            "utils",
            True,
            id="relative import",
        ),
        pytest.param(
            ImportInfo(module=("requests",), name=("Session",)),
            "Session",
            False,
            id="imported symbol does not match",
        ),
        pytest.param(
            ImportInfo(module=(), name=("os", "path")),
            "path",
            False,
            id="trailing segment of import does not match",
        ),
        pytest.param(
            ImportInfo(module=("requests", "auth"), name=("HTTPBasicAuth",)),
            "auth",
            False,
            id="trailing segment of from-import module does not match",
        ),
        pytest.param(
            ImportInfo(module=("google", "cloud"), name=("storage",)),
            "cloud",
            False,
            id="middle segment does not match",
        ),
        pytest.param(
            ImportInfo(module=(), name=()),
            "requests",
            False,
            id="empty import info does not match",
        ),
    ],
)
def test_associate_dep_with_import(
    imp: ImportInfo, import_name: str, want_match: bool
) -> None:
    # arrange
    resolver = DepsResolver(imports=[imp], dependency_names=[], venvs=[])
    dep_info = DependencyInfo(name="dep")

    # act
    resolver.associate_dep_with_import(dep_info, import_name)

    # assert
    assert dep_info.associated_imports == ([imp] if want_match else [])

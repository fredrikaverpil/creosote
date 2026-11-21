import pytest

from creosote.models import DependencyInfo, ImportInfo
from creosote.resolvers import DepsResolver


@pytest.mark.parametrize(
    ["lines", "want"],
    [
        pytest.param(
            [
                "requests/__init__.py,sha256=x,1",
                "requests/api.py,sha256=x,1",
                "requests-2.32.3.dist-info/RECORD,,",
            ],
            ["requests"],
            id="regular package",
        ),
        pytest.param(
            [
                "google/cloud/storage/__init__.py,sha256=x,1",
                "google/cloud/storage/_media/__init__.py,sha256=x,1",
                "google/cloud/storage/blob.py,sha256=x,1",
            ],
            ["google.cloud.storage"],
            id="pep 420 namespace package",
        ),
        pytest.param(
            [
                "google_cloud_storage-1.44.0-py3.10-nspkg.pth,sha256=x,1",
                "google/cloud/storage/__init__.py,sha256=x,1",
                "google/cloud/storage/blob.py,sha256=x,1",
                "google_cloud_storage-1.44.0.dist-info/namespace_packages.txt,sha256=x,1",
                "google_cloud_storage-1.44.0.dist-info/top_level.txt,sha256=x,1",
            ],
            ["google.cloud.storage"],
            id="setuptools namespace_packages wheel",
        ),
        pytest.param(
            [
                "ruamel\\yaml\\__init__.py,sha256=x,1",
                "ruamel\\yaml\\anchor.py,sha256=x,1",
            ],
            ["ruamel.yaml"],
            id="windows path separators",
        ),
        pytest.param(
            [
                "setuptools/__init__.py,sha256=x,1",
                "pkg_resources/__init__.py,sha256=x,1",
            ],
            ["setuptools", "pkg_resources"],
            id="multiple top-level packages",
        ),
        pytest.param(
            [
                "opentelemetry/trace/__init__.py,sha256=x,1",
                "opentelemetry/trace/span.py,sha256=x,1",
                "opentelemetry/propagators/composite.py,sha256=x,1",
                "opentelemetry/propagators/textmap.py,sha256=x,1",
                "opentelemetry/propagators/py.typed,sha256=x,0",
            ],
            [
                "opentelemetry.trace",
                "opentelemetry.propagators.composite",
                "opentelemetry.propagators.textmap",
            ],
            id="modules in pep 420 namespace package",
        ),
        pytest.param(
            [
                "google/protobuf/__init__.py,sha256=x,1",
                "google/_upb/_message.abi3.so,sha256=x,1",
            ],
            ["google.protobuf", "google._upb._message"],
            id="extension module in pep 420 namespace package",
        ),
        pytest.param(
            [
                "foo/__init__.cpython-312-x86_64-linux-gnu.so,sha256=x,1",
                "foo/core.cpython-312-x86_64-linux-gnu.so,sha256=x,1",
            ],
            ["foo"],
            id="compiled regular package",
        ),
        pytest.param(
            [
                "six.py,sha256=x,1",
                "__init__.py,sha256=x,1",
                "../../bin/tool.py,sha256=x,1",
                "/usr/local/bin/tool.py,sha256=x,1",
                "six-1.17.0.dist-info/hook.py,sha256=x,1",
                "six-1.17.0.data/scripts/tool.py,sha256=x,1",
                "six-1.17.0.dist-info/RECORD,,",
            ],
            [],
            id="top-level modules and non-package paths",
        ),
    ],
)
def test_import_names_from_record_lines(lines: list[str], want: list[str]) -> None:
    # act
    got = DepsResolver.import_names_from_record_lines(lines)

    # assert
    assert got == want


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

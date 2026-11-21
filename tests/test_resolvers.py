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
        pytest.param(
            [
                "google/cloud/.hidden.py,sha256=x,1",
                "google/cloud/my-script.py,sha256=x,1",
                "google/cloud/foo.bak.py,sha256=x,1",
                "google/libs/libfoo-1.2.so,sha256=x,1",
                "google/cloud/storage/__init__.py,sha256=x,1",
            ],
            ["google.cloud.storage"],
            id="non-identifier and multi-dot py stems ignored",
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
            ImportInfo(module=(), name=("utils",)),
            "utils",
            True,
            id="relative import",
        ),
        pytest.param(
            ImportInfo(module=("requests", "auth"), name=("HTTPBasicAuth",)),
            "auth",
            False,
            id="trailing segment of from-import module does not match",
        ),
        pytest.param(
            ImportInfo(module=("google", "cloud"), name=("storage",)),
            "google.cloud.storage",
            True,
            id="from namespace import package",
        ),
        pytest.param(
            ImportInfo(module=("google", "cloud"), name=("storage",)),
            "google.cloud.bigquery",
            False,
            id="from namespace import other package",
        ),
        pytest.param(
            ImportInfo(module=(), name=("google", "cloud", "storage")),
            "google.cloud.storage",
            True,
            id="import dotted package",
        ),
        pytest.param(
            ImportInfo(module=("google", "cloud", "storage"), name=("Client",)),
            "google.cloud.storage",
            True,
            id="from package import symbol",
        ),
        pytest.param(
            ImportInfo(module=(), name=("google", "cloud")),
            "google.cloud.storage",
            True,
            id="ambiguous bare namespace import",
        ),
        pytest.param(
            ImportInfo(module=("google",), name=("cloud",)),
            "google.cloud.storage",
            True,
            id="ambiguous from root import namespace",
        ),
        pytest.param(
            ImportInfo(module=("google", "cloud"), name=("storage",)),
            "cloud",
            False,
            id="single-segment name does not match middle segment",
        ),
        pytest.param(
            ImportInfo(module=(), name=("google", "cloud", "storage")),
            "storage",
            False,
            id="single-segment name does not match trailing segment",
        ),
        pytest.param(
            ImportInfo(module=(), name=("requests", "api")),
            "requests",
            True,
            id="single-segment name matches leading segment",
        ),
        pytest.param(
            ImportInfo(module=("requests", "auth"), name=("HTTPBasicAuth",)),
            "requests",
            True,
            id="single-segment name matches from-import root",
        ),
        pytest.param(
            ImportInfo(
                module=("opentelemetry", "propagators", "textmap"),
                name=("TextMapPropagator",),
            ),
            "opentelemetry.propagators.textmap",
            True,
            id="module directly inside namespace package",
        ),
        pytest.param(
            ImportInfo(module=("opentelemetry", "sdk"), name=("trace",)),
            "opentelemetry.trace",
            False,
            id="other portion of namespace package",
        ),
        pytest.param(
            ImportInfo(module=(), name=()),
            "google.cloud.storage",
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


def test_resolve_skips_namespace_parent_in_canonicalized_dep_name() -> None:
    # arrange: distribution name equals the PEP 420 namespace root
    resolver = DepsResolver(
        imports=[ImportInfo(module=("acme",), name=("auth",))],
        dependency_names=[],
        venvs=[],
    )
    acme = DependencyInfo(
        name="acme",
        top_level_import_names=["acme"],
        record_import_names=["acme.core"],
        canonicalized_dep_name="acme",
    )
    acme_auth = DependencyInfo(
        name="acme-auth",
        top_level_import_names=["acme"],
        record_import_names=["acme.auth"],
        canonicalized_dep_name="acme_auth",
    )
    resolver.dependencies = [acme, acme_auth]

    # act
    resolver.resolve()
    resolver.get_unused_dependencies()

    # assert
    assert [d.name for d in resolver.unused_deps] == ["acme"]


def test_resolve_keeps_non_namespace_top_level_and_dedupes_candidates() -> None:
    # arrange
    standalone_imp = ImportInfo(module=(), name=("standalone",))
    requests_imp = ImportInfo(module=(), name=("requests",))
    resolver = DepsResolver(
        imports=[standalone_imp, requests_imp],
        dependency_names=[],
        venvs=[],
    )
    mixed = DependencyInfo(
        name="mixed-pkg",
        top_level_import_names=["ns", "standalone"],
        record_import_names=["ns.sub"],
        canonicalized_dep_name="mixed_pkg",
    )
    requests = DependencyInfo(
        name="requests",
        top_level_import_names=["requests"],
        record_import_names=["requests"],
        canonicalized_dep_name="requests",
    )
    resolver.dependencies = [mixed, requests]

    # act
    resolver.resolve()
    resolver.get_unused_dependencies()

    # assert
    assert resolver.unused_deps == []
    assert mixed.associated_imports == [standalone_imp]
    assert requests.associated_imports == [requests_imp]


@pytest.mark.parametrize(
    ["imports", "want_unused"],
    [
        pytest.param(
            [
                ImportInfo(
                    module=("opentelemetry", "propagators", "textmap"),
                    name=("TextMapPropagator",),
                )
            ],
            [],
            id="module in namespace package",
        ),
        pytest.param(
            [ImportInfo(module=("opentelemetry", "trace"), name=("Span",))],
            [],
            id="regular package in namespace package",
        ),
        pytest.param(
            [ImportInfo(module=("opentelemetry", "sdk"), name=("trace",))],
            ["opentelemetry-api"],
            id="other portion of namespace package",
        ),
    ],
)
def test_resolve_modules_in_namespace_package(
    imports: list[ImportInfo], want_unused: list[str]
) -> None:
    # arrange
    resolver = DepsResolver(imports=imports, dependency_names=[], venvs=[])
    resolver.dependencies = [
        DependencyInfo(
            name="opentelemetry-api",
            top_level_import_names=["opentelemetry"],
            record_import_names=[
                "opentelemetry.trace",
                "opentelemetry.propagators.textmap",
            ],
            canonicalized_dep_name="opentelemetry_api",
        )
    ]

    # act
    resolver.resolve()
    resolver.get_unused_dependencies()

    # assert
    assert [d.name for d in resolver.unused_deps] == want_unused

import pytest

from creosote.parsers import PackageReader


@pytest.mark.parametrize(
    ["dependency_string", "expected_package"],
    [
        ("requests==1.0.0", "requests"),
        ("requests>=1.0.0", "requests"),
        ("requests<=1.0.0", "requests"),
        ("requests~=1.0.0", "requests"),
        ("Qt.py==1.0.0", "Qt.py"),
        ("Qt_py==1.0.0", "Qt_py"),
    ],
)
def test_dependency_without_version_constraint(dependency_string, expected_package):
    assert expected_package == PackageReader.dependency_without_version_constraint(
        dependency_string
    )

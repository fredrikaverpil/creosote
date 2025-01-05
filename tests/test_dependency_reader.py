from typing import List

import pytest

from creosote.parsers import DependencyReader


@pytest.mark.parametrize(
    ["sections", "expected_dependencies"],
    [
        (
            ["project.dependencies"],
            ["dotty-dict", "loguru", "toml"],
        ),
        (
            ["project.optional-dependencies"],
            [
                "black",
                "creosote",
                "loguru-mypy",
                "mypy",
                "pytest",
                "ruff",
                "types-toml",
                "typing_extensions",
            ],
        ),
    ],
)
def test_read_toml_pep621(
    sections: List[str], expected_dependencies: List[str]
) -> None:
    reader = DependencyReader(
        deps_file="tests/deps_files/pyproject.pep621.toml",
        sections=sections,
        exclude_deps=[],
    )
    dependencies = reader.read()
    assert dependencies == expected_dependencies


@pytest.mark.parametrize(
    ["sections", "expected_dependencies"],
    [
        (
            ["dependency-groups"],
            [
                "coverage",
                "mypy",
                "pytest",
                "sphinx",
                "sphinx-rtd-theme",
                "types-requests",
                "useful-types",
            ],
        ),
    ],
)
def test_read_toml_pep735(
    sections: List[str], expected_dependencies: List[str]
) -> None:
    reader = DependencyReader(
        deps_file="tests/deps_files/pyproject.pep735.toml",
        sections=sections,
        exclude_deps=[],
    )
    dependencies = reader.read()
    assert dependencies == expected_dependencies


@pytest.mark.parametrize(
    ["sections", "expected_dependencies"],
    [
        (
            ["tool.poetry.dependencies"],
            ["dotty-dict", "loguru", "toml"],
        ),
        (
            ["tool.poetry.group.dev.dependencies"],
            ["black", "loguru-mypy", "mypy", "pytest", "ruff", "types-toml"],
        ),
        (
            ["tool.poetry.group.directrefs.dependencies"],
            ["typing_extensions"],
        ),
    ],
)
def test_read_toml_poetry(
    sections: List[str], expected_dependencies: List[str]
) -> None:
    reader = DependencyReader(
        deps_file="tests/deps_files/pyproject.poetry.toml",
        sections=sections,
        exclude_deps=[],
    )
    dependencies = reader.read()
    assert dependencies == expected_dependencies


@pytest.mark.parametrize(
    ["sections", "expected_dependencies"],
    [
        (["packages"], ["dotty-dict", "loguru", "toml"]),
        (["dev-packages"], ["pytest"]),
    ],
)
def test_read_toml_pipfile(
    sections: List[str], expected_dependencies: List[str]
) -> None:
    reader = DependencyReader(
        deps_file="tests/deps_files/Pipfile",
        sections=sections,
        exclude_deps=[],
    )
    dependencies = reader.read()
    assert dependencies == expected_dependencies


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
def test_dependency_without_version_constraint(
    dependency_string: str, expected_package: str
) -> None:
    assert expected_package == DependencyReader.dependency_without_version_constraint(
        dependency_string
    )


@pytest.mark.parametrize(
    ["dependency_string", "expected_package"],
    [
        ("pip @ file:///localbuilds/pip-1.3.1.zip", "pip"),
        ("pip @ https://github.com/pypa/pip.git", "pip"),
        ("pip @ git+https://github.com/pypa/pip.git", "pip"),
        ("pip @ git+ssh://git@github.com/pypa/pip.git", "pip"),
    ],
)
def test_pyproject_directref_package_name(
    dependency_string: str, expected_package: str
) -> None:
    assert expected_package == DependencyReader.dependency_without_direct_reference(
        dependency_string
    )

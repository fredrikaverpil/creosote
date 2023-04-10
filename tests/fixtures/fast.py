"""Fixtures used for the fast, mocked tests."""

from pathlib import Path
from typing import Callable, Generator, List, Tuple

import pytest
from pytest_mock import MockerFixture

from creosote.models import ImportInfo


@pytest.fixture()
def mock_imports_from_source_code(mocker: MockerFixture):
    def _(import_names: List[str]):
        # TODO: mock deeper down than this
        imports = [ImportInfo(module=[], name=[i]) for i in import_names]
        return mocker.patch(
            "creosote.parsers.get_module_names_from_code",
            return_value=imports,
        )

    yield _


@pytest.fixture()
def mock_dependencies_from_pyproject_toml(mocker: MockerFixture):
    def _(dependency_names: List[str]):
        # TODO: mock deeper down than this
        return mocker.patch(
            "creosote.parsers.DependencyReader.load_pyproject",
            return_value=dependency_names,
        )

    yield _


@pytest.fixture()
def create_venv(tmp_path: Path) -> Generator[Tuple[Path, Path], None, None]:
    venv_path = tmp_path / "venv"
    site_packages_path = venv_path / "lib" / "python3.7" / "site-packages"
    site_packages_path.mkdir(parents=True)
    yield venv_path, site_packages_path


@pytest.fixture()
def venv_with_top_level_txt(
    create_venv: Tuple[Path, Path]
) -> Generator[Callable, None, None]:
    def _(dependency_name: str, contents: List[str]) -> Tuple[Path, Path]:
        venv_path, site_packages_path = create_venv
        dist_info_path = site_packages_path / f"{dependency_name}-1.2.3.dist-info"
        dist_info_path.mkdir(parents=True)
        top_level_txt_path = dist_info_path / "top_level.txt"
        top_level_txt_path.write_text("\n".join(contents))
        return venv_path, top_level_txt_path

    yield _


@pytest.fixture()
def venv_with_record(create_venv: Tuple[Path, Path]) -> Generator[Callable, None, None]:
    def _(dependency_name: str, contents: List[str]) -> Tuple[Path, Path]:
        venv_path, site_packages_path = create_venv
        dist_info_path = site_packages_path / f"{dependency_name}-1.2.3.dist-info"
        dist_info_path.mkdir(parents=True)
        record_path = dist_info_path / "RECORD"
        record_path.write_text("\n".join(contents))
        return venv_path, record_path

    yield _

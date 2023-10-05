from pathlib import Path
from typing import Generator, List, Tuple

import pytest


class VenvManager:
    def __init__(self, temporary_path: Path) -> None:
        self.temporary_path = temporary_path

    def create_venv(self) -> Tuple[Path, Path]:
        """Create a simulated virtual environment."""
        venv_path = self.temporary_path / "venv"
        site_packages_path = venv_path / "lib" / "python3.8" / "site-packages"
        site_packages_path.mkdir(parents=True)
        return venv_path, site_packages_path

    def create_deps_file(
        self,
        relative_filepath: str,
        contents: List[str],
    ) -> Path:
        """Create a file which defines the dependencies.

        For example, this could be a pyproject.toml file, a Pipfile, or
        a requirements.txt file.
        """
        pyproject_path = self.temporary_path / relative_filepath
        pyproject_path.write_text("\n".join(contents))
        return pyproject_path

    def create_record(
        self,
        site_packages_path: Path,
        dependency_name: str,
        contents: List[str],
    ) -> Path:
        """Simulate an installed dependency and its RECORD file.

        This is the most reliable way for creosote to find a dependency
        and correlate its import naming against the actual dependency
        name.
        """
        dist_info_path = site_packages_path / f"{dependency_name}-1.2.3.dist-info"
        dist_info_path.mkdir(parents=True)
        record_path = dist_info_path / "RECORD"
        record_path.write_text("\n".join(contents))
        return record_path

    def create_top_level_txt(
        self,
        site_packages_path: Path,
        dependency_name: str,
        contents: List[str],
    ) -> Path:
        """Simulate an installed dependency and its top_level.txt file.

        This is a less reliable way for creosote to find a dependency
        and correlate its import naming against the actual dependency
        name.
        """
        dist_info_path = site_packages_path / f"{dependency_name}-1.2.3.dist-info"
        dist_info_path.mkdir(parents=True)
        top_level_txt_path = dist_info_path / "top_level.txt"
        top_level_txt_path.write_text("\n".join(contents))
        return top_level_txt_path

    def create_source_file(
        self,
        relative_filepath: str,
        contents: List[str],
    ) -> Path:
        """Create a source file with the given contents."""
        filepath = self.temporary_path / relative_filepath
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text("\n".join(contents))
        return filepath


@pytest.fixture()
def venv_manager(tmp_path: Path) -> Generator[VenvManager, None, None]:
    """The virtual environment manager.

    This fixture is used to create virtual environments and manage
    their contents.

    The pytest builtin "tmp_path" fixture is used here to create the
    virtual environment in a temporary directory, which is removed
    after the test is run.
    """
    yield VenvManager(tmp_path)

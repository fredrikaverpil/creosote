import shutil
from collections.abc import Generator
from pathlib import Path

import pytest


class VenvManager:
    def __init__(self, temporary_path: Path) -> None:
        self.temporary_path: Path = temporary_path

    def create_venv(self) -> tuple[Path, Path]:
        """Create a simulated virtual environment."""
        venv_path = self.temporary_path / "venv"
        site_packages_path = venv_path / "lib" / "python3.9" / "site-packages"
        site_packages_path.mkdir(parents=True)
        return venv_path, site_packages_path

    def create_deps_file(
        self,
        relative_filepath: str,
        contents: list[str],
    ) -> Path:
        """Create a file which defines the dependencies.

        For example, this could be a pyproject.toml file, a Pipfile, or
        a requirements.txt file.
        """
        pyproject_path = self.temporary_path / relative_filepath
        _ = pyproject_path.write_text("\n".join(contents))
        return pyproject_path

    def create_record(
        self,
        site_packages_path: Path,
        dependency_name: str,
        contents: list[str],
        version: str = "1.2.3",  # Add version parameter
    ) -> Path:
        """Simulate an installed dependency and its RECORD file."""
        # Use the provided version in the directory name
        dist_info_path = site_packages_path / f"{dependency_name}-{version}.dist-info"
        dist_info_path.mkdir(parents=True, exist_ok=True)
        record_path = dist_info_path / "RECORD"
        _ = record_path.write_text("\n".join(contents))
        return record_path

    def create_top_level_txt(
        self,
        site_packages_path: Path,
        dependency_name: str,
        contents: list[str],
        version: str = "1.2.3",  # Add version parameter
    ) -> Path:
        """Simulate an installed dependency and its top_level.txt file."""
        # Use the provided version in the directory name
        dist_info_path = site_packages_path / f"{dependency_name}-{version}.dist-info"
        dist_info_path.mkdir(parents=True, exist_ok=True)
        top_level_txt_path = dist_info_path / "top_level.txt"
        _ = top_level_txt_path.write_text("\n".join(contents))
        return top_level_txt_path

    def create_source_file(
        self,
        relative_filepath: str,
        contents: list[str],
    ) -> Path:
        """Create a source file with the given contents."""
        filepath = self.temporary_path / relative_filepath
        filepath.parent.mkdir(parents=True, exist_ok=True)
        _ = filepath.write_text("\n".join(contents))
        return filepath


def remove(filepath: Path) -> None:
    if filepath.exists():
        if filepath.is_file():
            filepath.unlink()  # Delete a file
        else:
            shutil.rmtree(filepath)  # Delete a directory


@pytest.fixture()
def venv_manager(tmp_path: Path) -> Generator[VenvManager, None, None]:
    """The virtual environment manager.

    This fixture is used to create virtual environments and manage
    their contents.

    The pytest builtin "tmp_path" fixture is used here to create the
    virtual environment in a temporary directory, which is removed
    after the test is run.
    """
    # setup
    vm = VenvManager(tmp_path)

    # yield
    yield vm

    # cleanup
    remove(tmp_path)

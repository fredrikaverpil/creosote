import pathlib
import subprocess
from pathlib import Path

import pytest


@pytest.fixture()
def _stash_away_project_toml():
    Path("pyproject.toml").rename("pyproject.toml.stashed")
    yield
    Path("pyproject.toml.stashed").rename("pyproject.toml")


@pytest.fixture()
def with_poetry_packages(_stash_away_project_toml, capsys, request):
    repo_root = Path.cwd()
    deps_files = Path("tests/deps_files")

    with capsys.disabled():
        Path(deps_files / "pyproject.poetry.toml").rename(repo_root / "pyproject.toml")
        subprocess.run(
            ["poetry", "add", *request.param],
            stdout=subprocess.DEVNULL,
        )
    try:
        yield
    finally:
        with capsys.disabled():
            subprocess.run(
                ["poetry", "remove", *request.param],
                stdout=subprocess.DEVNULL,
            )
            pathlib.Path("poetry.lock").unlink()
            Path(repo_root / "pyproject.toml").rename(deps_files / "pyproject.poetry.toml")


@pytest.fixture()
def with_pyproject_pep621_packages(_stash_away_project_toml, capsys, request):
    repo_root = Path.cwd()
    deps_files = Path("tests/deps_files")

    with capsys.disabled():
        Path(deps_files / "pyproject.pep621.toml").rename(repo_root / "pyproject.toml")
        subprocess.run(
            ["pip", "install", *request.param],
            stdout=subprocess.DEVNULL,
        )
    try:
        yield
    finally:
        with capsys.disabled():
            subprocess.run(
                ["pip", "uninstall", "-y", *request.param],
                stdout=subprocess.DEVNULL,
            )
            Path(repo_root / "pyproject.toml").rename(deps_files / "pyproject.pep621.toml")


@pytest.fixture()
def with_requirements_txt_packages(_stash_away_project_toml, capsys, request):
    repo_root = Path.cwd()
    deps_files = Path("tests/deps_files")

    with capsys.disabled():
        Path(deps_files / "requirements.txt").rename(repo_root / "requirements.txt")
        subprocess.run(
            ["pip", "install", *request.param],
            stdout=subprocess.DEVNULL,
        )
    try:
        yield
    finally:
        with capsys.disabled():
            subprocess.run(
                ["pip", "uninstall", "-y", *request.param],
                stdout=subprocess.DEVNULL,
            )
            Path(repo_root / "requirements.txt").rename(deps_files / "requirements.txt")

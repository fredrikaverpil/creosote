import pathlib
import subprocess

import pytest


@pytest.fixture
def with_poetry_packages(capsys, request):
    with capsys.disabled():
        subprocess.run(
            ["poetry", "add", *request.param],
            stdout=subprocess.DEVNULL,
        )
    yield
    with capsys.disabled():
        subprocess.run(
            ["git", "checkout", "pyproject.toml"],
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            ["poetry", "install", "--sync"],
            stdout=subprocess.DEVNULL,
        )
        pathlib.Path("poetry.lock").unlink()


@pytest.fixture
def with_pip_packages(capsys, request):
    with capsys.disabled():
        subprocess.run(
            ["pip", "install", *request.param],
            stdout=subprocess.DEVNULL,
        )
    yield
    with capsys.disabled():
        subprocess.run(
            ["pip", "uninstall", "-y", *request.param],
            stdout=subprocess.DEVNULL,
        )

import subprocess

import pytest


@pytest.fixture
def with_poetry_packages(capsys, request):
    with capsys.disabled():
        subprocess.run(
            ["poetry", "add"] + request.param,
            stdout=subprocess.DEVNULL,
        )
    yield
    with capsys.disabled():
        subprocess.run(
            ["poetry", "remove"] + request.param,
            stdout=subprocess.DEVNULL,
        )

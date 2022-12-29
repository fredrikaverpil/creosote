import subprocess

import pytest


@pytest.fixture
def with_packages(capsys, request):
    with capsys.disabled():
        subprocess.run(
            ["pip", "install"] + request.param,
            stdout=subprocess.DEVNULL,
        )
    yield
    with capsys.disabled():
        subprocess.run(
            ["pip", "install"] + request.param,
            stdout=subprocess.DEVNULL,
        )

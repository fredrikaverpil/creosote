import subprocess

import pytest


@pytest.fixture
def with_packages(capsys, request):
    with capsys.disabled():
        subprocess.run(["poetry", "add"] + request.param)
    yield
    with capsys.disabled():
        subprocess.run(["poetry", "remove"] + request.param)

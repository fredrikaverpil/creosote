import subprocess

import pytest


@pytest.fixture
def with_packages(capsys, request):
    with capsys.disabled():
        subprocess.run(["poetry", "install", "--remove-untracked", "--quiet"])
        subprocess.run(["poetry", "add", "--quiet"] + request.param)
    yield
    with capsys.disabled():
        subprocess.run(["poetry", "remove", "--quiet"] + request.param)

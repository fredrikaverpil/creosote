"""Pytest configuration file.

Notes:
    Do not define fixtures in this file. Instead, place them under
    tests/pytest/fixtures.

    Fixtures defined via `pytest_plugins` may not be defined in
    non-top-level `conftest.py` file. More info:
    https://docs.pytest.org/en/7.0.x/deprecations.html#pytest-plugins-in-non-top-level-conftest-files
"""


import os
from glob import glob


def refactor(string: str) -> str:
    filename, ext = os.path.splitext(string.replace(os.path.sep, "."))
    return filename


pytest_plugins = [
    refactor(fixture)
    for fixture in glob("tests/fixtures/*.py") + glob("tests/fixtures/**/*.py")
    if "__" not in fixture
]  # magic pytest variable, used for collecting fixtures

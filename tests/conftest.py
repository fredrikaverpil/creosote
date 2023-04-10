"""Pytest configuration file.

Notes:
    Do not define fixtures in this file. Instead, place them under
    tests/pytest/fixtures.

    Fixtures defined via `pytest_plugins` may not be defined in
    non-top-level `conftest.py` file. More info:
    https://docs.pytest.org/en/7.0.x/deprecations.html#pytest-plugins-in-non-top-level-conftest-files
"""


import os
from pathlib import Path


def refactor(path: Path) -> str:
    relative_path = path.relative_to(Path.cwd())
    relative_path_as_string = str(relative_path)
    return relative_path_as_string.replace(os.path.sep, ".").replace(".py", "")


pytest_plugins = [
    refactor(fixture) for fixture in Path.cwd().glob("tests/fixtures/**/*.py")
]  # magic pytest variable, used for collecting fixtures

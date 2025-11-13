import logging
from pathlib import Path

import pytest
from loguru import logger

from creosote.parsers import get_modules_from_django_settings


@pytest.mark.parametrize(
    ("content", "expected_modules"),
    [
        pytest.param(
            'INSTALLED_APPS = ["django.contrib.admin", "debug_toolbar", "myapp"]',
            ["django", "debug_toolbar", "myapp"],
            id="simple_list",
        ),
        pytest.param(
            'INSTALLED_APPS = ("django.contrib.admin", "debug_toolbar", "myapp",)',
            ["django", "debug_toolbar", "myapp"],
            id="simple_tuple",
        ),
        pytest.param(
            (
                "INSTALLED_APPS = [\n"
                "    'django.contrib.admin',\n"
                "    'django.contrib.auth',\n"
                "    'debug_toolbar.apps.DebugToolbarConfig',\n"
                "]"
            ),
            ["django", "django", "debug_toolbar"],
            id="dotted_paths",
        ),
        pytest.param(
            "INSTALLED_APPS = []",
            [],
            id="empty_list",
        ),
        pytest.param(
            "INSTALLED_APPS = get_apps()",
            [],
            id="dynamic_apps_in_func_call",
        ),
        pytest.param(
            "SECRET_KEY = '123'",
            [],
            id="no_installed_apps",
        ),
        pytest.param(
            "",
            [],
            id="empty_file",
        ),
        pytest.param(
            (
                "if True:\n"
                '    INSTALLED_APPS = ["a"]\n'
                "else:\n"
                '    INSTALLED_APPS = ["b"]\n'
            ),
            ["a", "b"],
            id="multiple_definitions",
        ),
        pytest.param(
            (
                "PREREQ_APPS = ['django.contrib.auth', 'impersonate']\n"
                "PROJECT_APPS = ['ebbs', 'events']\n"
                "INSTALLED_APPS = PREREQ_APPS + PROJECT_APPS"
            ),
            ["django", "impersonate", "ebbs", "events"],
            id="concatenated_lists",
        ),
    ],
)
def test_get_modules_from_django_settings(
    tmp_path: Path,
    content: str,
    expected_modules: list[str],
    caplog: pytest.LogCaptureFixture,
):
    """Test parsing of a Django settings file for INSTALLED_APPS."""
    # Add caplog handler to logger to fix "I/O operation on closed file"
    # See: https://loguru.readthedocs.io/en/stable/resources/migration.html#replacing-caplog-fixture-from-pytest-for-testing-logs
    logger.remove()
    logger.add(caplog.handler, format="{message}")
    caplog.set_level(logging.INFO)

    settings_file = tmp_path / "settings.py"
    settings_file.write_text(content, encoding="utf-8")

    modules = get_modules_from_django_settings(settings_file)

    assert sorted(modules) == sorted(expected_modules)


def test_get_modules_from_django_settings_file_not_found(caplog: pytest.LogCaptureFixture):
    """Test parsing a non-existent Django settings file."""
    logger.remove()
    logger.add(caplog.handler, format="{message}")
    non_existent_file = Path("non_existent_settings.py")

    modules = get_modules_from_django_settings(non_existent_file)

    assert modules == []
    assert f"Django settings file not found: {non_existent_file}" in caplog.text


def test_get_modules_from_django_settings_no_apps_found_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
):
    """Test that a warning is logged if INSTALLED_APPS is not found."""
    logger.remove()
    logger.add(caplog.handler, format="{message}")
    settings_file = tmp_path / "settings.py"
    settings_file.write_text("SECRET_KEY = '123'", encoding="utf-8")

    get_modules_from_django_settings(settings_file)

    assert f"Could not find INSTALLED_APPS in {settings_file}" in caplog.text


def test_get_modules_from_django_settings_not_a_list_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
):
    """Test that a warning is logged if INSTALLED_APPS is not a list/tuple."""
    logger.remove()
    logger.add(caplog.handler, format="{message}")
    settings_file = tmp_path / "settings.py"
    settings_file.write_text("INSTALLED_APPS = 'not-a-list'", encoding="utf-8")

    get_modules_from_django_settings(settings_file)

    assert "Could not find INSTALLED_APPS in" in caplog.text
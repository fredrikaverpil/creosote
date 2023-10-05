import os

from creosote import config


def test_load_defaults_no_file(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    configuration = config.load_defaults(pyproject)
    assert configuration == config.Config()  # Should return a default config


def test_load_defaults_no_tool_section(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[foo]")
    configuration = config.load_defaults(pyproject)
    assert configuration == config.Config()  # Should return a default config


def test_load_defaults_no_tool_creosote_section(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.foo]")
    configuration = config.load_defaults(pyproject)
    assert configuration == config.Config()  # Should return a default config


def test_load_defaults_tool_creosote_section_simple(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[tool.creosote]\nvenvs=["foo"]')
    configuration = config.load_defaults(pyproject)
    assert configuration == config.Config(venvs=["foo"])


def test_load_defaults_tool_creosote_section_complex(tmp_path):
    """More close to a real configuration."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
        [tool.creosote]
        venvs=[".virtual_environment"]
        paths=["src"]
        deps-file="requirements.txt"
        exclude-deps=[
            "importlib_resources",
            "pydantic",
        ]
    """
    )
    configuration = config.load_defaults(pyproject)
    assert configuration == config.Config(
        venvs=[".virtual_environment"],
        paths=["src"],
        deps_file="requirements.txt",
        exclude_deps=[
            "importlib_resources",
            "pydantic",
        ],  # Tests hyphen -> underscore logic.
    )


def test_load_defaults_no_venv():
    # Unset VIRTUAL_ENV environment variable
    os.environ.pop("VIRTUAL_ENV", None)
    configuration = config.Config()
    assert configuration.venvs == [".venv"]


def test_load_defaults_set_venv():
    os.environ["VIRTUAL_ENV"] = "foo"
    configuration = config.Config()
    assert configuration.venvs == ["foo"]

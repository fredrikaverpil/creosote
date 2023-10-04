import os
from pathlib import Path
from typing import Callable, List, Tuple

import pytest
from _pytest.capture import CaptureFixture

from creosote import cli, config


def test_no_unused_and_found_in_top_level_txt(
    capsys: CaptureFixture,
    mock_dependencies_from_pyproject_toml: Callable,
    mock_imports_from_source_code: Callable,
    venv_with_top_level_txt: Callable,
):
    """The dependency is found in the top_level.txt file."""
    mock_dependencies_from_pyproject_toml(["YoloYolo"])
    mock_imports_from_source_code(["yolo"])
    venv_path, _top_level_txt_path = venv_with_top_level_txt(
        dependency_name="YoloYolo", contents=["yolo"]
    )

    exit_code = cli.main(
        ["--venv", str(venv_path), "--format", "no-color", "--verbose"]
    )
    actual_output = capsys.readouterr().err.splitlines()

    assert "[YoloYolo] found import name(s) via top_level.txt: yolo ⭐️" in actual_output
    assert "[YoloYolo] did not find RECORD in venv" in actual_output
    assert "No unused dependencies found!" in actual_output[-1]
    assert exit_code == 0


def test_no_unused_and_found_via_record_file(
    capsys: CaptureFixture,
    mock_dependencies_from_pyproject_toml: Callable,
    mock_imports_from_source_code: Callable,
    venv_with_record: Callable,
):
    """The dependency is found in the RECORD file."""
    mock_dependencies_from_pyproject_toml(["YoloYolo"])
    mock_imports_from_source_code(["yolo"])
    venv_path, _record_path = venv_with_record(
        dependency_name="YoloYolo",
        contents=[
            "yolo/__init__.py,sha256=4skFj_sdo33SWqTefV1JBAvZiT4MY_pB5yaRL5DMNVs,240"
        ],
    )

    exit_code = cli.main(
        ["--venv", str(venv_path), "--format", "no-color", "--verbose"]
    )
    actual_output = capsys.readouterr().err.splitlines()

    assert "[YoloYolo] did not find top_level.txt in venv" in actual_output
    assert "[YoloYolo] found import name via RECORD: yolo ⭐️" in actual_output
    assert "No unused dependencies found!" in actual_output[-1]
    assert exit_code == 0


def test_no_unused_and_found_via_canonicalization(
    capsys: CaptureFixture,
    create_venv: Tuple[Path, Path],
    mock_dependencies_from_pyproject_toml: Callable,
    mock_imports_from_source_code: Callable,
):
    """The dependency is found by canonicalization of dep name."""
    mock_dependencies_from_pyproject_toml(dependency_names=["Yo-Lo"])
    mock_imports_from_source_code(import_names=["Yo_Lo"])
    venv_path, _site_packages_path = create_venv

    exit_code = cli.main(
        ["--venv", str(venv_path), "--format", "no-color", "--verbose"]
    )
    actual_output = capsys.readouterr().err.splitlines()

    assert "[Yo-Lo] did not find top_level.txt in venv" in actual_output
    assert "[Yo-Lo] did not find RECORD in venv" in actual_output
    assert "[Yo-Lo] relying on canonicalization fallback: Yo_Lo 🤞" in actual_output
    assert "No unused dependencies found!" in actual_output[-1]
    assert exit_code == 0


def test_unused_found(
    capsys: CaptureFixture,
    create_venv: Tuple[Path, Path],
    mock_dependencies_from_pyproject_toml: Callable,
    mock_imports_from_source_code: Callable,
):
    """Unused dependency was detected."""
    mock_dependencies_from_pyproject_toml(dependency_names=["yolo"])
    mock_imports_from_source_code(import_names=["dummy"])
    venv_path, _site_packages_path = create_venv

    expected_unused_packages = ["yolo"]

    exit_code = cli.main(["--venv", str(venv_path), "--format", "porcelain"])

    captured = capsys.readouterr()

    assert captured.out.splitlines() == expected_unused_packages
    assert exit_code == 1


def test_multiple_args(
    capsys: CaptureFixture,
    mock_dependencies_from_pyproject_toml: Callable,
    venv_with_top_level_txts: Callable,
):
    """Excluded dependency is used but never imported by source code."""
    mock_dependencies_from_pyproject_toml(dependency_names=["foo", "bar"])

    venv_path, _top_level_txt_path = venv_with_top_level_txts(
        dependency_names=["foo", "bar"], contents=["baz"]
    )

    expected_unused_packages: List[str] = []

    exit_code = cli.main(
        [
            "--venv",
            str(venv_path),
            "--path",
            "src/creosote/cli.py",
            "--path",
            "src/creosote/config.py",
            "--exclude-dep",
            "foo",
            "--exclude-dep",
            "bar",
            "--format",
            "porcelain",
        ]
    )

    captured = capsys.readouterr()

    assert captured.out.splitlines() == expected_unused_packages
    assert exit_code == 0


def test_detected_indirectly_used_but_not_imported_and_excluded(
    capsys: CaptureFixture,
    mock_dependencies_from_pyproject_toml: Callable,
    mock_imports_from_source_code: Callable,
    venv_with_top_level_txt: Callable,
):
    """Excluded dependency is used but never imported by source code."""
    mock_dependencies_from_pyproject_toml(dependency_names=["hello", "bye"])
    mock_imports_from_source_code(import_names=["hello"])

    venv_path, _top_level_txt_path = venv_with_top_level_txt(
        dependency_name="hello", contents=["hello"]
    )

    expected_unused_packages: List[str] = []

    exit_code = cli.main(
        [
            "--venv",
            str(venv_path),
            "--exclude-dep",
            "bye",
            "--format",
            "porcelain",
        ]
    )

    captured = capsys.readouterr()

    assert captured.out.splitlines() == expected_unused_packages
    assert exit_code == 0


@pytest.mark.parametrize(
    ["use_feature", "expected_exit_code"],
    [
        ("", 0),  # no feature in use
        ("fail-excluded-and-not-installed", 1),
    ],
)
def test_unused_found_because_excluded_but_not_installed(  # noqa: PLR0913
    capsys: CaptureFixture,
    mock_dependencies_from_pyproject_toml: Callable,
    mock_imports_from_source_code: Callable,
    create_venv: Tuple[Path, Path],
    use_feature: str,
    expected_exit_code: int,
):
    """Excluded dependency is used but never imported by source code."""
    mock_dependencies_from_pyproject_toml(dependency_names=["hello", "bye"])
    mock_imports_from_source_code(import_names=["hello"])

    venv_path, _site_packages_path = create_venv
    expected_unused_packages: List[str] = []

    args = [
        "--venv",
        str(venv_path),
        "--exclude-dep",
        "bye",
        "--format",
        "porcelain",
    ]
    if use_feature:
        args.extend(["--use-feature", use_feature])

    exit_code = cli.main(args)
    captured = capsys.readouterr()

    assert captured.out.splitlines() == expected_unused_packages
    assert exit_code == expected_exit_code


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

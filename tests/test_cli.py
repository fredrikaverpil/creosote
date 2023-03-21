from pathlib import Path

from _pytest.capture import CaptureFixture
from pytest_mock import MockerFixture

from creosote import cli
from creosote.models import ImportInfo


def test_no_unused_and_found_in_top_level_txt(
    capsys: CaptureFixture,
    mocker: MockerFixture,
    tmp_path: Path,
):
    """The dependency if found in top_level.txt file."""
    imports_from_code = [ImportInfo(module=[], name=["yolo"])]
    dependency_names_from_deps_file = ["yolo"]
    venv_path = tmp_path / "venv"
    site_packages_path = venv_path / "lib" / "python3.7" / "site-packages"
    dist_info_path = site_packages_path / "yolo-1.2.3.dist-info"
    dist_info_path.mkdir(parents=True)
    top_level_txt_path = dist_info_path / "top_level.txt"
    top_level_txt_path.write_text("yolo\n")

    expected_unused_packages = []

    mocker.patch(
        "creosote.parsers.get_module_names_from_code",
        return_value=imports_from_code,
    )
    mocker.patch(
        "creosote.parsers.DependencyReader.load_pyproject",
        return_value=dependency_names_from_deps_file,
    )
    mocked_map_via_distlib = mocker.patch(
        "creosote.resolvers.DepsResolver.map_dep_to_module_via_distlib",
        return_value=False,
    )
    mocked_map_via_canonicalization = mocker.patch(
        "creosote.resolvers.DepsResolver.map_dep_to_canonical_name",
        return_value="",
    )

    exit_code = cli.main(
        ["--venv", str(venv_path), "--format", "porcelain", "--verbose"]
    )

    captured = capsys.readouterr()

    mocked_map_via_distlib.assert_not_called()
    mocked_map_via_canonicalization.assert_called_once()
    assert captured.out.splitlines() == expected_unused_packages
    assert exit_code == 0


def test_no_unused_and_found_via_distlib_db(
    capsys: CaptureFixture,
    mocker: MockerFixture,
    tmp_path: Path,
):
    """The dependency is found by distlib db lookup."""
    imports_from_code = [ImportInfo(module=[], name=["dotty_dict"])]
    dependency_names_from_deps_file = ["dotty-dict"]
    venv_path = tmp_path / "venv"

    expected_unused_packages = []

    mocker.patch(
        "creosote.parsers.get_module_names_from_code",
        return_value=imports_from_code,
    )
    mocker.patch(
        "creosote.parsers.DependencyReader.load_pyproject",
        return_value=dependency_names_from_deps_file,
    )
    mocker.patch(
        "creosote.resolvers.DepsResolver.map_dep_to_import_via_top_level_txt_file",
        return_value=False,
    )
    mocker.patch(
        "creosote.resolvers.DepsResolver.canonicalize_module_name",
        return_value=None,
    )
    mocked_map_via_canonicalization = mocker.patch(
        "creosote.resolvers.DepsResolver.map_dep_to_canonical_name",
        return_value="",
    )

    exit_code = cli.main(["--venv", str(venv_path), "--format", "porcelain"])

    captured = capsys.readouterr()

    mocked_map_via_canonicalization.assert_called_once()
    assert captured.out.splitlines() == expected_unused_packages
    assert exit_code == 0


def test_no_unused_and_found_via_canonicalization(
    capsys: CaptureFixture,
    mocker: MockerFixture,
    tmp_path: Path,
):
    """The dependency is found by canonicalization of dep name."""
    imports_from_code = [ImportInfo(module=[], name=["dotty_dict"])]
    dependency_names_from_deps_file = ["dotty-dict"]
    venv_path = tmp_path / "venv"

    expected_unused_packages = []

    mocker.patch(
        "creosote.parsers.get_module_names_from_code",
        return_value=imports_from_code,
    )
    mocker.patch(
        "creosote.parsers.DependencyReader.load_pyproject",
        return_value=dependency_names_from_deps_file,
    )
    mocker.patch(
        "creosote.resolvers.DepsResolver.map_dep_to_import_via_top_level_txt_file",
        return_value=False,
    )
    mocker.patch(
        "creosote.resolvers.DepsResolver.map_dep_to_module_via_distlib",
        return_value=False,
    )

    exit_code = cli.main(["--venv", str(venv_path), "--format", "porcelain"])

    captured = capsys.readouterr()

    assert captured.out.splitlines() == expected_unused_packages
    assert exit_code == 0


def test_unused_found(
    capsys: CaptureFixture,
    mocker: MockerFixture,
    tmp_path: Path,
):
    """Unused dependency was detected."""
    imports_from_code = [ImportInfo(module=[], name=["dotty_dict"])]
    dependency_names_from_deps_file = ["dotty-dict"]
    venv_path = tmp_path / "venv"

    expected_unused_packages = ["dotty-dict"]

    mocker.patch(
        "creosote.parsers.get_module_names_from_code",
        return_value=imports_from_code,
    )
    mocker.patch(
        "creosote.parsers.DependencyReader.load_pyproject",
        return_value=dependency_names_from_deps_file,
    )
    mocker.patch(
        "creosote.resolvers.DepsResolver.map_dep_to_import_via_top_level_txt_file",
        return_value=False,
    )
    mocker.patch(
        "creosote.resolvers.DepsResolver.map_dep_to_module_via_distlib",
        return_value=False,
    )
    mocker.patch(
        "creosote.resolvers.DepsResolver.map_dep_to_canonical_name",
        return_value="",
    )

    exit_code = cli.main(["--venv", str(venv_path), "--format", "porcelain"])

    captured = capsys.readouterr()

    assert captured.out.splitlines() == expected_unused_packages
    assert exit_code == 1


def test_detected_indirectly_used_but_not_imported_and_excluded(
    capsys: CaptureFixture,
    mocker: MockerFixture,
    tmp_path: Path,
):
    """Excluded dependency is used but never imported by source code."""
    imports_from_code = [ImportInfo(module=[], name=["dotty_dict"])]
    dependency_names_from_deps_file = ["dotty-dict", "pyodbc"]
    excluded_dependencies = "pyodbc"
    venv_path = tmp_path / "venv"
    site_packages_path = venv_path / "lib" / "python3.7" / "site-packages"
    dist_info_path = site_packages_path / "pyodbc-1.2.3.dist-info"
    dist_info_path.mkdir(parents=True)
    top_level_txt_path = dist_info_path / "top_level.txt"
    top_level_txt_path.write_text("pyodbc\n")
    expected_unused_packages = []

    mocker.patch(
        "creosote.parsers.get_module_names_from_code",
        return_value=imports_from_code,
    )
    mocker.patch(
        "creosote.parsers.DependencyReader.load_pyproject",
        return_value=dependency_names_from_deps_file,
    )
    mocker.patch(
        "creosote.resolvers.DepsResolver.map_dep_to_import_via_top_level_txt_file",
        return_value=False,
    )
    mocker.patch(
        "creosote.resolvers.DepsResolver.map_dep_to_module_via_distlib",
        return_value=False,
    )

    exit_code = cli.main(
        [
            "--venv",
            str(venv_path),
            "--exclude-deps",
            excluded_dependencies,
            "--format",
            "porcelain",
        ]
    )

    captured = capsys.readouterr()

    assert captured.out.splitlines() == expected_unused_packages
    assert exit_code == 0

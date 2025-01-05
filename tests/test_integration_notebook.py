from typing import Any

from _pytest.capture import CaptureFixture

from creosote import cli
from tests.fixtures.integration import VenvManager


def test_jupyter_ok(
    venv_manager: VenvManager,
    capsys: CaptureFixture[Any],  # pyright: ignore[reportExplicitAny]
) -> None:
    venv_path, site_packages_path = venv_manager.create_venv()

    deps_filename = "pyproject.toml"
    toml_section = "project.dependencies"
    deps_file_contents = [
        "[project]",
        "dependencies = [",
        '"nbconvert",',
        '"nbformat",',
        "]",
    ]

    installed_dependencies = [
        "nbconvert",
        "nbformat",
    ]

    for dependency_name in installed_dependencies:
        _ = venv_manager.create_record(
            site_packages_path=site_packages_path,
            dependency_name=dependency_name,
            contents=[
                f"{dependency_name}/__init__.py,sha256=4skFj_sdo33SWqTefV1JBAvZiT4MY_pB5yaRL5DMNVs,240"
            ],
        )

    deps_filepath = venv_manager.create_deps_file(
        relative_filepath=deps_filename,
        contents=deps_file_contents,
    )

    with open("tests/notebook.ipynb", "r") as notebook:
        contents = notebook.readlines()

    source_file = venv_manager.create_source_file(
        relative_filepath="src/foo.ipynb",
        contents=contents,
    )

    args = [
        "--venv",
        str(venv_path),
        "--path",
        str(source_file),
        "--deps-file",
        str(deps_filepath),
        "--section",
        toml_section,
        "--format",
        "no-color",
    ]

    if not toml_section:
        # this is the case for requirements.txt
        args.remove("--section")
        args.remove(toml_section)

    # act
    exit_code = cli.main(args)
    actual_output = capsys.readouterr().err.splitlines()

    # assert
    assert actual_output == [
        f"Found dependencies in {deps_filepath}: nbconvert, nbformat",
        "No unused dependencies found! ✨",
    ]
    assert exit_code == 0

"""This file holds all integration tests.

The general idea:
- Invoke the test by runing the CLI and provide arguments.
- Assert on the output.
- Use pytest fixtures to set up...
  - A dummy virtual environment.
  - One or more top_level_txt files.
  - One or more RECORD files.
  - A dependency specification file (e.g. pyproject.toml).
  - Source code with imports.

"""


from typing import List

import pytest
from _pytest.capture import CaptureFixture

from creosote import cli
from tests.fixtures.integration import VenvManager


def test_creosote_project_success(
    venv_manager: VenvManager,
    capsys: CaptureFixture,
) -> None:
    """Test running cresote on its own project, successfully."""

    # arrange

    venv_path, site_packages_path = venv_manager.create_venv()
    for dependency_name in ["dotty-dict", "loguru", "pip-requirements-parser", "toml"]:
        venv_manager.create_record(
            site_packages_path=site_packages_path,
            dependency_name=dependency_name,
            contents=[
                f"{dependency_name}/__init__.py,sha256=4skFj_sdo33SWqTefV1JBAvZiT4MY_pB5yaRL5DMNVs,240"
            ],
        )

    # act

    exit_code = cli.main(
        [
            "--venv",
            str(venv_path),
            "--path",
            "src",  # use this project's "src" folder
            "--deps-file",
            "pyproject.toml",  # use this project's own pyproject.toml
            "--format",
            "no-color",
        ]
    )
    actual_output = capsys.readouterr().err.splitlines()

    # assert

    assert actual_output == [
        "Found dependencies in pyproject.toml: "
        "dotty-dict, loguru, pip-requirements-parser, toml",
        "No unused dependencies found! ✨",
    ]
    assert exit_code == 0


@pytest.mark.parametrize(
    argnames=["deps_filename", "toml_section", "deps_file_contents"],
    argvalues=[
        pytest.param(
            *[
                "pyproject.toml",
                "project.dependencies",
                [
                    "[project]",
                    "dependencies = [",
                    '"dotty-dict>=1.3.1,<1.4",',
                    '"loguru>=0.6.0,<0.8",',
                    '"pip-requirements-parser>=32.0.1,<33.1",',
                    '"toml>=0.10.2,<0.11",',
                    "]",
                ],
            ],
            id="PEP-621 project dependencies",
        ),
        pytest.param(
            *[
                "pyproject.toml",
                "project.optional-dependencies",
                [
                    "[project.optional-dependencies]",
                    "my_group = [",
                    '"dotty-dict>=1.3.1,<1.4",',
                    '"loguru>=0.6.0,<0.8",',
                    '"pip-requirements-parser>=32.0.1,<33.1",',
                    '"toml>=0.10.2,<0.11",',
                    "]",
                ],
            ],
            id="PEP-621 optional dependencies",
        ),
        pytest.param(
            *[
                "requirements.txt",
                "",  # NOTE: this is not needed for requirements.txt
                [
                    "dotty-dict>=1.3.1,<1.4",
                    "loguru>=0.6.0,<0.8",
                    "pip-requirements-parser>=32.0.1,<33.1",
                    "toml>=0.10.2,<0.11",
                ],
            ],
            id="Pipenv dev packages",
        ),
        pytest.param(
            *[
                "pyproject.toml",
                "tool.pdm.dev-dependencies",
                [
                    "[tool.pdm.dev-dependencies]",
                    "my_group = [",
                    '"dotty-dict>=1.3.1,<1.4",',
                    '"loguru>=0.6.0,<0.8",',
                    '"pip-requirements-parser>=32.0.1,<33.1",',
                    '"toml>=0.10.2,<0.11",',
                    "]",
                ],
            ],
            id="PDM dev dependencies",
        ),
        pytest.param(
            *[
                "pyproject.toml",
                "tool.poetry.dependencies",
                [
                    "[tool.poetry.dependencies]",
                    'python = ">=3.11, <3.12"',
                    'dotty-dict = "^1.3.1"',
                    'loguru = "^0.6.0"',
                    'pip-requirements-parser = "^32.0.1"',
                    'toml = "^0.10.2"',
                ],
            ],
            id="Poetry",
        ),
        pytest.param(
            *[
                "Pipfile",
                "packages",
                [
                    "[packages]",
                    'dotty-dict = "^1.3.1"',
                    'loguru = "^0.6.0"',
                    'pip-requirements-parser = "^32.0.1"',
                    'toml = "^0.10.2"',
                ],
            ],
            id="Pipenv",
        ),
        pytest.param(
            *[
                "Pipfile",
                "dev-packages",
                [
                    "[dev-packages]",
                    'dotty-dict = "^1.3.1"',
                    'loguru = "^0.6.0"',
                    'pip-requirements-parser = "^32.0.1"',
                    'toml = "^0.10.2"',
                ],
            ],
            id="Pipenv dev packages",
        ),
    ],
)
@pytest.mark.parametrize(["scan_type"], [["RECORD"], ["top_level.txt"]])
def test_no_unused_dependencies_found(  # noqa: PLR0913
    venv_manager: VenvManager,
    capsys: CaptureFixture,
    scan_type: str,
    deps_filename: str,
    toml_section: str,
    deps_file_contents: List[str],
) -> None:
    """Test simulated setup without any unused dependencies found."""

    # arrange

    venv_path, site_packages_path = venv_manager.create_venv()

    deps_filepath = venv_manager.create_deps_file(
        relative_filepath=deps_filename,
        contents=deps_file_contents,
    )

    installed_dependencies = [
        "dotty-dict",
        "loguru",
        "pip-requirements-parser",
        "toml",
    ]

    for dependency_name in installed_dependencies:
        if scan_type == "RECORD":
            venv_manager.create_record(
                site_packages_path=site_packages_path,
                dependency_name=dependency_name,
                contents=[
                    f"{dependency_name}/__init__.py,sha256=4skFj_sdo33SWqTefV1JBAvZiT4MY_pB5yaRL5DMNVs,240"
                ],
            )
        elif scan_type == "top_level.txt":
            venv_manager.create_top_level_txt(
                site_packages_path=site_packages_path,
                dependency_name=dependency_name,
                contents=["yolo"],
            )
        else:
            raise NotImplementedError("Case not implemented.")

    source_file = venv_manager.create_source_file(
        relative_filepath="src/foo.py",
        contents=[
            "from dotty_dict import Dotty, dotty",
            "from loguru import logger",
            "from pip_requirements_parser import RequirementsFile",
            "import toml",
        ],
    )

    # act

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

    exit_code = cli.main(args)
    actual_output = capsys.readouterr().err.splitlines()

    # assert

    assert actual_output == [
        f"Found dependencies in {deps_filepath}: "
        "dotty-dict, loguru, pip-requirements-parser, toml",
        "No unused dependencies found! ✨",
    ]
    assert exit_code == 0


@pytest.mark.parametrize(
    argnames=["deps_filename", "toml_section", "deps_file_contents"],
    argvalues=[
        pytest.param(
            *[
                "pyproject.toml",
                "project.dependencies",
                [
                    "[project]",
                    "dependencies = [",
                    '"dotty-dict>=1.3.1,<1.4",',
                    '"loguru>=0.6.0,<0.8",',
                    '"pip-requirements-parser>=32.0.1,<33.1",',
                    '"toml>=0.10.2,<0.11",',
                    '"yolo",',  # NOTE: this is the unused dependency
                    "]",
                ],
            ],
            id="PEP-621 project dependencies",
        ),
        pytest.param(
            *[
                "pyproject.toml",
                "project.optional-dependencies",
                [
                    "[project.optional-dependencies]",
                    "my_group = [",
                    '"dotty-dict>=1.3.1,<1.4",',
                    '"loguru>=0.6.0,<0.8",',
                    '"pip-requirements-parser>=32.0.1,<33.1",',
                    '"toml>=0.10.2,<0.11",',
                    '"yolo",',  # NOTE: this is the unused dependency
                    "]",
                ],
            ],
            id="PEP-621 optional dependencies",
        ),
        pytest.param(
            *[
                "requirements.txt",
                "",  # NOTE: this is not needed for requirements.txt
                [
                    "dotty-dict>=1.3.1,<1.4",
                    "loguru>=0.6.0,<0.8",
                    "pip-requirements-parser>=32.0.1,<33.1",
                    "toml>=0.10.2,<0.11",
                    "yolo",  # NOTE: this is the unused dependency
                ],
            ],
            id="Pipenv dev packages",
        ),
        pytest.param(
            *[
                "pyproject.toml",
                "tool.pdm.dev-dependencies",
                [
                    "[tool.pdm.dev-dependencies]",
                    "my_group = [",
                    '"dotty-dict>=1.3.1,<1.4",',
                    '"loguru>=0.6.0,<0.8",',
                    '"pip-requirements-parser>=32.0.1,<33.1",',
                    '"toml>=0.10.2,<0.11",',
                    '"yolo",',  # NOTE: this is the unused dependency
                    "]",
                ],
            ],
            id="PDM dev dependencies",
        ),
        pytest.param(
            *[
                "pyproject.toml",
                "tool.poetry.dependencies",
                [
                    "[tool.poetry.dependencies]",
                    'python = ">=3.11, <3.12"',
                    'dotty-dict = "^1.3.1"',
                    'loguru = "^0.6.0"',
                    'pip-requirements-parser = "^32.0.1"',
                    'toml = "^0.10.2"',
                    'yolo = "^9.9.9"',  # NOTE: this is the unused dependency
                ],
            ],
            id="Poetry",
        ),
        pytest.param(
            *[
                "Pipfile",
                "packages",
                [
                    "[packages]",
                    'dotty-dict = "^1.3.1"',
                    'loguru = "^0.6.0"',
                    'pip-requirements-parser = "^32.0.1"',
                    'toml = "^0.10.2"',
                    'yolo = "^9.9.9"',  # NOTE: this is the unused dependency
                ],
            ],
            id="Pipenv",
        ),
        pytest.param(
            *[
                "Pipfile",
                "dev-packages",
                [
                    "[dev-packages]",
                    'dotty-dict = "^1.3.1"',
                    'loguru = "^0.6.0"',
                    'pip-requirements-parser = "^32.0.1"',
                    'toml = "^0.10.2"',
                    'yolo = "^9.9.9"',  # NOTE: this is the unused dependency
                ],
            ],
            id="Pipenv dev packages",
        ),
    ],
)
@pytest.mark.parametrize(["scan_type"], [["RECORD"], ["top_level.txt"]])
@pytest.mark.parametrize(["exclude_unused_dep"], [[False], [True]])
@pytest.mark.parametrize(["unused_dep_is_installed"], [[False], [True]])
def test_one_unused_dependency_found(  # noqa: PLR0913
    venv_manager: VenvManager,
    capsys: CaptureFixture,
    scan_type: str,
    deps_filename: str,
    toml_section: str,
    deps_file_contents: List[str],
    exclude_unused_dep: bool,
    unused_dep_is_installed: bool,
) -> None:
    """Test showcasing one unused dependency being found.

    When the 'yolo' dependency is found to be unused, this test covers:
      - when the 'yolo' dependency is installed vs not installed.
      - when the 'yolo' dependency is excluded vs not excluded.
    """

    # arrange

    venv_path, site_packages_path = venv_manager.create_venv()

    deps_filepath = venv_manager.create_deps_file(
        relative_filepath=deps_filename,
        contents=deps_file_contents,
    )

    installed_dependencies = [
        "dotty-dict",
        "loguru",
        "pip-requirements-parser",
        "toml",
    ]

    if unused_dep_is_installed:
        # having the unused dependency installed should trigger a warning
        installed_dependencies.append("yolo")

    for dependency_name in installed_dependencies:
        if scan_type == "RECORD":
            venv_manager.create_record(
                site_packages_path=site_packages_path,
                dependency_name=dependency_name,
                contents=[
                    f"{dependency_name}/__init__.py,sha256=4skFj_sdo33SWqTefV1JBAvZiT4MY_pB5yaRL5DMNVs,240"
                ],
            )
        elif scan_type == "top_level.txt":
            venv_manager.create_top_level_txt(
                site_packages_path=site_packages_path,
                dependency_name=dependency_name,
                contents=["yolo"],
            )
        else:
            raise NotImplementedError("Case not implemented.")

    source_file = venv_manager.create_source_file(
        relative_filepath="src/foo.py",
        contents=[
            "from dotty_dict import Dotty, dotty",
            "from loguru import logger",
            "from pip_requirements_parser import RequirementsFile",
            "import toml",
            # NOTE: there is no yolo import, hence it is unused
        ],
    )

    # act

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

    if exclude_unused_dep:
        args.extend(["--exclude-dep", "yolo"])

    exit_code = cli.main(args)
    actual_output = capsys.readouterr().err.splitlines()

    # assert

    if exclude_unused_dep and unused_dep_is_installed:
        assert "No unused dependencies found! ✨" in actual_output
        assert exit_code == 0
    elif exclude_unused_dep and not unused_dep_is_installed:
        assert (
            "Excluded dependencies not found in virtual environment: yolo"
            in actual_output
        )
        assert "No unused dependencies found! ✨" in actual_output
        assert exit_code == 0
    elif not exclude_unused_dep:
        assert "Unused dependencies found: yolo" in actual_output
        assert exit_code == 1
    else:
        raise NotImplementedError("Case not implemented.")


def test_multiple_paths(venv_manager: VenvManager, capsys: CaptureFixture) -> None:
    """This tests the case where multiple paths are passed as arguments."""

    # arrange

    venv_path, site_packages_path = venv_manager.create_venv()

    deps_filepath = venv_manager.create_deps_file(
        relative_filepath="pyproject.toml",
        contents=[
            "[project]",
            "dependencies = [",
            '"dotty-dict>=1.3.1,<1.4",',
            '"loguru>=0.6.0,<0.8",',
            '"pip-requirements-parser>=32.0.1,<33.1",',
            '"toml>=0.10.2,<0.11",',
            "]",
        ],
    )

    toml_section = "project.dependencies"

    deps_and_imports_map = {
        "dotty-dict": "from dotty_dict import Dotty, dotty",
        "loguru": "from loguru import logger",
        "pip-requirements-parser": "from pip_requirements_parser import RequirementsFile",  # noqa: E501
        "toml": "import toml",
    }

    installed_dependencies = deps_and_imports_map.keys()
    imports = deps_and_imports_map.values()

    for dependency_name in installed_dependencies:
        venv_manager.create_record(
            site_packages_path=site_packages_path,
            dependency_name=dependency_name,
            contents=[
                f"{dependency_name}/__init__.py,sha256=4skFj_sdo33SWqTefV1JBAvZiT4MY_pB5yaRL5DMNVs,240"
            ],
        )

    source_files = []
    for idx, import_ in enumerate(imports):
        source_files.append(
            venv_manager.create_source_file(
                relative_filepath=f"src/file{idx}.py",
                contents=[import_],
            )
        )

    # act

    args = [
        "--venv",
        str(venv_path),
        "--deps-file",
        str(deps_filepath),
        "--section",
        toml_section,
        "--format",
        "no-color",
    ]

    for source_file in source_files:
        args.extend(["--path", str(source_file)])

    exit_code = cli.main(args)
    actual_output = capsys.readouterr().err.splitlines()
    num_paths = len([arg for arg in args if arg == "--path"])
    number_of_paths = 4

    # assert

    assert num_paths == len(source_files) == number_of_paths
    assert "No unused dependencies found! ✨" in actual_output
    assert exit_code == 0

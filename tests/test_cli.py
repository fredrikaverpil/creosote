
import pytest

from creosote import cli


@pytest.mark.parametrize(
    "with_poetry_packages", [["PyYAML", "protobuf"]], indirect=True
)
def test_files_as_path_poetry(capsys, with_poetry_packages):
    cli.main(
        [
            "-p",
            "src/creosote/formatters.py",
            "src/creosote/models.py",
            "-f",
            "porcelain",
            "-s",
            "tool.poetry.dependencies",
        ]
    )

    captured = capsys.readouterr()
    expected_log = "distlib\ndotty-dict\nprotobuf\npyyaml\ntoml\n"

    assert captured.out == expected_log


def test_files_as_path_pep621(capsys):
    cli.main(
        [
            "-p",
            "src/creosote/formatters.py",
            "src/creosote/models.py",
            "-f",
            "porcelain",
            "-s",
            "project.dependencies",
        ]
    )

    captured = capsys.readouterr()
    expected_log = "distlib\ndotty-dict\ntoml\n"

    assert captured.out == expected_log


@pytest.mark.parametrize("with_pip_packages", [["boto3"]], indirect=True)
def test_files_as_path_pep621_git(capsys, with_pip_packages):
    cli.main(
        [
            "-p",
            "src/creosote/formatters.py",
            "src/creosote/models.py",
            "-f",
            "porcelain",
            "-s",
            "project.optional-dependencies.test-git-link",
        ]
    )

    captured = capsys.readouterr()
    expected_log = "boto3\n"

    assert captured.out == expected_log

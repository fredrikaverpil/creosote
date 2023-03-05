import pytest

from creosote import cli


@pytest.mark.parametrize(
    "with_poetry_packages", [["PyYAML", "protobuf"]], indirect=True
)
def test_pyproject_poetry(capsys, with_poetry_packages):
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


def test_pyproject_pep621(capsys):
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


@pytest.mark.parametrize("with_pyproject_pep621_packages", [["idna"]], indirect=True)
def test_pyproject_pep621_directrefs(capsys, with_pyproject_pep621_packages):
    cli.main(
        [
            "-p",
            "src/creosote/formatters.py",
            "src/creosote/models.py",
            "-f",
            "porcelain",
            "-s",
            "project.optional-dependencies.directrefs",
        ]
    )

    captured = capsys.readouterr()
    expected_log = "idna\n"

    assert captured.out == expected_log


@pytest.mark.parametrize("with_requirements_txt_packages", [["idna"]], indirect=True)
def test_requirementstxt_directrefs(capsys, with_requirements_txt_packages):
    cli.main(
        [
            "-p",
            "src/creosote/formatters.py",
            "src/creosote/models.py",
            "-f",
            "porcelain",
            "-d",
            "requirements.txt",
        ]
    )

    captured = capsys.readouterr()
    expected_log = "boto3\nidna\nrequests\n"

    assert captured.out == expected_log

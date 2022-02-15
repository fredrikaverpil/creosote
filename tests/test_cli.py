import pytest

from creosote import cli


@pytest.mark.parametrize("with_packages", [["PyYAML", "protobuf"]], indirect=True)
def test_files_as_path(capsys, with_packages):

    cli.main(
        [
            "-p",
            "src/creosote/formatters.py",
            "src/creosote/models.py",
            "-f",
            "porcelain",
        ]
    )

    captured = capsys.readouterr()
    expected_log = "PyYAML\ndistlib\nprotobuf\ntoml\n"

    assert captured.out == expected_log

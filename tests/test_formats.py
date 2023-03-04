import pytest

from creosote import cli


@pytest.mark.parametrize(
    "with_poetry_packages", [["PyYAML", "protobuf"]], indirect=True
)
def test_format_porcelain(capsys, with_poetry_packages):
    cli.main(["-f", "porcelain", "-s", "tool.poetry.dependencies"])

    captured = capsys.readouterr()
    expected_log = "protobuf\npyyaml\n"

    assert captured.out == expected_log

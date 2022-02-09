import pytest

from creosote import cli


@pytest.mark.parametrize("with_packages", [["PyYAML", "protobuf"]], indirect=True)
def test_format_porcelain(capsys, with_packages):

    cli.main(["-f", "porcelain"])

    captured = capsys.readouterr()
    expected_log = "PyYAML\nprotobuf\n"

    assert captured.out == expected_log

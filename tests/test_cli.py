import pytest

from creosote import cli


@pytest.mark.parametrize(
    ["all_dep_names", "unused_dep_names", "exclude_deps", "want"],
    [
        pytest.param(
            ["requests", "yolo"],
            {"yolo"},
            ["yolo"],
            [],
            id="excluded dep is unused",
        ),
        pytest.param(
            ["requests", "yolo"],
            set(),
            ["yolo"],
            ["yolo"],
            id="excluded dep is imported",
        ),
        pytest.param(
            ["requests"],
            set(),
            ["yolo"],
            ["yolo"],
            id="excluded dep is not in dep spec",
        ),
        pytest.param(
            ["requests", "used", "unused"],
            {"unused"},
            ["used", "unused", "missing"],
            ["used", "missing"],
            id="mixed excludes",
        ),
        pytest.param(
            ["requests"],
            set(),
            [],
            [],
            id="no excludes",
        ),
    ],
)
def test_get_redundant_excludes(
    all_dep_names: list[str],
    unused_dep_names: set[str],
    exclude_deps: list[str],
    want: list[str],
) -> None:
    # act
    got = cli.get_redundant_excludes(
        all_dep_names=all_dep_names,
        unused_dep_names=unused_dep_names,
        exclude_deps=exclude_deps,
        deps_file="pyproject.toml",
    )

    # assert
    assert got == want

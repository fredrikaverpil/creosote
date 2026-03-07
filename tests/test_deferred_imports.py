from pathlib import Path

import pytest

from creosote.parsers import get_module_info_from_python_file


@pytest.fixture()
def python_file(tmp_path: Path) -> Path:
    """Create a Python file with both top-level and deferred imports."""
    content = (
        "import mod_a\n"
        "\n"
        "def foo():\n"
        "    import mod_b\n"
        "\n"
        "class Bar:\n"
        "    def baz(self):\n"
        "        from mod_c import something\n"
    )
    path = tmp_path / "example.py"
    _ = path.write_text(content)
    return path


def test_top_level_only(python_file: Path) -> None:
    """Without --include-deferred, only top-level imports are detected."""
    imports = list(get_module_info_from_python_file(str(python_file)))

    import_names = [i.name[0] for i in imports]
    assert import_names == ["mod_a"]


def test_include_deferred(python_file: Path) -> None:
    """With --include-deferred, all imports are detected."""
    imports = list(
        get_module_info_from_python_file(str(python_file), include_deferred=True)
    )

    import_names = [i.name[0] for i in imports]
    assert sorted(import_names) == ["mod_a", "mod_b", "something"]


def test_deferred_from_import(tmp_path: Path) -> None:
    """Deferred 'from X import Y' imports are detected."""
    content = "def foo():\n    from os.path import join\n"
    path = tmp_path / "example.py"
    _ = path.write_text(content)

    # Without flag: no imports detected
    imports = list(get_module_info_from_python_file(str(path)))
    assert imports == []

    # With flag: import detected
    imports = list(get_module_info_from_python_file(str(path), include_deferred=True))
    assert len(imports) == 1
    assert imports[0].module == ["os", "path"]
    assert imports[0].name == ["join"]


def test_nested_function_import(tmp_path: Path) -> None:
    """Imports nested multiple levels deep are detected."""
    content = "def outer():\n    def inner():\n        import deeply_nested\n"
    path = tmp_path / "example.py"
    _ = path.write_text(content)

    imports = list(get_module_info_from_python_file(str(path), include_deferred=True))
    assert len(imports) == 1
    assert imports[0].name == ["deeply_nested"]

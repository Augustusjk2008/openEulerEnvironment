from pathlib import PurePath

from build_helpers.pyinstaller_pywin32 import (
    collect_pywin32_binaries,
    find_pywin32_system32_dirs,
    relocate_collected_pywin32_binaries,
)


def test_find_pywin32_system32_dirs_returns_existing_unique_dirs(tmp_path):
    site_root = tmp_path / "site-packages"
    dll_dir = site_root / "pywin32_system32"
    dll_dir.mkdir(parents=True)

    result = find_pywin32_system32_dirs([site_root, site_root])

    assert result == [dll_dir]


def test_collect_pywin32_binaries_collects_only_dlls(tmp_path):
    site_root = tmp_path / "site-packages"
    dll_dir = site_root / "pywin32_system32"
    dll_dir.mkdir(parents=True)
    pythoncom = dll_dir / "pythoncom38.dll"
    pywintypes = dll_dir / "pywintypes38.dll"
    pythoncom.write_bytes(b"pythoncom")
    pywintypes.write_bytes(b"pywintypes")
    (dll_dir / "README.txt").write_text("ignore me", encoding="utf-8")

    result = collect_pywin32_binaries([site_root])

    assert result == [
        (str(pythoncom), "pywin32_compat"),
        (str(pywintypes), "pywin32_compat"),
    ]


def test_collect_pywin32_binaries_returns_empty_when_missing(tmp_path):
    result = collect_pywin32_binaries([tmp_path / "site-packages"])

    assert result == []


def test_relocate_collected_pywin32_binaries_moves_pywin32_system32_entries():
    binaries = [
        ("pywin32_system32/pythoncom38.dll", "src/pythoncom38.dll", "BINARY"),
        ("pywin32_system32/pywintypes38.dll", "src/pywintypes38.dll", "BINARY"),
        ("win32/win32api.pyd", "src/win32api.pyd", "EXTENSION"),
    ]

    result = relocate_collected_pywin32_binaries(binaries)

    assert [
        (PurePath(dest_name), src_name, typecode)
        for dest_name, src_name, typecode in result
    ] == [
        (PurePath("pywin32_compat/pythoncom38.dll"), "src/pythoncom38.dll", "BINARY"),
        (PurePath("pywin32_compat/pywintypes38.dll"), "src/pywintypes38.dll", "BINARY"),
        (PurePath("win32/win32api.pyd"), "src/win32api.pyd", "EXTENSION"),
    ]

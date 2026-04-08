import os
import sys

import pyimod04_pywin32 as compat


def _set_meipass(monkeypatch, tmp_path):
    monkeypatch.setattr(compat.sys, "path", list(sys.path))
    monkeypatch.setattr(compat.sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setenv("PATH", r"C:\Windows\System32")


def test_install_adds_pywin32_search_paths_without_add_dll_directory(monkeypatch, tmp_path):
    win32_dir = tmp_path / "win32"
    pythonwin_dir = tmp_path / "pythonwin"
    dll_dir = tmp_path / "pywin32_system32"
    win32_dir.mkdir()
    pythonwin_dir.mkdir()
    dll_dir.mkdir()
    _set_meipass(monkeypatch, tmp_path)
    monkeypatch.delattr(compat.os, "add_dll_directory", raising=False)

    compat.install()

    assert str(win32_dir) in compat.sys.path
    assert str(pythonwin_dir) in compat.sys.path
    assert str(dll_dir) in compat.sys.path
    assert compat.os.environ["PATH"].split(os.pathsep)[0] == str(dll_dir)


def test_install_falls_back_to_path_when_add_dll_directory_raises(monkeypatch, tmp_path):
    dll_dir = tmp_path / "pywin32_system32"
    dll_dir.mkdir()
    _set_meipass(monkeypatch, tmp_path)

    def _boom(_path):
        raise AttributeError("missing API")

    monkeypatch.setattr(compat.os, "add_dll_directory", _boom)

    compat.install()

    assert compat.os.environ["PATH"].split(os.pathsep)[0] == str(dll_dir)


def test_install_does_nothing_without_meipass(monkeypatch):
    monkeypatch.delattr(compat.sys, "_MEIPASS", raising=False)
    original_path = list(compat.sys.path)
    monkeypatch.setenv("PATH", r"C:\Windows\System32")

    compat.install()

    assert compat.sys.path == original_path
    assert compat.os.environ["PATH"] == r"C:\Windows\System32"

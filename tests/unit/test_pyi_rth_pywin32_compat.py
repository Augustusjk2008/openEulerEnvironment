import os
import sys

import build_helpers.pyi_rth_pywin32_compat as compat


def _set_meipass(monkeypatch, tmp_path):
    monkeypatch.setattr(compat.sys, "path", list(sys.path))
    monkeypatch.setattr(compat.sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setenv("PATH", r"C:\Windows\System32")
    monkeypatch.setattr(compat, "_dll_directory_handles", [])


def test_install_registers_pywin32_compat_dll_directory(monkeypatch, tmp_path):
    dll_dir = tmp_path / "pywin32_compat"
    dll_dir.mkdir()
    _set_meipass(monkeypatch, tmp_path)
    calls = []
    handle = object()

    def _add_dll_directory(path):
        calls.append(path)
        return handle

    monkeypatch.setattr(compat.os, "add_dll_directory", _add_dll_directory)

    compat.install()

    assert str(dll_dir) in compat.sys.path
    assert calls == [str(dll_dir)]
    assert compat._dll_directory_handles == [handle]
    assert compat.os.environ["PATH"].split(os.pathsep)[0] == str(dll_dir)


def test_install_falls_back_to_path_when_add_dll_directory_raises(monkeypatch, tmp_path):
    dll_dir = tmp_path / "pywin32_compat"
    dll_dir.mkdir()
    _set_meipass(monkeypatch, tmp_path)

    def _boom(_path):
        raise AttributeError("missing API")

    monkeypatch.setattr(compat.os, "add_dll_directory", _boom)

    compat.install()

    assert str(dll_dir) in compat.sys.path
    assert compat._dll_directory_handles == []
    assert compat.os.environ["PATH"].split(os.pathsep)[0] == str(dll_dir)

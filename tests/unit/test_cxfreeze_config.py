from pathlib import Path

from build_helpers.cxfreeze_config import (
    TARGET_NAME,
    get_build_dir,
    get_build_exe_options,
)


def test_get_build_dir_defaults_to_cxfreeze_dist(monkeypatch, tmp_path):
    monkeypatch.delenv("CXFREEZE_BUILD_DIR", raising=False)

    result = get_build_dir(tmp_path)

    assert result == tmp_path / "dist" / "openEulerManage_cxfreeze"


def test_get_build_dir_respects_environment_override(monkeypatch, tmp_path):
    override = tmp_path / "custom-build"
    monkeypatch.setenv("CXFREEZE_BUILD_DIR", str(override))

    result = get_build_dir(tmp_path)

    assert result == override


def test_get_build_exe_options_include_required_modules(monkeypatch, tmp_path):
    monkeypatch.delenv("CXFREEZE_BUILD_DIR", raising=False)

    options = get_build_exe_options(tmp_path)
    paths = [Path(p) for p in options["path"]]

    assert options["build_exe"] == str(tmp_path / "dist" / "openEulerManage_cxfreeze")
    assert "core" in options["packages"]
    assert "ui" in options["packages"]
    assert "qfluentwidgets" in options["packages"]
    assert "qframelesswindow" in options["packages"]
    assert "ui.interfaces.ftp_interface" in options["includes"]
    assert "ui.interfaces.protocol_editor_interface" in options["includes"]
    assert "matplotlib.backends.backend_qt5agg" in options["includes"]
    assert "qframelesswindow.windows.window_effect" in options["includes"]
    assert "win32api" in options["includes"]
    assert "win32comext.shell.shellcon" in options["includes"]
    assert options["include_msvcr"] is True
    assert options["zip_exclude_packages"] == ["*"]
    assert tmp_path in paths
    assert tmp_path / "src" in paths
    assert TARGET_NAME == "openEulerManage_cxfreeze.exe"

from pathlib import Path
import os


TARGET_NAME = "openEulerManage_cxfreeze.exe"

INTERFACE_MODULES = [
    "ui.interfaces.home_interface",
    "ui.interfaces.settings_interface",
    "ui.interfaces.initializer_interface",
    "ui.interfaces.environment_install_interface",
    "ui.interfaces.code_generation_interface",
    "ui.interfaces.tutorial_interface",
    "ui.interfaces.terminal_interface",
    "ui.interfaces.ftp_interface",
    "ui.interfaces.data_visualization_interface",
    "ui.interfaces.protocol_editor_interface",
    "ui.interfaces.autopilot_editor_interface",
]

QT_MODULES = [
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtSvg",
    "PyQt5.QtWidgets",
    "PyQt5.QtXml",
]

PYWIN32_MODULES = [
    "pythoncom",
    "pywintypes",
    "win32api",
    "win32con",
    "win32gui",
    "win32print",
    "win32com",
    "win32comext",
    "win32comext.shell",
    "win32comext.shell.shellcon",
]

THIRD_PARTY_MODULES = [
    "docx",
    "matplotlib.backends.backend_agg",
    "matplotlib.backends.backend_qt5agg",
    "pyte.graphics",
    "qframelesswindow.windows",
    "qframelesswindow.windows.window_effect",
    "qframelesswindow.utils.win32_utils",
    "wcwidth",
]

PACKAGES = [
    "core",
    "ui",
    "qfluentwidgets",
    "qframelesswindow",
    "paramiko",
    "pyte",
    "matplotlib",
    "docx",
]


def get_build_dir(root_dir):
    default_build_dir = Path(root_dir) / "dist" / "openEulerManage_cxfreeze"
    return Path(os.environ.get("CXFREEZE_BUILD_DIR", str(default_build_dir)))


def get_build_exe_options(root_dir):
    import sys
    root_dir = Path(root_dir)
    src_dir = root_dir / "src"

    includes = []
    for module_name in INTERFACE_MODULES + QT_MODULES + PYWIN32_MODULES + THIRD_PARTY_MODULES:
        if module_name not in includes:
            includes.append(module_name)

    packages = []
    for package_name in PACKAGES:
        if package_name not in packages:
            packages.append(package_name)

    return {
        "build_exe": str(get_build_dir(root_dir)),
        "packages": packages,
        "includes": includes,
        "excludes": ["tkinter", "test", "unittest"],
        "include_msvcr": True,
        "optimize": 0,
        "path": sys.path + [str(root_dir), str(src_dir)],
        "zip_include_packages": [],
        "zip_exclude_packages": ["*"],
        "silent_level": 1,
    }

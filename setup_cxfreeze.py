from pathlib import Path
import sys

from cx_Freeze import Executable, setup

from build_helpers.cxfreeze_config import TARGET_NAME, get_build_exe_options


ROOT_DIR = Path(__file__).resolve().parent

build_exe_options = get_build_exe_options(ROOT_DIR)

base = "Win32GUI" if sys.platform == "win32" else None

executables = [
    Executable(
        script=str(ROOT_DIR / "src" / "main.py"),
        base=base,
        target_name=TARGET_NAME,
    )
]

setup(
    name="openEulerManage_cxfreeze",
    version="0.0.7",
    description="RTopenEuler system management tool",
    options={"build_exe": build_exe_options},
    executables=executables,
)

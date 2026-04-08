import os
import sys


def _append_unique_sys_path(path):
    if path and os.path.isdir(path) and path not in sys.path:
        sys.path.append(path)


def _prepend_env_path(path):
    current = os.environ.get("PATH")
    if not current:
        os.environ["PATH"] = path
        return

    normalized = os.path.normcase(path)
    parts = current.split(os.pathsep)
    if any(os.path.normcase(part) == normalized for part in parts):
        return

    os.environ["PATH"] = path + os.pathsep + current


def _safe_add_dll_directory(path):
    add_dll_directory = getattr(os, "add_dll_directory", None)
    if add_dll_directory is None:
        return

    try:
        add_dll_directory(path)
    except Exception:
        # Win7 may lack the underlying AddDllDirectory API even if Python
        # exposes os.add_dll_directory.
        return


def install():
    base = getattr(sys, "_MEIPASS", None)
    if not base:
        return

    for subdir in ("win32", "pythonwin"):
        _append_unique_sys_path(os.path.join(base, subdir))

    pywin32_system32_path = os.path.join(base, "pywin32_system32")
    if not os.path.isdir(pywin32_system32_path):
        return

    _append_unique_sys_path(pywin32_system32_path)
    _safe_add_dll_directory(pywin32_system32_path)
    _prepend_env_path(pywin32_system32_path)

import os
import sys

_dll_directory_handles = []


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
        _dll_directory_handles.append(add_dll_directory(path))
    except Exception:
        return


def install():
    base = getattr(sys, "_MEIPASS", None)
    if not base:
        return

    pywin32_compat_path = os.path.join(base, "pywin32_compat")
    if os.path.isdir(pywin32_compat_path):
        if pywin32_compat_path not in sys.path:
            sys.path.append(pywin32_compat_path)
        _safe_add_dll_directory(pywin32_compat_path)
        _prepend_env_path(pywin32_compat_path)


install()

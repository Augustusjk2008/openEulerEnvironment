import os
import sys


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


base = getattr(sys, "_MEIPASS", None)
if base:
    pywin32_compat_path = os.path.join(base, "pywin32_compat")
    if os.path.isdir(pywin32_compat_path):
        if pywin32_compat_path not in sys.path:
            sys.path.append(pywin32_compat_path)
        _prepend_env_path(pywin32_compat_path)

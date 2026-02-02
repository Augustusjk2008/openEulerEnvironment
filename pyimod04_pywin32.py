import os
import sys


def _prepend_env_path(dir_path):
    current = os.environ.get("PATH", "")
    if not current:
        os.environ["PATH"] = dir_path
        return
    parts = current.split(";")
    if parts and parts[0].lower() == dir_path.lower():
        return
    if any(p.lower() == dir_path.lower() for p in parts):
        return
    os.environ["PATH"] = dir_path + ";" + current


def patch_pyinstaller_loader_for_win7():
    try:
        import PyInstaller.loader.pyimod04_pywin32 as pyi_mod
    except Exception:
        return False

    target = getattr(pyi_mod, "__file__", None)
    if not target or not os.path.isfile(target):
        return False

    try:
        with open(target, "r", encoding="utf-8") as f:
            src = f.read()
    except Exception:
        return False

    if "winerror" in src and "127" in src and "_prepend_env_path" in src:
        return True

    import re

    m = re.search(r"(?m)^(?P<indent>[ \t]*)os\\.add_dll_directory\\((?P<arg>[^\\)]+)\\)[ \t]*$", src)
    if not m:
        return False

    indent = m.group("indent")
    arg = m.group("arg").strip()

    replacement = (
        f"{indent}try:\\n"
        f"{indent}    os.add_dll_directory({arg})\\n"
        f"{indent}except OSError as e:\\n"
        f"{indent}    if getattr(e, 'winerror', None) != 127:\\n"
        f"{indent}        raise\\n"
        f"{indent}    _prepend_env_path({arg})"
    )

    src2 = src[: m.start()] + replacement + src[m.end() :]

    if "_prepend_env_path" not in src2:
        insert_at = 0
        m_import_end = re.search(r"(?ms)\\A(?:.*?\\n)(?:\\n)", src2)
        if m_import_end:
            insert_at = m_import_end.end()

        helper = (
            "def _prepend_env_path(dir_path):\n"
            "    current = os.environ.get('PATH', '')\n"
            "    if not current:\n"
            "        os.environ['PATH'] = dir_path\n"
            "        return\n"
            "    parts = current.split(';')\n"
            "    if parts and parts[0].lower() == dir_path.lower():\n"
            "        return\n"
            "    if any(p.lower() == dir_path.lower() for p in parts):\n"
            "        return\n"
            "    os.environ['PATH'] = dir_path + ';' + current\n"
            "\n\n"
        )
        src2 = src2[:insert_at] + helper + src2[insert_at:]

    try:
        with open(target, "w", encoding="utf-8") as f:
            f.write(src2)
        return True
    except Exception:
        return False


def install():
    base = getattr(sys, "_MEIPASS", None)
    if not base:
        return

    dll_dir = os.path.join(base, "pywin32_system32")
    if not os.path.isdir(dll_dir):
        return

    if dll_dir not in sys.path:
        sys.path.insert(0, dll_dir)

    try:
        os.add_dll_directory(dll_dir)
        return
    except OSError as e:
        if getattr(e, "winerror", None) != 127:
            raise

    _prepend_env_path(dll_dir)

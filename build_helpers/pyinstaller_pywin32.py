from pathlib import Path
import pathlib
import site
import sysconfig


def _iter_site_roots(search_roots=None):
    if search_roots is not None:
        for root in search_roots:
            yield Path(root)
        return

    seen = set()
    candidates = []

    try:
        candidates.extend(site.getsitepackages())
    except AttributeError:
        pass

    user_site = site.getusersitepackages()
    if user_site:
        candidates.append(user_site)

    for key in ("platlib", "purelib"):
        value = sysconfig.get_path(key)
        if value:
            candidates.append(value)

    for candidate in candidates:
        root = Path(candidate)
        normalized = str(root).lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        yield root


def find_pywin32_system32_dirs(search_roots=None):
    matches = []
    seen = set()

    for root in _iter_site_roots(search_roots):
        pywin32_dir = root / "pywin32_system32"
        normalized = str(pywin32_dir).lower()
        if normalized in seen or not pywin32_dir.is_dir():
            continue
        seen.add(normalized)
        matches.append(pywin32_dir)

    return matches


def collect_pywin32_binaries(search_roots=None, dest_dir="pywin32_compat"):
    binaries = []

    for pywin32_dir in find_pywin32_system32_dirs(search_roots):
        for dll_path in sorted(pywin32_dir.glob("*.dll")):
            binaries.append((str(dll_path), dest_dir))

    return binaries


def relocate_collected_pywin32_binaries(binaries, dest_dir="pywin32_compat"):
    relocated = []

    for entry in binaries:
        if len(entry) != 3:
            relocated.append(entry)
            continue

        dest_name, src_name, typecode = entry
        dest_path = pathlib.PurePath(dest_name)

        if dest_path.parts and dest_path.parts[0].lower() == "pywin32_system32":
            dest_name = str(pathlib.PurePath(dest_dir) / dest_path.name)

        relocated.append((dest_name, src_name, typecode))

    return relocated

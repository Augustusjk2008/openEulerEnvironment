# -*- mode: python ; coding: utf-8 -*-

from build_helpers.pyinstaller_pywin32 import (
    collect_pywin32_binaries,
    relocate_collected_pywin32_binaries,
)


pywin32_binaries = collect_pywin32_binaries()


a = Analysis(
    ['src\\main.py'],
    pathex=['src', '.'],
    binaries=pywin32_binaries,
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['build_helpers\\pyi_rth_pywin32_compat.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
a.binaries = relocate_collected_pywin32_binaries(a.binaries)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='openEulerManage',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='openEulerManage',
)

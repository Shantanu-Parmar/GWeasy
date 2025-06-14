# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
binaries = collect_data_files('msvcrt', include_py_files=True)

# Add the binaries (DLLs, etc.) explicitly if necessary
binaries += [
    ('C:/WINDOWS/system32/MSVCRT.dll', '.'),
    ('C:/Users/HP/miniconda3/envs/GWeasy/Lib/site-packages/framel.pyd', '.'),
    ('C:/Users/HP/miniconda3/envs/GWeasy/Library/bin/libframel.dll', '.')
]

a = Analysis(
    ['GWeasy.py'],
    pathex=[],
    binaries = binaries,
    datas = [('C:/Users/HP/miniconda3/envs/GWeasy/Lib/site-packages/Fr.py', '.')],
    hiddenimports = ['framel'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,

)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GWeasy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icon.ico'],

)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GWeasy',

)

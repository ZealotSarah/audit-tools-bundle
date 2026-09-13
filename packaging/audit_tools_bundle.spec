# -*- mode: python ; coding: utf-8 -*-

import os


project_root = os.path.abspath(os.path.join(SPECPATH, '..'))

a = Analysis(
    [os.path.join(project_root, 'run.py')],
    pathex=[project_root],
    binaries=[],
    datas=[(os.path.join(project_root, 'component-lock.json'), '.')],
    hiddenimports=[
        'audit_tools_bundle.tabs.medical_record',
        'audit_tools_bundle.tabs.fund_calculator',
        'audit_tools_bundle.tabs.file_renamer',
    ],
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
    [],
    exclude_binaries=True,
    name='飞检工具包',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='飞检工具包',
)

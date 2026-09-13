# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['manual_capture_studio.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('fonts', 'fonts'), ('config.json', '.'), ('version.json', '.'), ('AGENTS.md', '.'), ('RELEASE_NOTES.md', '.'), ('각 기능(키)설명.MD', '.')],
    hiddenimports=['i18n_manager', 'manual_cli', 'mcp_server', 'license_engine', 'updater_engine'],
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
    name='ManualStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/manual_studio.ico'],
)

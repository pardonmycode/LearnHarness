# PyInstaller one-folder build for Windows.
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("learnharness_client")

a = Analysis(
    ["src/learnharness_client/__main__.py"],
    pathex=["src", "../protocol/src"],
    binaries=[],
    datas=datas,
    hiddenimports=["PyQt6.QtWebSockets"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LearnHarness",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="LearnHarness",
)

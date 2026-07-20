# -*- mode: python -*-
# PyInstaller spec for the spatialmedia CLI (console).

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
# SPECPATH is the spatialmedia/ directory containing this spec file.
root = Path(SPECPATH).resolve().parent

a = Analysis(
    [str(root / "spatialmedia" / "__main__.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules("spatialmedia"),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="spatialmedia",
    debug=False,
    strip=False,
    upx=True,
    console=True,
)

# -*- mode: python -*-
# PyInstaller spec for the spatial-media console binary.

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
root = Path(SPECPATH).resolve().parent

a = Analysis(
    [str(root / "spatial" / "__main__.py")],
    pathex=[str(root.parent)],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules("spatial"),
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
    name="spatial-media",
    debug=False,
    strip=False,
    upx=True,
    console=True,
)

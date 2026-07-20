# -*- mode: python -*-
# PyInstaller spec for the SpatialTag desktop GUI.

import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH).resolve().parent

a = Analysis(
    [str(root / "spatial" / "gui.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe_kwargs = dict(
    name="SpatialTag",
    debug=False,
    strip=False,
    upx=True,
    console=False,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    **exe_kwargs,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="SpatialTag.app",
        icon=None,
        bundle_identifier=None,
        info_plist={"NSHighResolutionCapable": "True"},
    )

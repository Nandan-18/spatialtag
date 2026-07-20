<p align="center">
  <img src="web/assets/favicon.svg" alt="SpatialTag" width="96" height="96" />
</p>

<p align="center">
  <a href="https://github.com/Nandan-18/spatial-media/actions/workflows/ci.yml"><img src="https://github.com/Nandan-18/spatial-media/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://nandan-18.github.io/spatial-media/"><img src="https://img.shields.io/badge/docs-SpatialTag-0B7A75" alt="Docs" /></a>
  <a href="https://github.com/Nandan-18/spatial-media/releases/latest"><img src="https://img.shields.io/github/v/release/Nandan-18/spatial-media?label=release" alt="Release" /></a>
  <img src="https://img.shields.io/badge/python-%3E%3D3.12-blue" alt="Python &gt;= 3.12" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT" /></a>
</p>

# SpatialTag

inspect and inject immersive metadata

SpatialTag inspects and injects the MP4/MOV metadata that platforms need for
360°, VR180, and spatial audio.

Platforms like YouTube, Facebook, and VR headsets rely on special metadata
boxes inside MP4/MOV files to know that a video is spherical and how its audio
should be spatially rendered. This project lets you **inspect and inject**
that metadata so your immersive content plays back correctly everywhere.

## What it does

- **Reads** existing spherical-video (V1 XML and V2 `sv3d`/`st3d`) and
  spatial-audio (`SA3D`) metadata from any MP4/MOV file.
- **Writes** the correct MPEG-4 boxes so players recognise a file as 360°
  equirectangular, VR180 side-by-side, or ambisonics-enabled.
- Works as a **SpatialTag CLI** (`spatialtag`), a **desktop GUI**
  (Tkinter), a **browser demo**, or a **Docker web UI** (Flask).

**Site:**
[nandan-18.github.io/spatial-media](https://nandan-18.github.io/spatial-media/)
(browser demo, docs)

## Quick start

SpatialTag CLI command: `spatialtag`

```bash
git clone https://github.com/Nandan-18/spatial-media.git
cd spatial-media
python3 -m pip install -e .
spatialtag video.mp4              # inspect metadata
spatialtag -I --vr180 video.mp4   # inject in place
```

Pre-built [CLI binaries and HRIR
assets](https://github.com/Nandan-18/spatial-media/releases/latest)
are on GitHub Releases if you prefer not to install Python.

## Repository layout

| Path                 | Description                               |
| -------------------- | ----------------------------------------- |
| [web/](web/)         | Site source, browser demo, specifications |
| [spatial/](spatial/) | Core library, CLI, and desktop GUI        |
| [docker/](docker/)   | Flask web UI (Docker)                     |
| [audio/](audio/)     | HRIR reference assets for DAW monitoring  |
| [tests/](tests/)     | Unit tests and media fixtures             |
| [tools/](tools/)     | PyInstaller helper for the desktop GUI    |

## Development

```bash
python3 -m pip install -e ".[dev]"
python3 tests/test.py -v
python3 -m ruff check spatial tests/test.py docker
```

### Local site preview

```bash
cd web
pnpm install
pnpm dev
```

User-facing docs live in [web/guide/](web/guide/) and are published to the
site on push to `main`.

## License

[MIT](LICENSE)

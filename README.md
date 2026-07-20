# Spatial Media

Specifications and tools for **360° video** and **spatial audio** metadata in MP4/MOV files. This repository includes the original Google VR specifications, reference HRIR assets for ambisonic monitoring, and Python tools to inspect and inject metadata.

## What's in this repo

| Path | Description |
|------|-------------|
| [docs/](docs/) | RFCs, **browser demo** ([GitHub Pages](https://nandan-18.github.io/spatial-media/)), and specifications |
| [spatialmedia/](spatialmedia/) | Python CLI and desktop GUI for reading and injecting metadata |
| [docker/](docker/) | Browser-based metadata injector (Flask + Docker) |
| [spatial-audio/](spatial-audio/) | HRIR filters and ambisonic correction assets for binaural preview |

## Requirements

- **Python 3.9+** for the CLI and GUI
- **Docker** (optional) for the web UI

The core CLI uses only the Python standard library. Optional extras are declared in `pyproject.toml`.

## Install

From the repository root:

```bash
python3 -m pip install -e .
```

Optional dependency groups:

```bash
python3 -m pip install -e ".[gui]"    # desktop GUI (Pillow, packaging)
python3 -m pip install -e ".[build]"  # PyInstaller standalone build
python3 -m pip install -e ".[dev]"    # ruff, mypy (for development)
```

After install, the `spatialmedia` command is available on your PATH.

## Quick start (CLI)

```bash
# Help
spatialmedia -h

# Inspect metadata in one or more files
spatialmedia path/to/video.mp4

# Inject to a new file (v1 XML metadata)
spatialmedia -i --stereo=left-right input.mp4 output.mp4

# Inject with v2 box metadata
spatialmedia -i -2 --stereo=left-right input.mp4 output.mp4

# In-place inject (same path; no second full copy when layout allows)
spatialmedia -I --stereo=left-right video.mp4

# VR180 side-by-side helper (stereo + 180° crop/bounds from frame size)
spatialmedia -I --vr180 video.mp4
```

**In-place inject** works when rewriting the `moov` atom does not require moving `mdat` (typically `moov` after `mdat`). If the layout is incompatible, use separate input/output paths instead.

See [spatialmedia/README.md](spatialmedia/README.md) for all CLI flags, GUI usage, and PyInstaller builds.

## Browser demo (GitHub Pages)

**[Live demo →](https://nandan-18.github.io/spatial-media/)**: inspect and inject 360° / VR180 metadata in your browser, read the full specifications, and **download CLI binaries** (Linux + macOS). Best for browser use under ~2 GB; for multi‑GB sources use the CLI with `-I`.

Pages deploys from `docs/` via [.github/workflows/pages.yml](.github/workflows/pages.yml) (builds binaries + static docs on each push to `main`).

## Other interfaces

**Desktop GUI** (requires `[gui]` extra):

```bash
python3 -m spatialmedia.gui
```

**Docker web UI**: drag-and-drop in the browser; supports in-place inject for large files when you mount a host directory:

```bash
docker build -t spatial-media-web -f docker/Dockerfile .
docker run -p 5000:5000 -v "$(pwd)/data:/app/uploads" spatial-media-web
```

Open [http://localhost:5000](http://localhost:5000). Details: [docker/README.md](docker/README.md).

## Development

```bash
python3 -m pip install -e ".[dev]"
python3 spatialmedia_test.py -v
python3 -m ruff check spatialmedia spatialmedia_test.py docker
python3 -m ruff format --check spatialmedia spatialmedia_test.py docker
```

CI runs on Python 3.9 and 3.12 (see [.github/workflows/ci.yml](.github/workflows/ci.yml)).

## License

Apache License 2.0. This repository includes work originally published by Google Inc.

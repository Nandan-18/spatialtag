# Spatial Media

One toolkit for **immersive MP4/MOV metadata**: 360° and VR180 spherical video tags, plus first-order ambisonic spatial audio. Inspect and inject metadata without re-encoding media. Specifications, Python tools, a browser demo, and HRIR reference assets for ambisonic monitoring.

## What's in this repo

| Path | Description |
|------|-------------|
| [web/](web/) | Site source, **browser demo** ([GitHub Pages](https://nandan-18.github.io/spatial-media/)), and specifications |
| [cli/](cli/) | Core library, CLI, and desktop GUI for reading and injecting metadata |
| [docker/](docker/) | Browser-based metadata injector (Flask + Docker) |
| [audio/](audio/) | HRIR filters and ambisonic correction assets for binaural preview in a DAW (not inject code) |
| [tests/](tests/) | Unit tests and media fixtures |
| [tools/](tools/) | PyInstaller helper for the desktop GUI |

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

After install, the `cli` command is available on your PATH.

## Quick start (CLI)

```bash
# Help
cli -h

# Inspect metadata in one or more files
cli path/to/video.mp4

# Inject spherical video to a new file (v1 XML metadata)
cli -i --stereo=left-right input.mp4 output.mp4

# Inject with v2 box metadata
cli -i -2 --stereo=left-right input.mp4 output.mp4

# Inject spatial audio metadata (first-order ambiX ACN/SN3D)
cli -i -a input.mp4 output.mp4

# In-place inject (same path; no second full copy when layout allows)
cli -I --stereo=left-right video.mp4

# VR180 side-by-side helper (stereo + 180° crop/bounds from frame size)
cli -I --vr180 video.mp4
```

**In-place inject** works when rewriting the `moov` atom does not require moving `mdat` (typically `moov` after `mdat`). If the layout is incompatible, use separate input/output paths instead.

See [cli/README.md](cli/README.md) for all CLI flags, GUI usage, and PyInstaller builds.

## Choose your interface

All surfaces use the same `cli` library. Pick the one that fits your workflow:

| Interface | Best for |
|-----------|----------|
| **[Browser demo](https://nandan-18.github.io/spatial-media/)** | Quick inspect/inject under ~2 GB; no install required |
| **CLI** (`cli`) | Scripting, large files, in-place inject (`-I`), VR180 helper |
| **Desktop GUI** (`python3 -m cli.gui`) | Interactive desktop use with file pickers |
| **Docker web UI** | Drag-and-drop in a browser; mount a host folder for multi-GB files |

**Browser demo:** inspect and inject 360° / VR180 video and spatial audio metadata, read specifications, and download CLI binaries (Linux + macOS). Pages deploys from [web/](web/) via [.github/workflows/pages.yml](.github/workflows/pages.yml).

**Desktop GUI** (requires `[gui]` extra):

```bash
python3 -m cli.gui
```

**Docker web UI:**

```bash
docker build -t spatial-media-web -f docker/Dockerfile .
docker run -p 5000:5000 -v "$(pwd)/data:/app/uploads" spatial-media-web
```

Open [http://localhost:5000](http://localhost:5000). Details: [docker/README.md](docker/README.md).

## Spatial audio workflow

1. **Inject metadata** into your MP4 with the CLI (`-a`), GUI, Docker UI, or browser demo. This writes the `SA3D` atom so players know the track is first-order ambisonics (ACN/SN3D).
2. **Monitor mixes** using the HRIR reference assets in [audio/](audio/README.md) when previewing ambisonic audio in a DAW.

See the [Spatial Audio RFC](web/spec/audio.md) for the `SA3D` box specification.

## Development

```bash
python3 -m pip install -e ".[dev]"
python3 tests/test.py -v
python3 -m ruff check cli tests/test.py docker
python3 -m ruff format --check cli tests/test.py docker
```

### Local site preview

Preview the GitHub Pages site (landing page, docs, browser demo) with one command:

```bash
cd web
pnpm install   # or: npm install
pnpm dev       # builds web/dist, serves http://localhost:8888, rebuilds on save
```

Other scripts (from `web/`):

```bash
pnpm build       # build static site to web/dist only
pnpm preview     # serve web/dist (run build first)
pnpm test:demo   # browser inject smoke test
```

Requires **Node.js 18+** and **Python 3.9+** (for the site builder). Change the port with `PORT=3000 pnpm dev`.

CI runs on Python 3.12 (see [.github/workflows/ci.yml](.github/workflows/ci.yml)).


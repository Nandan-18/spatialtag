# Spatial Media

One toolkit for **immersive MP4/MOV metadata**: 360° and VR180 spherical video tags, plus first-order ambisonic spatial audio.

**Site:** [nandan-18.github.io/spatial-media](https://nandan-18.github.io/spatial-media/) (browser demo, docs)

## Quick start

```bash
git clone https://github.com/Nandan-18/spatial-media.git
cd spatial-media
python3 -m pip install -e .
cli video.mp4              # inspect metadata
cli -I --vr180 video.mp4   # inject in place
```

Pre-built [CLI binaries and HRIR assets](https://github.com/Nandan-18/spatial-media/releases/latest) are on GitHub Releases if you prefer not to install Python.

## Repository layout

| Path | Description |
|------|-------------|
| [web/](web/) | Site source, browser demo, specifications |
| [cli/](cli/) | Core library, CLI, and desktop GUI |
| [docker/](docker/) | Flask web UI (Docker) |
| [audio/](audio/) | HRIR reference assets for DAW monitoring |
| [tests/](tests/) | Unit tests and media fixtures |
| [tools/](tools/) | PyInstaller helper for the desktop GUI |

## Development

```bash
python3 -m pip install -e ".[dev]"
python3 tests/test.py -v
python3 -m ruff check cli tests/test.py docker
```

### Local site preview

```bash
cd web
pnpm install
pnpm dev
```

User-facing docs live in [web/guide/](web/guide/) and are published to the site on push to `main`.

### Publishing a release

Tag a version to build CLI binaries and `audio.zip`:

```bash
git tag v2.2.0
git push origin v2.2.0
```

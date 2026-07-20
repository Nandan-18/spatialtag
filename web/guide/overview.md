# Spatial Media

One toolkit for **immersive MP4/MOV metadata**: 360° and VR180 spherical video tags, plus first-order ambisonic spatial audio. Inspect and inject metadata without re-encoding media.

## Choose your interface

| Interface | Best for |
|-----------|----------|
| **[Browser demo](../index.html#demo)** | Quick inspect/inject under ~2 GB; no install |
| **[CLI binaries](../download.html)** | Scripting, large files, in-place inject (`-I`), VR180 helper |
| **[CLI guide](cli.html)** | All command-line flags and examples |
| **[Desktop GUI](cli.html#desktop-gui)** | Interactive desktop use with file pickers |
| **[Docker web UI](docker.html)** | Drag-and-drop in a browser with mounted folders |

## What you can do

- **Spherical video:** tag 360° equirectangular and VR180 side-by-side layouts (v1 XML and v2 `SV3D` / `ST3D` atoms).
- **Spatial audio:** tag first-order ambiX tracks with `SA3D` metadata (ACN channel order, SN3D normalization).
- **In-place inject:** rewrite metadata without a second full copy when the file layout allows (`moov` after `mdat`).
- **Specifications:** read the format RFCs for video, VR180, and spatial audio.
- **HRIR assets:** reference filters for ambisonic binaural monitoring in a DAW (listening only, not inject code).

## Specifications

| Topic | Document |
|-------|----------|
| Spherical video v1 | [RFC](../spec/v1.html) |
| Spherical video v2 | [RFC](../spec/v2.html) |
| VR180 | [Format](../spec/vr180.html) |
| Spatial audio | [RFC](../spec/audio.html) |

## Spatial audio workflow

1. **Inject metadata** with the [browser demo](../index.html#demo), [CLI](cli.html), [GUI](cli.html#desktop-gui), or [Docker UI](docker.html). This writes the `SA3D` atom so players know the track is first-order ambisonics.
2. **Monitor mixes** using the [HRIR reference assets](audio.html) when previewing ambisonic audio in a DAW.

## Requirements

- **Browser demo:** any modern desktop browser; files stay local.
- **CLI binaries:** Linux (x86_64) or macOS (Apple Silicon) from [GitHub Releases](../download.html).
- **Python install:** `git clone` and `pip install -e .`; see the [CLI guide](cli.html).
- **Docker UI:** [Docker](https://docs.docker.com/get-docker/) and a local `docker build`.

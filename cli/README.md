# Spatial Media Metadata Injector

Inspect and inject [spherical video](../web/spec/v1.md) and [spatial audio](../web/spec/audio.md) metadata into MP4 and MOV files.

Supports **v1** (XML in a UUID box) and **v2** (native `SV3D` / `ST3D` atoms). On inject, conflicting v1/v2 tags are cleared so players see a single coherent metadata set.

## Install

From the repository root:

```bash
python3 -m pip install -e .
# or, after install:
cli -h
```

## Examine

Print spatial media metadata for each file:

```bash
cli video.mp4
cli clip1.mp4 clip2.mov
```

## Inject

Write metadata to a **separate output file**:

```bash
cli -i [options] <input> <output>
```

Common examples:

```bash
# Mono 360 equirectangular (v1)
cli -i input.mp4 output.mp4

# Stereoscopic left-right (v1)
cli -i --stereo=left-right input.mp4 output.mp4

# v2 atom metadata
cli -i -2 --stereo=left-right input.mp4 output.mp4

# v2 with VR180 equirect bounds (fixed-point crop on each border)
cli -i -2 --stereo=left-right \
  --bounds="0:0:0x40000000:0x40000000" input.mp4 output.mp4

# v1 crop region (w:h:full_w:full_h:left:top)
cli -i --stereo=left-right \
  --crop="4096:4096:8192:4096:2048:0" input.mp4 output.mp4

# Spatial audio (first-order ambisonics, ACN + SN3D)
cli -i -a input.mp4 output.mp4
```

You can also pass the same path twice with `-i` to request in-place output when supported:

```bash
cli -i --stereo=left-right video.mp4 video.mp4
```

## In-place inject

Rewrite metadata **without a full second copy** of the media. Prefer `-I` for a single file:

```bash
cli -I --stereo=left-right video.mp4
```

**Requirements:** the file layout must allow updating `moov` without shifting `mdat` offsets. This is typical when **`moov` comes after `mdat`** (common for files optimized for streaming). If `moov` is before `mdat`, in-place inject is refused; use separate input and output paths.

## VR180 helper

For side-by-side equirectangular VR180, `--vr180` reads the video track dimensions and sets left-right stereo, v1 crop, and v2 180° bounds automatically:

```bash
cli -I --vr180 video.mp4
```

Example: an 8192×4096 SBS frame gets half-width eye crop and `0x40000000` (90°) bounds on left and right.

## CLI reference

### Modes

| Flag | Description |
|------|-------------|
| *(default)* | Print metadata for each file |
| `-i`, `--inject` | Write metadata to `<input>` → `<output>` |
| `-I`, `--in-place` | Inject into a single file in place |

### Spherical video

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `-2`, `--v2` | flag | off | Use v2 box metadata instead of v1 XML |
| `-s`, `--stereo` | `none`, `top-bottom`, `left-right` | `none` | Stereoscopic layout ([RFC](../web/spec/v1.md)) |
| `-p`, `--projection` | `none`, `equirectangular` | `equirectangular` | Projection type |
| `-c`, `--crop` | `w:h:f_w:f_h:x:y` | (none) | v1 crop region (six integers) |
| `-b`, `--bounds` | `top:bottom:left:right` | (none) | v2 equirect bounds (four 0.32 fixed-point values) |
| `--vr180` | flag | off | Derive VR180 stereo + crop/bounds from video size (implies v2 fields) |

### Spatial audio

| Flag | Description |
|------|-------------|
| `-a`, `--spatial-audio` | Inject spatial audio metadata. Input must contain a supported first-order ambisonics track (ACN channel order, SN3D normalization). See the [Spatial Audio RFC](../web/spec/audio.md). |

## Desktop GUI

Requires the `gui` extra:

```bash
python3 -m pip install -e ".[gui]"
python3 -m cli.gui
```

The GUI supports spherical video, stereoscopic modes (none / left-right / top-bottom), and spatial audio when the file has a compatible ambisonics track.

For large files or headless servers, use the [Docker web UI](../docker/) or the CLI with `-I`.

## Standalone executable

Install build dependencies and run PyInstaller:

```bash
python3 -m pip install -e ".[build]"
pyinstaller cli/gui.spec
```

The bundled app is built from `gui.py` (Tkinter). On Linux you may need `python3-tk` installed separately.

## Programmatic use

The injector is importable as a library:

```python
import cli.metadata as meta

meta.parse_metadata("video.mp4", print)
md = meta.Metadata("equirectangular", "left-right", None)
md.video = meta.generate_spherical_xml("equirectangular", "left-right")
meta.inject_metadata("input.mp4", "output.mp4", md, print)
```

Lower-level MP4 box helpers live under `cli.mpeg`.

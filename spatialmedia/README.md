# Spatial Media Metadata Injector

A tool for manipulating spatial media
([spherical video](../docs/spherical-video-rfc.md) and
[spatial audio](../docs/spatial-audio-rfc.md)) metadata in MP4 and MOV files.
It can be used to inject spatial media metadata into a file or validate metadata
in an existing file.

## Usage

**Python 3.9+** is required. From the repository root (or after `pip install -e .`):

#### Help

    python3 -m spatialmedia -h

Prints help and usage information.

#### Examine

    python3 -m spatialmedia <files...>

For each file specified, prints spatial media metadata contained in the file.

#### Inject

    python3 -m spatialmedia -i [--stereo=(none|top-bottom|left-right)] [--spatial-audio] <input> <output>

Saves a version of `<input>` injected with spatial media metadata to `<output>`.

#### In-place inject

Rewrite metadata without making a full second copy of the media. Requires a
layout where `mdat` offsets would not change (typically `moov` after `mdat`).

    python3 -m spatialmedia -I [--stereo=...] <file>

You can also pass the same path twice with `-i`:

    python3 -m spatialmedia -i [--stereo=...] <file> <file>

If the file layout would require moving `mdat` (for example `moov` before
`mdat`), in-place inject is refused and a separate output path must be used.

#### VR180 helper

For side-by-side equirectangular VR180, `--vr180` derives stereo mode and 180°
crop / v2 bounds from the video track dimensions:

    python3 -m spatialmedia -I --vr180 <file>

##### --stereo

Selects the left/right eye frame layout; see the `StereoMode` element in the
[Spherical Video RFC](../docs/spherical-video-rfc.md) for more information.

Options:

- `none`: Mono frame layout.

- `top-bottom`: Top half contains the left eye and bottom half contains the
right eye.

- `left-right`: Left half contains the left eye and right half contains the
right eye.

##### --spatial-audio

Enables injection of spatial audio metadata. If enabled, the file must contain a
4-channel first-order ambisonics audio track with ACN channel ordering and SN3D
normalization; see the [Spatial Audio RFC](../docs/spatial-audio-rfc.md) for
more information.

## GUI

    python3 -m spatialmedia.gui

Supports spherical + stereoscopic (left-right or top-bottom) and spatial audio.
For large files or headless use, prefer the [Docker web UI](../docker/).

## Building standalone GUI application

Install [PyInstaller](https://pyinstaller.org/), then run:

    pyinstaller spatialmedia/spatial_media_metadata_injector.spec

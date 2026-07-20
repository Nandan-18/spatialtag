# Spatial Media

A collection of specifications and tools for 360° video and spatial audio, including:

- [Spatial Audio](docs/spatial-audio-rfc.md) metadata specification
- [Spherical Video](docs/spherical-video-rfc.md) metadata specification
- [Spherical Video V2](docs/spherical-video-v2-rfc.md) metadata specification
- [VR180 Video Format](docs/vr180.md) VR180 video format
- [Spatial Media tools](spatialmedia/) for injecting spatial media metadata in media files
- [Docker web UI](docker/) for browser-based metadata injection

## Quick start (CLI)

Requires **Python 3.9+**.

```bash
python3 -m pip install -e .
python3 -m spatialmedia -h

# Inspect metadata
python3 -m spatialmedia path/to/video.mp4

# Inject (separate output path)
python3 -m spatialmedia -i --stereo=left-right input.mp4 output.mp4

# In-place inject (same path; requires moov after mdat)
python3 -m spatialmedia -I --stereo=left-right video.mp4

# VR180 SBS helper (sets stereo + 180° crop/bounds from frame size)
python3 -m spatialmedia -I --vr180 video.mp4
```

See [spatialmedia/README.md](spatialmedia/README.md) for full options.

## License

Apache License 2.0. This repository includes work originally published by Google Inc.

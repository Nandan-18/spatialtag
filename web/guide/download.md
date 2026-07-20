# Download

Pre-built assets are published on [GitHub
Releases](https://github.com/Nandan-18/spatial-media/releases/latest).

| File | Description |
|------|-------------|
| `spatialtag-linux-x86_64` | Linux CLI (x86_64) |
| `spatialtag-macos-arm64` | macOS CLI (Apple Silicon) |
| `audio.zip` | HRIR reference WAV files |

## CLI usage

```bash
chmod +x spatialtag-macos-arm64   # macOS or Linux
./spatialtag-macos-arm64 -h
./spatialtag-macos-arm64 -I --vr180 /path/to/video.mp4
```

On macOS you may need: `xattr -dr com.apple.quarantine
./spatialtag-macos-arm64`

See the [CLI guide](cli.html) for all options.

## Install from source

```bash
git clone https://github.com/Nandan-18/spatial-media.git
cd spatial-media
python3 -m pip install -e .
spatialtag -h
```

## HRIR assets

Extract `audio.zip` or clone the repository and use the files under `audio/`.
See the [spatial audio resources guide](audio.html).

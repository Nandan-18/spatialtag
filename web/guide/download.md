# Download

Pre-built assets are published on [GitHub Releases](https://github.com/Nandan-18/spatial-media/releases/latest).

| File | Description |
|------|-------------|
| `cli-linux-x86_64` | Linux CLI (x86_64) |
| `cli-macos-arm64` | macOS CLI (Apple Silicon) |
| `audio.zip` | HRIR reference WAV files |

## CLI usage

```bash
chmod +x cli-macos-arm64   # macOS or Linux
./cli-macos-arm64 -h
./cli-macos-arm64 -I --vr180 /path/to/video.mp4
```

On macOS you may need: `xattr -dr com.apple.quarantine ./cli-macos-arm64`

See the [CLI guide](guide/cli.html) for all options.

## Install from source

```bash
git clone https://github.com/Nandan-18/spatial-media.git
cd spatial-media
python3 -m pip install -e .
cli -h
```

## HRIR assets

Extract `audio.zip` or clone the repository and use the files under `audio/`. See the [spatial audio resources guide](guide/audio.html).

# Docker Web UI

Browser-based metadata injection for MP4/MOV files, running in Docker. Uses the same `cli` library as the command-line tool and desktop GUI.

## Features

- **Web interface:** drag-and-drop upload, progress indicator, download links
- **Stereoscopic modes:** none, left-right, or top-bottom
- **In-place inject:** rewrite metadata in the uploaded file when the layout supports it (default on; avoids a second full copy on disk)
- **Spatial audio:** inject ambisonics metadata when the source track is compatible
- **Large files:** up to 16 GB per upload; mount a host directory to process files without uploading through the browser
- **Headless:** no X11 or Tkinter in the container

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)

For quick one-off tagging without Docker, use the [browser demo](../index.html#demo) or [download a CLI binary](../download.html).

## Build and run

```bash
git clone https://github.com/Nandan-18/spatial-media.git
cd spatial-media
docker build -t spatial-media-web -f docker/Dockerfile .
mkdir -p data
docker run -p 5000:5000 \
  --name spatial-media-metadata-injector \
  -v "$(pwd)/data:/app/uploads" \
  spatial-media-web
```

Open [http://localhost:5000](http://localhost:5000).

**PowerShell** (volume mount):

```powershell
mkdir data -ErrorAction SilentlyContinue
docker run -p 5000:5000 `
  --name spatial-media-metadata-injector `
  -v ${PWD}\data:/app/uploads `
  spatial-media-web
```

### Working with very large files

For multi-GB sources, skip the browser upload and bind-mount the directory that already contains your videos:

```bash
docker run -p 5000:5000 \
  -v /path/to/your/videos:/app/uploads \
  spatial-media-web
```

Copy or move files into that folder, then use the web UI to inject (with **Inject in place** enabled). Alternatively, use a [CLI binary](../download.html) on the host:

```bash
cli -I --vr180 /path/to/your/videos/file.mp4
```

## Usage

1. Drag and drop `.mp4` or `.mov` files (or click to browse).
2. Choose options:
   - **Spherical (360):** equirectangular video metadata
   - **Stereo mode:** none, left-right, or top-bottom
   - **Inject in place:** overwrite the uploaded file when supported (recommended for large files on a mounted volume)
   - **Spatial audio:** ambisonics metadata (requires a compatible track)
3. Click **Inject Metadata**.
4. Download results from the page, or read them from your mounted `data/` (or custom) folder.

## Troubleshooting

### "File not found" or missing output

Ensure the volume mount is set: `-v ...:/app/uploads`. All uploads and in-place writes go to that path inside the container.

### Container name already in use

```bash
docker rm -f spatial-media-metadata-injector
```

### In-place inject failed

Some files have `moov` before `mdat`; those cannot be updated in place. Disable **Inject in place** in the UI (creates `injected_<filename>`) or use the CLI with separate input/output paths.

## Security notes

- Filenames are sanitized and path traversal (`..`, `/`) is rejected.
- Do not expose this service on a public network without authentication; it accepts file uploads and writes to disk.
- Intended for local or trusted LAN use.

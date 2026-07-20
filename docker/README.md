# Spatial Media Metadata Injector — Web UI

Browser-based metadata injection for MP4/MOV files, running in Docker. Uses the same `spatialmedia` library as the CLI and desktop GUI, wrapped in a small Flask app.

## Features

- **Web interface** — drag-and-drop upload, progress indicator, download links
- **Stereoscopic modes** — none, left-right, or top-bottom
- **In-place inject** — rewrite metadata in the uploaded file when the layout supports it (default on; avoids a second full copy on disk)
- **Spatial audio** — inject ambisonics metadata when the source track is compatible
- **Large files** — up to 16 GB per upload; mount a host directory to process files without uploading through the browser
- **Headless** — no X11 or Tkinter in the container

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)

## Build

Run from the **repository root** (build context must include `spatialmedia/`):

```bash
docker build -t spatial-media-web -f docker/Dockerfile .
```

## Run

Create a local folder for uploads/processed files, then start the container:

**macOS / Linux:**

```bash
mkdir -p data
docker run -p 5000:5000 \
  --name spatial-media-metadata-injector \
  -v "$(pwd)/data:/app/uploads" \
  spatial-media-web
```

**PowerShell:**

```powershell
mkdir data -ErrorAction SilentlyContinue
docker run -p 5000:5000 `
  --name spatial-media-metadata-injector `
  -v ${PWD}\data:/app/uploads `
  spatial-media-web
```

Open [http://localhost:5000](http://localhost:5000).

### Working with very large files

For multi‑GB sources, skip the browser upload and bind-mount the directory that already contains your videos:

```bash
docker run -p 5000:5000 \
  -v /path/to/your/videos:/app/uploads \
  spatial-media-web
```

Copy or move files into that folder, then use the web UI to inject (with **Inject in place** enabled). Alternatively, run the CLI on the host for maximum control:

```bash
spatialmedia -I --vr180 /path/to/your/videos/file.mp4
```

## Usage

1. Drag and drop `.mp4` or `.mov` files (or click to browse).
2. Choose options:
   - **Spherical (360)** — equirectangular video metadata
   - **Stereo mode** — none, left-right, or top-bottom
   - **Inject in place** — overwrite the uploaded file when supported (recommended for large files on a mounted volume)
   - **Spatial audio** — ambisonics metadata (requires a compatible track)
3. Click **Inject Metadata**.
4. Download results from the page, or read them from your mounted `data/` (or custom) folder.

## Troubleshooting

### "File not found" or missing output

Ensure the volume mount is set: `-v ...:/app/uploads`. All uploads and in-place writes go to that path inside the container.

### Container name already in use

Remove the old container and run again:

```bash
docker rm -f spatial-media-metadata-injector
```

### In-place inject failed

Some files have `moov` before `mdat`; those cannot be updated in place. Disable **Inject in place** in the UI (creates `injected_<filename>`) or use the CLI with separate input/output paths.

## Local development (without Docker)

From the repository root:

```bash
python3 -m pip install -r docker/requirements.txt
export UPLOAD_FOLDER="$(pwd)/data"
mkdir -p "$UPLOAD_FOLDER"
python3 docker/app.py
```

The app listens on `http://127.0.0.1:5000` with Flask debug mode enabled.

## Security notes

- Filenames are sanitized and path traversal (`..`, `/`) is rejected.
- Do not expose this service on a public network without authentication; it accepts file uploads and writes to disk.
- Intended for local or trusted LAN use.

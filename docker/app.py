import os
import sys
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

try:
    import spatial.metadata as meta
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    import spatial.metadata as meta

ALLOWED_EXTENSIONS = {".mp4", ".mov"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "/app/uploads")
# Soft cap for the Docker UI; use the CLI for larger files.
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_BYTES", 4 * 1024 * 1024 * 1024))

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


class Console:
    def __init__(self):
        self.log = []

    def append(self, text):
        self.log.append(text)

    def __call__(self, text):
        self.append(text)


def _allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def _safe_join(folder: str, filename: str) -> str | None:
    secure_name = secure_filename(filename)
    if not secure_name or not _allowed_file(secure_name):
        return None
    path = os.path.abspath(os.path.join(folder, secure_name))
    root = os.path.abspath(folder)
    if not path.startswith(root + os.sep) and path != root:
        return None
    return path


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_files():
    if "files[]" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files[]")
    uploaded_files = []
    batch_id = uuid.uuid4().hex
    batch_dir = os.path.join(app.config["UPLOAD_FOLDER"], batch_id)
    os.makedirs(batch_dir, mode=0o750, exist_ok=True)

    for file in files:
        if not file.filename:
            continue

        normalized_filename = file.filename.replace("\\", "/")
        if "/" in normalized_filename or ".." in normalized_filename:
            return jsonify({"error": f"Invalid filename detected: {file.filename}"}), 400

        if not _allowed_file(file.filename):
            return jsonify({"error": f"Unsupported file type: {file.filename}"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(batch_dir, filename)
        file.save(filepath)

        uploaded_files.append(
            {
                "filename": f"{batch_id}/{filename}",
                "spherical": False,
                "stereo": "none",
                "audio": False,
                "audio_desc": "Unknown",
            }
        )

    return jsonify({"files": uploaded_files})


@app.route("/inject", methods=["POST"])
def inject_metadata():
    data = request.json or {}
    files_to_process = data.get("files", [])
    options = data.get("options", {})

    if not files_to_process:
        return jsonify({"error": "No files specified"}), 400

    stereo_mode = options.get("stereo_mode") or "none"
    if stereo_mode not in ("none", "left-right", "top-bottom"):
        stereo_mode = "none"
    if stereo_mode == "none":
        stereo_mode = None

    results = []
    use_inplace = bool(options.get("inplace", True))

    for raw_filename in files_to_process:
        normalized_filename = raw_filename.replace("\\", "/")
        parts = Path(normalized_filename).parts
        if ".." in parts or len(parts) != 2:
            results.append(
                {
                    "filename": raw_filename,
                    "error": "Invalid filename detected",
                    "logs": ["Rejected due to unsafe filename path."],
                    "success": False,
                }
            )
            continue

        batch_id, filename = parts
        batch_dir = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(batch_id))
        input_path = _safe_join(batch_dir, filename)
        if not input_path or not os.path.isfile(input_path):
            results.append(
                {
                    "filename": raw_filename,
                    "error": "File not found",
                    "logs": ["Upload missing or rejected."],
                    "success": False,
                }
            )
            continue

        if use_inplace:
            output_filename = filename
            output_path = input_path
        else:
            output_filename = f"injected_{filename}"
            output_path = os.path.join(batch_dir, output_filename)

        # Fresh metadata per file so audio flags do not leak across the batch.
        metadata = meta.Metadata()
        if options.get("spherical"):
            metadata.video = meta.generate_spherical_xml(stereo=stereo_mode)

        console = Console()
        try:
            if options.get("spatial_audio"):
                parsed = meta.parse_metadata(input_path, lambda _x: None)
                if parsed and parsed.num_audio_channels:
                    desc = meta.get_spatial_audio_description(parsed.num_audio_channels)
                    if desc.is_supported:
                        metadata.audio = meta.get_spatial_audio_metadata(
                            desc.order, desc.has_head_locked_stereo
                        )

            meta.inject_metadata(input_path, output_path, metadata, console.append)
            results.append(
                {
                    "filename": raw_filename,
                    "output_url": f"/download/{batch_id}/{output_filename}",
                    "logs": console.log,
                    "success": True,
                }
            )
        except Exception as e:
            results.append(
                {
                    "filename": raw_filename,
                    "error": str(e),
                    "logs": console.log,
                    "success": False,
                }
            )

    return jsonify({"results": results})


@app.route("/download/<batch_id>/<path:filename>")
def download_file(batch_id, filename):
    batch_dir = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(batch_id))
    path = _safe_join(batch_dir, filename)
    if not path or not os.path.isfile(path):
        return "Invalid file path", 400
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    # Local development only — production uses gunicorn via startup.sh.
    app.run(host="127.0.0.1", port=5000, debug=False)

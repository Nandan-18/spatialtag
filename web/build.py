"""Build the GitHub Pages site: markdown docs, download page, static assets."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension

ROOT = Path(__file__).resolve().parent.parent
WEB = Path(__file__).resolve().parent
DEFAULT_OUT = WEB / "dist"

# (source path relative to ROOT, output path relative to site root, page title)
DOC_PAGES: list[tuple[str, str, str]] = [
    ("README.md", "guide/overview.html", "Overview"),
    ("cli/README.md", "guide/cli.html", "CLI Guide"),
    ("docker/README.md", "guide/docker.html", "Docker Web UI"),
    ("audio/README.md", "guide/audio.html", "Spatial Audio Resources"),
    ("web/spec/audio.md", "spec/audio.html", "Spatial Audio RFC"),
    ("web/spec/v1.md", "spec/v1.html", "Spherical Video v1 RFC"),
    ("web/spec/v2.md", "spec/v2.html", "Spherical Video v2 RFC"),
    ("web/spec/vr180.md", "spec/vr180.html", "VR180 Format"),
]

LINK_REWRITES: dict[str, str] = {
    "audio.md": "spec/audio.html",
    "v1.md": "spec/v1.html",
    "v2.md": "spec/v2.html",
    "vr180.md": "spec/vr180.html",
    "../web/spec/audio.md": "spec/audio.html",
    "../web/spec/v1.md": "spec/v1.html",
    "../web/spec/v2.md": "spec/v2.html",
    "../web/spec/vr180.md": "spec/vr180.html",
    "cli/README.md": "guide/cli.html",
    "../cli/README.md": "guide/cli.html",
    "docker/README.md": "guide/docker.html",
    "../docker/README.md": "guide/docker.html",
    "audio/README.md": "guide/audio.html",
    "../audio/README.md": "guide/audio.html",
    "README.md": "guide/overview.html",
}

NAV_ITEMS = [
    ("Demo", "index.html"),
    ("Download", "download.html"),
    ("Overview", "guide/overview.html"),
    ("CLI Guide", "guide/cli.html"),
    ("Docker", "guide/docker.html"),
    ("Spatial Audio", "guide/audio.html"),
    ("Specifications", None),
    ("Spatial Audio RFC", "spec/audio.html"),
    ("Spherical v1", "spec/v1.html"),
    ("Spherical v2", "spec/v2.html"),
    ("VR180", "spec/vr180.html"),
]

# Shared global nav (keep in sync with web/index.html)
GLOBAL_NAV_GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "",
        [
            ("Demo", "index.html#demo"),
            ("Download", "download.html"),
        ],
    ),
    (
        "Guides",
        [
            ("Overview", "guide/overview.html"),
            ("CLI", "guide/cli.html"),
            ("Docker", "guide/docker.html"),
            ("GUI", "guide/cli.html#desktop-gui"),
        ],
    ),
    (
        "Specs",
        [
            ("Spherical v1", "spec/v1.html"),
            ("Spherical v2", "spec/v2.html"),
            ("VR180", "spec/vr180.html"),
            ("Spatial audio", "spec/audio.html"),
        ],
    ),
    (
        "Resources",
        [
            ("HRIR assets", "guide/audio.html"),
        ],
    ),
]


def nav_href(current_page: str, target: str) -> str:
    if "#" in target:
        path, anchor = target.split("#", 1)
        if path == "index.html":
            if current_page == "index.html":
                return f"#{anchor}"
            return f"{relpath(current_page, 'index.html')}#{anchor}"
        return f"{relpath(current_page, path)}#{anchor}"
    if target == "index.html":
        return relpath(current_page, "index.html")
    return relpath(current_page, target)


def render_global_nav(current_page: str) -> str:
    logo_href = html.escape(nav_href(current_page, "index.html"))
    groups: list[str] = []
    for label, links in GLOBAL_NAV_GROUPS:
        link_html = "".join(
            f'<a href="{html.escape(nav_href(current_page, href))}">{html.escape(text)}</a>'
            for text, href in links
        )
        if label:
            groups.append(
                f'<div class="nav-group"><span class="nav-group-label">{html.escape(label)}</span>'
                f'<div class="nav-sublinks">{link_html}</div></div>'
            )
        else:
            groups.append(f'<div class="nav-group nav-group-primary">{link_html}</div>')
    return (
        f'<nav class="global-nav" aria-label="Global">\n'
        f'  <div class="nav-inner">\n'
        f'    <a class="nav-logo" href="{logo_href}">Spatial Media</a>\n'
        f'    <div class="nav-links">{"".join(groups)}</div>\n'
        f"  </div>\n"
        f"</nav>"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def relpath(from_page: str, to_page: str) -> str:
    from_dir = Path(from_page).parent
    target = Path(to_page)
    rel = Path(os_path_relpath(from_dir, target))
    return rel.as_posix()


def os_path_relpath(from_dir: Path, target: Path) -> str:
    import os

    return os.path.relpath(target, start=from_dir if str(from_dir) != "." else ".")


def rewrite_links(md_text: str) -> str:
    for old, new in LINK_REWRITES.items():
        md_text = md_text.replace(f"]({old})", f"]({new})")
        md_text = md_text.replace(f"]({old}#", f"]({new}#")
    # Drop links to private GitHub repo paths that won't resolve on Pages.
    md_text = re.sub(
        r"\[([^\]]+)\]\(https://github\.com/[^)]+\)",
        r"\1",
        md_text,
    )
    return md_text


def render_nav(current_page: str) -> str:
    lines = ['<nav class="site-nav" aria-label="Site">', '<a class="site-logo" href="INDEX">Spatial Media</a>', "<div>"]
    index_href = relpath(current_page, "index.html")
    for label, href in NAV_ITEMS:
        if href is None:
            lines.append(f'<span class="nav-section">{html.escape(label)}</span>')
            continue
        url = relpath(current_page, href) if href != "index.html" else index_href
        active = " active" if href == current_page or (href == "index.html" and current_page == "index.html") else ""
        lines.append(f'<a href="{html.escape(url)}" class="nav-link{active}">{html.escape(label)}</a>')
    lines.append("</div></nav>")
    return "\n".join(lines).replace("INDEX", html.escape(index_href))


def render_favicon_links(current_page: str) -> str:
    icon_href = html.escape(relpath(current_page, "assets/favicon.svg"))
    return (
        f'<link rel="icon" href="{icon_href}" type="image/svg+xml" />\n'
        f'  <link rel="apple-touch-icon" href="{icon_href}" />'
    )


def render_doc_page(title: str, body_html: str, current_page: str) -> str:
    nav = render_nav(current_page)
    global_nav = render_global_nav(current_page)
    style_href = relpath(current_page, "assets/css/style.css")
    site_href = relpath(current_page, "assets/css/site.css")
    favicon = render_favicon_links(current_page)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(title)} · Spatial Media</title>
  {favicon}
  <link rel="stylesheet" href="{html.escape(style_href)}" />
  <link rel="stylesheet" href="{html.escape(site_href)}" />
</head>
<body class="doc-page">
  {global_nav}
  <div class="page doc-shell">
    <main class="doc-content">
      <h1>{html.escape(title)}</h1>
      {body_html}
    </main>
    <footer class="doc-footer">
      <p>Spatial Media metadata tools</p>
    </footer>
  </div>
</body>
</html>
"""


def render_download_page(downloads: list[dict], current_page: str = "download.html") -> str:
    cards = []
    for item in downloads:
        href = relpath(current_page, item["path"])
        cards.append(
            f"""<article class="download-card">
  <h2>{html.escape(item["label"])}</h2>
  <p class="download-meta">{html.escape(item.get("arch", ""))} · {format_bytes(item["size"])}</p>
  <p class="download-note">{html.escape(item.get("note", ""))}</p>
  <a class="button button-primary download-btn" href="{html.escape(href)}" download>Download {html.escape(item["filename"])}</a>
  <p class="sha">SHA-256: {html.escape(item["sha256"])}</p>
</article>"""
        )

    cli_href = html.escape(relpath(current_page, "guide/cli.html"))
    usage_code = highlight_code(
        "chmod +x cli-macos-arm64   # macOS / Linux\n"
        "./cli-macos-arm64 -h\n"
        "./cli-macos-arm64 -I --vr180 /path/to/video.mp4\n",
        "bash",
    )
    body = f"""
<p class="lede">Standalone CLI binaries built on every deploy. No Python install required: download, make executable, and run from a terminal.</p>
<div class="download-grid">{"".join(cards) if cards else "<p>No binaries bundled yet.</p>"}</div>
<section class="doc-section">
  <h2>Usage</h2>
  {usage_code}
  <p>See the <a href="{cli_href}">CLI guide</a> for all options including in-place inject for large files.</p>
</section>
"""
    return render_doc_page("Download CLI", body, current_page)


def highlight_code(source: str, language: str) -> str:
    """Highlight a code snippet with Pygments for static HTML pages."""
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name, TextLexer

    try:
        lexer = get_lexer_by_name(language, stripall=False)
    except Exception:
        lexer = TextLexer()
    formatter = HtmlFormatter(cssclass="highlight", nowrap=False)
    return highlight(source, lexer, formatter)


def md_to_html(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=[
            TableExtension(),
            FencedCodeExtension(),
            CodeHiliteExtension(
                css_class="highlight",
                guess_lang=False,
                linenums=False,
                pygments_formatter="html",
            ),
        ],
        output_format="html5",
    )


def load_manifest(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("downloads", [])


def build_site(output_dir: Path, manifest_path: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # Static assets + demo
    shutil.copytree(WEB / "assets", output_dir / "assets")
    shutil.copy2(WEB / "index.html", output_dir / "index.html")
    if (WEB / "img").is_dir():
        shutil.copytree(WEB / "img", output_dir / "img")

    # Markdown docs
    for src_rel, out_rel, title in DOC_PAGES:
        src = ROOT / src_rel
        text = rewrite_links(src.read_text(encoding="utf-8"))
        body = md_to_html(text)
        page_html = render_doc_page(title, body, out_rel)
        out_path = output_dir / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(page_html, encoding="utf-8")

    # Downloads
    downloads_dir = output_dir / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    manifest_downloads = load_manifest(manifest_path)
    bundled: list[dict] = []

    for entry in manifest_downloads:
        src = Path(entry["source"])
        if not src.is_file():
            continue
        dest_name = entry["filename"]
        dest = downloads_dir / dest_name
        shutil.copy2(src, dest)
        bundled.append(
            {
                "label": entry["label"],
                "arch": entry.get("arch", ""),
                "note": entry.get("note", ""),
                "filename": dest_name,
                "path": f"downloads/{dest_name}",
                "size": dest.stat().st_size,
                "sha256": sha256_file(dest),
            }
        )

    (output_dir / "download.html").write_text(
        render_download_page(bundled),
        encoding="utf-8",
    )

    print(f"Built site at {output_dir} ({len(bundled)} download(s))")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build GitHub Pages site")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=WEB / "manifest.json",
        help="JSON manifest listing built CLI binaries",
    )
    args = parser.parse_args()
    build_site(args.output, args.manifest)


if __name__ == "__main__":
    main()

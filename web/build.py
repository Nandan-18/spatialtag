"""Build the GitHub Pages site: markdown docs and static assets."""

from __future__ import annotations

import argparse
import html
import os
import shutil
from pathlib import Path

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension

ROOT = Path(__file__).resolve().parent.parent
WEB = Path(__file__).resolve().parent
DEFAULT_OUT = WEB / "dist"

DOC_PAGES: list[tuple[str, str, str]] = [
    ("web/guide/overview.md", "guide/overview.html", "Overview"),
    ("web/guide/download.md", "download.html", "Download"),
    ("web/guide/cli.md", "guide/cli.html", "CLI Guide"),
    ("web/guide/docker.md", "guide/docker.html", "Docker Web UI"),
    ("web/guide/audio.md", "guide/audio.html", "Spatial Audio Resources"),
    ("web/spec/audio.md", "spec/audio.html", "Spatial Audio RFC"),
    ("web/spec/v1.md", "spec/v1.html", "Spherical Video v1 RFC"),
    ("web/spec/v2.md", "spec/v2.html", "Spherical Video v2 RFC"),
    ("web/spec/vr180.md", "spec/vr180.html", "VR180 Format"),
]

# None = visual divider. Keep in sync with web/index.html.
GLOBAL_NAV_LINKS: list[tuple[str, str] | None] = [
    ("Demo", "index.html#demo"),
    ("Download", "download.html"),
    None,
    ("Overview", "guide/overview.html"),
    ("CLI", "guide/cli.html"),
    ("Docker", "guide/docker.html"),
    ("GUI", "guide/cli.html#desktop-gui"),
    None,
    ("Spherical v1", "spec/v1.html"),
    ("Spherical v2", "spec/v2.html"),
    ("VR180", "spec/vr180.html"),
    ("Spatial audio", "spec/audio.html"),
    None,
    ("HRIR", "guide/audio.html"),
]


def relpath(from_page: str, to_page: str) -> str:
    from_dir = Path(from_page).parent
    target = Path(to_page)
    rel = os.path.relpath(target, start=from_dir if str(from_dir) != "." else ".")
    return Path(rel).as_posix()


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
    items: list[str] = []
    for entry in GLOBAL_NAV_LINKS:
        if entry is None:
            items.append('<span class="nav-divider" aria-hidden="true"></span>')
            continue
        text, href = entry
        items.append(
            f'<a href="{html.escape(nav_href(current_page, href))}">{html.escape(text)}</a>'
        )
    links_html = "".join(items)
    return (
        f'<nav class="global-nav" aria-label="Global">\n'
        f'  <div class="nav-inner">\n'
        f'    <a class="nav-logo" href="{logo_href}">Spatial Media</a>\n'
        f'    <button class="nav-toggle" type="button" aria-expanded="false" '
        f'aria-controls="global-nav-links" aria-label="Open menu">\n'
        f'      <span class="nav-toggle-bar" aria-hidden="true"></span>\n'
        f'      <span class="nav-toggle-bar" aria-hidden="true"></span>\n'
        f"    </button>\n"
        f'    <div class="nav-links" id="global-nav-links">{links_html}</div>\n'
        f"  </div>\n"
        f"</nav>"
    )


def render_favicon_links(current_page: str) -> str:
    icon_href = html.escape(relpath(current_page, "assets/favicon.svg"))
    return (
        f'<link rel="icon" href="{icon_href}" type="image/svg+xml" />\n'
        f'  <link rel="apple-touch-icon" href="{icon_href}" />'
    )


def render_doc_page(title: str, body_html: str, current_page: str) -> str:
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
  <script src="{html.escape(relpath(current_page, "assets/js/site.js"))}" defer></script>
</body>
</html>
"""


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


def build_site(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    shutil.copytree(WEB / "assets", output_dir / "assets")
    shutil.copy2(WEB / "index.html", output_dir / "index.html")
    if (WEB / "img").is_dir():
        shutil.copytree(WEB / "img", output_dir / "img")

    for src_rel, out_rel, title in DOC_PAGES:
        src = ROOT / src_rel
        body = md_to_html(src.read_text(encoding="utf-8"))
        page_html = render_doc_page(title, body, out_rel)
        out_path = output_dir / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(page_html, encoding="utf-8")

    print(f"Built site at {output_dir} ({len(DOC_PAGES)} pages)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build GitHub Pages site")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    build_site(args.output)


if __name__ == "__main__":
    main()

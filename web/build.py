"""Build the GitHub Pages site: markdown docs and static assets."""

from __future__ import annotations

import argparse
import html
import os
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
    ("web/guide/overview.md", "docs/index.html", "Overview"),
    ("web/guide/download.md", "docs/download.html", "Download"),
    ("web/guide/cli.md", "docs/cli.html", "CLI Guide"),
    ("web/guide/docker.md", "docs/docker.html", "Docker Web UI"),
    ("web/guide/audio.md", "docs/audio.html", "Spatial Audio Resources"),
    ("web/spec/audio.md", "docs/spec/audio.html", "Spatial Audio RFC"),
    ("web/spec/v1.md", "docs/spec/v1.html", "Spherical Video v1 RFC"),
    ("web/spec/v2.md", "docs/spec/v2.html", "Spherical Video v2 RFC"),
    ("web/spec/vr180.md", "docs/spec/vr180.html", "VR180 Format"),
]

# Sidebar navigation. Keep section labels short.
DOC_SIDEBAR: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "Getting started",
        [
            ("Overview", "docs/index.html"),
            ("Download", "docs/download.html"),
        ],
    ),
    (
        "Guides",
        [
            ("CLI", "docs/cli.html"),
            ("Docker", "docs/docker.html"),
            ("HRIR assets", "docs/audio.html"),
        ],
    ),
    (
        "Specifications",
        [
            ("Spherical video v1", "docs/spec/v1.html"),
            ("Spherical video v2", "docs/spec/v2.html"),
            ("VR180", "docs/spec/vr180.html"),
            ("Spatial audio", "docs/spec/audio.html"),
        ],
    ),
]

# Keep in sync with web/index.html.
GLOBAL_NAV_LINKS: list[tuple[str, str]] = [
    ("Demo", "index.html#demo"),
    ("Download", "docs/download.html"),
    ("Docs", "docs/index.html"),
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
    for text, href in GLOBAL_NAV_LINKS:
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


def render_docs_sidebar(current_page: str) -> str:
    sections: list[str] = []
    for label, links in DOC_SIDEBAR:
        items: list[str] = []
        for text, href in links:
            url = html.escape(nav_href(current_page, href))
            active = ' class="is-active"' if href == current_page else ""
            items.append(f'<li><a href="{url}"{active}>{html.escape(text)}</a></li>')
        sections.append(
            f'<div class="docs-sidebar-section">\n'
            f'  <p class="docs-sidebar-label">{html.escape(label)}</p>\n'
            f'  <ul class="docs-sidebar-links">{"".join(items)}</ul>\n'
            f"</div>"
        )
    return (
        f'<aside class="docs-sidebar" aria-label="Documentation">\n'
        f'  <button class="docs-sidebar-toggle" type="button" '
        f'aria-expanded="false" aria-controls="docs-sidebar-nav">'
        f"Browse docs</button>\n"
        f'  <nav class="docs-sidebar-nav" id="docs-sidebar-nav">\n'
        f'{"".join(sections)}\n'
        f"  </nav>\n"
        f"</aside>"
    )


def render_favicon_links(current_page: str) -> str:
    icon_href = html.escape(relpath(current_page, "assets/favicon.svg"))
    return (
        f'<link rel="icon" href="{icon_href}" type="image/svg+xml" />\n'
        f'  <link rel="apple-touch-icon" href="{icon_href}" />'
    )


def render_doc_page(title: str, body_html: str, current_page: str) -> str:
    global_nav = render_global_nav(current_page)
    sidebar = render_docs_sidebar(current_page)
    style_href = relpath(current_page, "assets/css/style.css")
    site_href = relpath(current_page, "assets/css/site.css")
    favicon = render_favicon_links(current_page)
    site_js = html.escape(relpath(current_page, "assets/js/site.js"))
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
  <div class="docs-layout">
    {sidebar}
    <div class="docs-main">
      <main class="doc-content">
        <h1>{html.escape(title)}</h1>
        {body_html}
      </main>
      <footer class="doc-footer">
        <p>Spatial Media metadata tools</p>
      </footer>
    </div>
  </div>
  <script src="{site_js}" defer></script>
</body>
</html>
"""


def prepare_markdown(text: str) -> str:
    """Drop the leading markdown H1; the page title is rendered from the body."""
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    text = "\n".join(lines)
    return re.sub(r"\]\(([^)]+\.md)\)", lambda m: f"]({m.group(1)[:-3]}.html)", text)


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
        body = md_to_html(prepare_markdown(src.read_text(encoding="utf-8")))
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

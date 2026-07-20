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
    ("Docs", "docs/index.html"),
    ("Download", "docs/download.html"),
    ("GitHub", "https://github.com/Nandan-18/spatial-media"),
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
        if href.startswith("https://"):
            url = href
        else:
            url = html.escape(nav_href(current_page, href))
        icon = ""
        if text == "Demo":
            icon = (
                '<span class="nav-icon" aria-hidden="true">'
                '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" '
                'stroke-linecap="round" stroke-linejoin="round">'
                '<path d="M3 4.5h10v7H3z"></path>'
                '<path d="M6.5 11.5L8 10l1.5 1.5"></path>'
                '<path d="M8 10V7"></path>'
                "</svg></span>"
            )
        elif text == "Docs":
            icon = (
                '<span class="nav-icon" aria-hidden="true">'
                '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" '
                'stroke-linecap="round" stroke-linejoin="round">'
                '<path d="M4 2.5h6.5L13 5v8.5H4z"></path>'
                '<path d="M10.5 2.5V5H13"></path>'
                '<path d="M6 8h5"></path>'
                '<path d="M6 10.5h5"></path>'
                "</svg></span>"
            )
        elif text == "Download":
            icon = (
                '<span class="nav-icon" aria-hidden="true">'
                '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" '
                'stroke-linecap="round" stroke-linejoin="round">'
                '<path d="M8 2.5v7"></path>'
                '<path d="M5.5 7.5L8 10l2.5-2.5"></path>'
                '<path d="M3 12.5h10"></path>'
                "</svg></span>"
            )
        elif text == "GitHub":
            icon = (
                '<span class="nav-icon" aria-hidden="true">'
                '<svg viewBox="0 0 16 16" fill="currentColor">'
                '<path d="M8 1.5a6.5 6.5 0 0 0-2.055 12.666c.325.06.444-.141.444-.313v-1.106c-1.807.393-2.188-.87-2.188-.87-.296-.75-.723-.95-.723-.95-.591-.404.044-.396.044-.396.654.046.998.672.998.672.581.996 1.524.708 1.895.541.059-.421.227-.708.412-.87-1.443-.164-2.96-.722-2.96-3.214 0-.71.253-1.291.669-1.746-.067-.165-.29-.828.064-1.726 0 0 .546-.175 1.789.667A6.205 6.205 0 0 1 8 4.642c.55.003 1.104.074 1.62.218 1.242-.842 1.787-.667 1.787-.667.355.898.132 1.561.065 1.726.417.455.668 1.036.668 1.746 0 2.498-1.52 3.048-2.968 3.209.233.2.441.592.441 1.193v1.769c0 .174.117.377.447.313A6.5 6.5 0 0 0 8 1.5Z"></path>'
                "</svg></span>"
            )
        items.append(f'<a href="{url}">{icon}<span>{html.escape(text)}</span></a>')
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
        f"{''.join(sections)}\n"
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
        <div class="footer-bottom">
          <p>Spatial Media &middot;
            <a href="{html.escape(nav_href(current_page, "index.html"))}">Home</a>
            <span aria-hidden="true">&middot;</span>
            <a href="{html.escape(nav_href(current_page, "docs/download.html"))}">Download</a>
            <span aria-hidden="true">&middot;</span>
            <a href="https://github.com/Nandan-18/spatial-media">GitHub</a>
          </p>
        </div>
      </footer>
    </div>
  </div>
  <script src="{site_js}" defer></script>
</body>
</html>
"""


def prepare_markdown(text: str, out_rel: str) -> str:
    """Normalize markdown links and image URLs for the rendered HTML path."""
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    text = "\n".join(lines)
    text = re.sub(r"\]\(([^)]+\.md)\)", lambda m: f"]({m.group(1)[:-3]}.html)", text)
    # web/spec uses ../img/; pages under docs/spec/ need ../../img/.
    img_prefix = Path(os.path.relpath("img", Path(out_rel).parent)).as_posix() + "/"
    if img_prefix != "../img/":
        text = text.replace("../img/", img_prefix)
    return text


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
        body = md_to_html(prepare_markdown(src.read_text(encoding="utf-8"), out_rel))
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

# SpatialTag branding design

**Date:** 2026-07-20  
**Status:** Approved (site pass complete; CLI/package rename approved 2026-07-20)  
**Scope:** Full public branding plus CLI, PyPI project name, release binaries, and Docker image names. GitHub repo URL and Python import path `spatial.*` stay unchanged for now.

## Problem

The project is a clear immersive-metadata toolkit, but the public face reads as a generic category (“Spatial Media”) with Apple-like tooling chrome. Developers, creators, and the GitHub Pages presence all need a sharper product identity without turning it into lifestyle VR marketing.

## Goals

- Product name that matches the job: tagging media as spatial.
- Distinctive visual system (type, color, mark) that still feels like a precision tool.
- Homepage, README, CLI, binaries, and Docker use SpatialTag / `spatialtag` naming.
- Docs keep technical RFC content; branding strings and command examples stay aligned.

## Non-goals

- Renaming the GitHub repo (`spatial-media`) or Pages base path (until done on GitHub).
- Renaming Python import packages (`spatial.*` stays).
- Rewriting RFC / spec body content.
- Dark-mode-first redesign, purple/glow aesthetics, or card-heavy marketing layouts.
- Keeping a `spatial-media` CLI alias (clean break).

## Identity

| Item | Decision |
|------|----------|
| Product name | **SpatialTag** |
| Wordmark | SpatialTag (single word, capital S and T) |
| Subtitle | inspect and inject immersive metadata |
| Hero tagline | Tag video and audio for immersive playback. |
| Positioning | SpatialTag inspects and injects the MP4/MOV metadata that platforms need for 360°, VR180, and spatial audio. |

### Naming rules

- **Public face:** SpatialTag on site nav, page titles, README title, meta description.
- **Repo / Pages URL:** remains `Nandan-18/spatial-media` until renamed on GitHub.
- **CLI:** `spatialtag` (replaces `spatial-media`).
- **PyPI / project name:** `spatialtag`.
- **Python imports:** keep `spatial.*`.
- **Release binaries:** `spatialtag-linux-x86_64`, `spatialtag-macos-arm64`.
- **Docker image:** `spatialtag-web`; container name `spatialtag`.

## Visual system

### Direction

“Precision tool for immersive media”: clean and technical, not VR-neon and not system-UI gray clone.

### Color

| Token | Value | Role |
|-------|-------|------|
| Background | `#F7F4EF` | Warm paper base |
| Ink | `#12141A` | Primary text |
| Accent | `#0B7A75` | Links, CTAs, mark field |
| Surface | `#EBE6DE` | Secondary panels |
| Code chrome | `#1A2332` | Prefers / mono surfaces |

Avoid purple gradients, glow orbs, and default bootstrap blue as the primary accent.

### Typography

| Role | Family |
|------|--------|
| Display / brand | Fraunces (semibold wordmark) |
| UI / body | Source Sans 3 |
| Code | IBM Plex Mono |

Load via a privacy-friendly approach already compatible with the static site (self-hosted or vetted CDN). Fallbacks only after the primary families.

### Mark / favicon

- Rounded square, teal field, cream glyph.
- Motif: horizon line (equirect / sphere cue) + small tag notch (metadata).
- Legible at 16px; replace `web/assets/favicon.svg`.

### Motion

Two to three intentional motions on the homepage hero only (e.g. tag “stamp” settle, light horizon parallax). No decorative particle noise.

## Surfaces

### Homepage

1. Nav: SpatialTag wordmark + Demo / Docs / Download / GitHub.
2. Hero (first viewport): brand → one headline → one supporting sentence → CTA group (“Try in browser”, “Download CLI”) → privacy note.
3. Below fold: three paths (Browser / CLI / Docs), then existing demo restyled to new tokens.
4. CLI examples use `spatialtag`.

### Docs / README

- Docs chrome uses SpatialTag.
- Quick start and guides use `spatialtag` commands.
- Clone paths may still say `spatial-media` (repo name).

### CLI / packaging

- `pyproject.toml` project name and console script: `spatialtag`.
- PyInstaller console binary name: `spatialtag`.
- Release workflow artifact names: `spatialtag-*`.
- Docker image: `spatialtag-web`.

## Success criteria

- First viewport brand test passes with SpatialTag as hero-level signal.
- Developers install/run via `spatialtag`.
- No remaining user-facing `spatial-media` CLI command (repo URLs may still say `spatial-media`).
- `import spatial` still works.

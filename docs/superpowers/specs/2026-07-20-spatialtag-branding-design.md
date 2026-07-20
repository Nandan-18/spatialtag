# SpatialTag branding design

**Date:** 2026-07-20  
**Status:** Approved for implementation planning  
**Scope:** Full public branding pass (name, visual system, homepage, docs chrome, README, favicon). No repo/package/module rename.

## Problem

The project is a clear immersive-metadata toolkit, but the public face reads as a generic category (“Spatial Media”) with Apple-like tooling chrome. Developers, creators, and the GitHub Pages presence all need a sharper product identity without turning it into lifestyle VR marketing.

## Goals

- Product name that matches the job: tagging media as spatial.
- Distinctive visual system (type, color, mark) that still feels like a precision tool.
- Homepage and README lead with brand + outcome; keep CLI/package identifiers stable.
- Docs keep technical RFC content; only chrome/branding updates.

## Non-goals

- Renaming the GitHub repo (`spatial-media`).
- Renaming the Python package, import paths, or CLI entry point (`spatial-media`).
- Rewriting RFC / spec body content.
- Dark-mode-first redesign, purple/glow aesthetics, or card-heavy marketing layouts.

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
- **Repo:** remains `spatial-media`.
- **CLI:** remains `spatial-media`; docs/README refer to “SpatialTag CLI (`spatial-media`)”.
- **Code:** Python modules and package metadata unchanged in this pass.

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
2. Hero (first viewport): brand → one headline → one supporting sentence → CTA group (“Try in browser”, “Download CLI”) → privacy note. Full-bleed illustration of the job (file gains a spatial tag), not abstract SV3D rings or inset cards.
3. Below fold: three paths (Browser / CLI / Docs), then existing demo restyled to new tokens.
4. First screen avoids RFC jargon; specs linked from Docs.

### Docs chrome

- Apply color/type tokens and SpatialTag header/sidebar branding.
- Spec and guide **content** stays as-is aside from branding string replacements in chrome/titles where needed.

### README

- H1: SpatialTag.
- Opening uses positioning + subtitle.
- Quick start keeps `spatial-media` commands; one clarifying line for CLI naming.

### Meta / assets

- Update `<title>` and meta description to SpatialTag.
- New favicon/mark as specified.

## Success criteria

- First viewport fails the “could this be another brand?” test after removing nav: SpatialTag is the hero-level signal.
- Creators understand the job in one sentence; developers still see working install/CLI commands.
- Visual language is consistent across homepage, docs chrome, favicon, and README.
- No breaking changes to CLI invocation or Python imports.

## Implementation notes (for planning)

Likely touchpoints: `web/index.html`, `web/assets/css/style.css`, `web/assets/css/site.css`, `web/assets/favicon.svg`, `web/build.py` (nav/logo strings), `README.md`, and any hardcoded “Spatial Media” strings in site chrome.

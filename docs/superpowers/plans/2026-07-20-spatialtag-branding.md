# SpatialTag Branding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebrand the public site and README to **SpatialTag** with the approved visual system, while keeping the `spatial-media` repo, CLI, and Python package names unchanged.

**Architecture:** Update design tokens and fonts in shared CSS; replace favicon; rewrite homepage hero markup/illustration; retarget docs chrome strings in `web/build.py`; align README and overview titles. Spec/RFC bodies stay technical and untouched except where they are page chrome.

**Tech Stack:** Static HTML/CSS, Python `web/build.py` site generator, SVG favicon, self-hosted woff2 fonts under `web/assets/fonts/`.

**Spec:** `docs/superpowers/specs/2026-07-20-spatialtag-branding-design.md`

## Global Constraints

- Product name in public chrome: **SpatialTag** (wordmark: capital S and T).
- Subtitle: `inspect and inject immersive metadata`.
- Hero tagline: `Tag video and audio for immersive playback.`
- CLI command remains `spatial-media`; never rename the entry point in this pass.
- Repo URL `Nandan-18/spatial-media` stays unchanged.
- Colors: bg `#F7F4EF`, ink `#12141A`, accent `#0B7A75`, surface `#EBE6DE`, code chrome `#1A2332`.
- Type: Fraunces (brand/display), Source Sans 3 (UI/body), IBM Plex Mono (code).
- No purple gradients, glow orbs, or dark-mode-first redesign.
- First viewport: brand → one headline → one sentence → CTA group → privacy note; brand must be hero-level.

---

## File map

| File | Responsibility |
|------|----------------|
| `web/assets/fonts/*` | Self-hosted Fraunces, Source Sans 3, IBM Plex Mono woff2 |
| `web/assets/css/style.css` | Design tokens, `@font-face`, hero, homepage components |
| `web/assets/css/site.css` | Docs chrome that depends on tokens |
| `web/assets/favicon.svg` | SpatialTag mark |
| `web/index.html` | Homepage copy, hero structure, illustration markup |
| `web/build.py` | Docs nav logo, titles, footer brand strings |
| `README.md` | Public repo identity |
| `web/guide/overview.md` | Docs landing H1 / intro branding |

---

### Task 1: Design tokens and self-hosted fonts

**Files:**
- Create: `web/assets/fonts/` (woff2 files + optional `README` not required)
- Modify: `web/assets/css/style.css` (`:root` and base `body` / `code` font stacks)
- Test: visual/build — `python3 web/build.py --output web/dist` and grep CSS variables

**Interfaces:**
- Produces: CSS variables `--bg`, `--text`, `--link`, `--link-hover`, `--bg-gray` (map surface), `--bg-code`, `--font`, `--font-display`, `--mono` used by later tasks

- [ ] **Step 1: Add font files**

Download OFL-licensed woff2 files into `web/assets/fonts/` (use fontsource or Google Fonts helper; pin specific files):

- `fraunces-latin-600.woff2` (or variable Fraunces if smaller overall)
- `source-sans-3-latin-400.woff2`
- `source-sans-3-latin-600.woff2`
- `ibm-plex-mono-latin-400.woff2`

If download tooling differs, any equivalent latin woff2 for those families is fine; keep filenames consistent with `@font-face` below.

- [ ] **Step 2: Add `@font-face` and update `:root` tokens**

At the top of `web/assets/css/style.css`, replace the `:root` block and add font faces:

```css
@font-face {
  font-family: "Fraunces";
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url("../fonts/fraunces-latin-600.woff2") format("woff2");
}

@font-face {
  font-family: "Source Sans 3";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("../fonts/source-sans-3-latin-400.woff2") format("woff2");
}

@font-face {
  font-family: "Source Sans 3";
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url("../fonts/source-sans-3-latin-600.woff2") format("woff2");
}

@font-face {
  font-family: "IBM Plex Mono";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("../fonts/ibm-plex-mono-latin-400.woff2") format("woff2");
}

:root {
  --bg: #f7f4ef;
  --bg-gray: #ebe6de;
  --bg-dark: #1a2332;
  --bg-code: #1a2332;
  --text: #12141a;
  --text-secondary: #4a4e57;
  --text-tertiary: #6b7080;
  --link: #0b7a75;
  --link-hover: #096660;
  --border: rgba(18, 20, 26, 0.1);
  --radius: 18px;
  --radius-sm: 12px;
  --max: 980px;
  --font: "Source Sans 3", "Segoe UI", Helvetica, Arial, sans-serif;
  --font-display: "Fraunces", Georgia, "Times New Roman", serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, Monaco, Consolas, monospace;
  --nav-h: 44px;
  --ease: cubic-bezier(0.25, 0.1, 0.25, 1);
}
```

Update `body { font-family: var(--font); ... background: var(--bg); color: var(--text); }`.

Update `.nav-logo` to use `font-family: var(--font-display); font-weight: 600;`.

- [ ] **Step 3: Verify tokens and build**

Run:

```bash
python3 -m ruff check web/build.py
rg -n "\-\-link:|--bg:|--font-display|Fraunces|Source Sans 3|IBM Plex Mono" web/assets/css/style.css
ls web/assets/fonts/
python3 web/build.py --output web/dist
test -f web/dist/assets/css/style.css
```

Expected: ruff clean (unchanged), CSS contains new tokens, fonts directory non-empty, build succeeds.

- [ ] **Step 4: Commit**

```bash
git add web/assets/css/style.css web/assets/fonts/
git commit -m "$(cat <<'EOF'
style(site): add SpatialTag design tokens and fonts

Swap Apple-system chrome for Fraunces / Source Sans 3 / IBM Plex Mono
and the approved teal-on-paper palette.
EOF
)"
```

---

### Task 2: Favicon mark

**Files:**
- Modify: `web/assets/favicon.svg`
- Test: open SVG; confirm build copies it to `web/dist/assets/favicon.svg`

**Interfaces:**
- Consumes: accent `#0B7A75`, cream `#F7F4EF`
- Produces: favicon used by `index.html` and `web/build.py` favicon links

- [ ] **Step 1: Replace favicon**

Overwrite `web/assets/favicon.svg` with a 32×32 mark: teal rounded rect, cream horizon + tag notch (legible at 16px):

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="7" fill="#0B7A75"/>
  <!-- horizon -->
  <path d="M6 18c4-6 8-6 12 0s8 6 12 0" fill="none" stroke="#F7F4EF" stroke-width="1.6" stroke-linecap="round"/>
  <!-- tag notch -->
  <path d="M20 8h4l2 2-2 2h-4V8z" fill="#F7F4EF"/>
  <circle cx="22.2" cy="10" r="0.9" fill="#0B7A75"/>
</svg>
```

Adjust paths slightly if needed for balance; keep colors exact.

- [ ] **Step 2: Verify**

```bash
python3 web/build.py --output web/dist
rg -n "0B7A75|F7F4EF" web/assets/favicon.svg web/dist/assets/favicon.svg
```

Expected: both files contain teal/cream; no old `#0066cc`.

- [ ] **Step 3: Commit**

```bash
git add web/assets/favicon.svg
git commit -m "$(cat <<'EOF'
style(site): refresh favicon for SpatialTag mark

Use teal field with horizon and tag notch so the icon matches the
product identity at small sizes.
EOF
)"
```

---

### Task 3: Docs chrome brand strings (`build.py`)

**Files:**
- Modify: `web/build.py` (nav logo, `<title>` suffix, footer name)
- Test: build output HTML under `web/dist/docs/`

**Interfaces:**
- Consumes: product name SpatialTag
- Produces: docs pages titled `… · SpatialTag` with SpatialTag nav/footer

- [ ] **Step 1: Update brand strings**

In `web/build.py`:

- `render_global_nav`: change `Spatial Media` logo text to `SpatialTag`
- `render_doc_page` `<title>`: `· Spatial Media` → `· SpatialTag`
- Footer: `Spatial Media &middot;` → `SpatialTag &middot;`

Keep GitHub URL `https://github.com/Nandan-18/spatial-media`.

- [ ] **Step 2: Verify**

```bash
python3 -m ruff check web/build.py
python3 -m ruff format --check web/build.py
python3 web/build.py --output web/dist
rg -n "SpatialTag|Spatial Media" web/dist/docs/index.html web/dist/docs/spec/vr180.html
```

Expected: ruff clean; built docs show `SpatialTag` in nav/title/footer; no `Spatial Media` in those chrome locations.

- [ ] **Step 3: Commit**

```bash
git add web/build.py
git commit -m "$(cat <<'EOF'
feat(site): brand docs chrome as SpatialTag

Update nav wordmark, document titles, and footer to the public product
name without changing repo or CLI identifiers.
EOF
)"
```

---

### Task 4: Homepage identity + hero illustration

**Files:**
- Modify: `web/index.html` (head meta/title, nav, hero markup)
- Modify: `web/assets/css/style.css` (hero brand + new illustration styles; remove or stop using `.sphere-demo` as primary visual)
- Test: build + HTML structure grep

**Interfaces:**
- Consumes: tokens and fonts from Task 1; favicon from Task 2
- Produces: first viewport matching brand → headline → sentence → CTAs → note

- [ ] **Step 1: Update head and nav strings**

In `web/index.html`:

```html
<meta
  name="description"
  content="SpatialTag inspects and injects 360°, VR180, and spatial audio metadata in MP4/MOV files. Browser demo, CLI, GUI, and Docker."
/>
<title>SpatialTag | Inspect and inject immersive metadata</title>
```

Nav logo text: `SpatialTag`.

Footer `.footer-name`: `SpatialTag`.

Replace remaining user-facing “Spatial Media” sentences on the homepage with “SpatialTag” (demo lead, how section, etc.). Do **not** change GitHub URLs or `spatial-media` CLI mentions.

- [ ] **Step 2: Restructure hero markup**

Replace the hero content/visual so the brand is the dominant signal:

```html
<header class="hero">
  <div class="hero-content">
    <p class="hero-brand">SpatialTag</p>
    <h1 class="hero-title">
      Tag video and audio<br />for immersive playback.
    </h1>
    <p class="hero-subtitle">
      SpatialTag inspects and injects the MP4/MOV metadata that platforms need
      for 360°, VR180, and spatial audio.
    </p>
    <div class="hero-cta">
      <a class="button button-primary" href="#demo">Try in browser</a>
      <a class="button button-secondary" href="docs/download.html">Download CLI</a>
    </div>
    <p class="hero-note">Runs locally. Your files never leave your device.</p>
  </div>
  <div class="hero-visual" aria-hidden="true">
    <div class="tag-demo">
      <div class="tag-demo-file">
        <span class="tag-demo-filename">clip.mp4</span>
        <span class="tag-demo-atom">moov</span>
      </div>
      <div class="tag-demo-stamp">SpatialTag</div>
      <div class="tag-demo-horizon"></div>
    </div>
  </div>
</header>
```

Remove the old `.sphere-demo` / SV3D / SA3D floating tags from the hero (below-fold format cards may keep technical labels).

- [ ] **Step 3: Style brand + illustration + motion**

In `web/assets/css/style.css`:

- `.hero-brand`: `font-family: var(--font-display); font-size: clamp(48px, 7vw, 72px); font-weight: 600; color: var(--text); margin: 0 0 12px; line-height: 1;`
- `.hero-title`: slightly smaller than brand (spec: brand overpowers headline), e.g. `clamp(28px, 3.5vw, 40px)`
- `.tag-demo`: relative frame ~320×240, surface background, full-bleed within hero visual column
- `.tag-demo-stamp`: accent pill that animates in (`@keyframes stamp-in` opacity + translateY, ~600ms, `--ease`)
- `.tag-demo-horizon`: subtle horizontal gradient line with gentle `transform` parallax animation (slow, low amplitude)
- Optional third motion: file atom label fade-in

Delete unused `.sphere-*` rules if nothing else references them.

- [ ] **Step 4: Verify**

```bash
python3 web/build.py --output web/dist
rg -n "hero-brand|SpatialTag|sphere-demo|SV3D" web/dist/index.html
rg -n "tag-demo|hero-brand|stamp-in" web/dist/assets/css/style.css
```

Expected: `hero-brand` present; hero has no `sphere-demo`; homepage chrome says SpatialTag; stamp animation present.

- [ ] **Step 5: Commit**

```bash
git add web/index.html web/assets/css/style.css
git commit -m "$(cat <<'EOF'
feat(site): rebrand homepage hero as SpatialTag

Lead with the product name, approved tagline, and a file-tagging
illustration instead of abstract SV3D rings.
EOF
)"
```

---

### Task 5: Below-fold homepage paths + token cleanup

**Files:**
- Modify: `web/index.html` (insert or retitle a three-path section if missing; keep demo)
- Modify: `web/assets/css/style.css` (ensure buttons, dark demo section, cards use new tokens; remove leftover `#0066cc` / Apple gray hardcodes where practical)

**Interfaces:**
- Consumes: SpatialTag naming from Task 4
- Produces: Browser / CLI / Docs path section before `#demo`

- [ ] **Step 1: Add three paths section**

Immediately before `#demo` (or after the “how” section), ensure a section exists:

```html
<section id="paths" class="section section-gray">
  <div class="section-inner">
    <h2 class="section-headline">Three ways to tag.</h2>
    <div class="compare-grid compare-grid-3">
      <article class="compare-card">
        <h3>Browser</h3>
        <p>Inspect and inject in the demo below. Best under ~2 GB.</p>
        <a href="#demo">Open demo</a>
      </article>
      <article class="compare-card">
        <h3>CLI</h3>
        <p>SpatialTag CLI (<code>spatial-media</code>) for local and in-place inject.</p>
        <a href="docs/download.html">Download</a>
      </article>
      <article class="compare-card">
        <h3>Docs</h3>
        <p>Guides and spherical / spatial-audio specifications.</p>
        <a href="docs/index.html">Read docs</a>
      </article>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Sweep hardcoded old blues**

```bash
rg -n "#0066cc|#0077ed|#fbfbfd|#f5f5f7" web/assets/css/style.css web/assets/css/site.css || true
```

Replace remaining primary brand hardcodes with `var(--link)` / `var(--bg)` / `var(--bg-gray)` where they are brand colors (not one-off diagram paints that need distinct hues).

- [ ] **Step 3: Verify build + contrast**

```bash
python3 web/build.py --output web/dist
rg -n "Three ways to tag|SpatialTag CLI" web/dist/index.html
rg -n "#0066cc" web/assets/css/style.css web/assets/css/site.css || true
```

Expected: paths section present; no `#0066cc` left in shared brand CSS (diagram-specific colors OK if documented in comment).

- [ ] **Step 4: Commit**

```bash
git add web/index.html web/assets/css/style.css web/assets/css/site.css
git commit -m "$(cat <<'EOF'
feat(site): add SpatialTag paths section and token cleanup

Surface Browser, CLI, and Docs entry points and finish migrating
shared CSS off the old blue/gray palette.
EOF
)"
```

---

### Task 6: README and docs overview branding

**Files:**
- Modify: `README.md`
- Modify: `web/guide/overview.md`
- Optional polish (same commit if small): `spatial/README.md` H1 only → SpatialTag with CLI note
- Test: `markdownlint` on touched markdown

**Interfaces:**
- Consumes: identity copy from the design spec
- Produces: repo README that leads with SpatialTag; overview docs landing aligned

- [ ] **Step 1: Rewrite README opening**

```markdown
# SpatialTag

**inspect and inject immersive metadata**

SpatialTag inspects and injects the MP4/MOV metadata that platforms need
for 360°, VR180, and spatial audio.

### What it does
```

Keep the existing bullet list (update “Works as a **CLI**” line to mention SpatialTag CLI). Keep quick start commands as `spatial-media`, with:

```markdown
SpatialTag CLI command: `spatial-media`
```

before the quick-start block. Keep repo clone URL unchanged.

- [ ] **Step 2: Update overview guide**

`web/guide/overview.md` H1 → `# SpatialTag` and first paragraph uses positioning line. Keep tool table and `spatial-media` command references.

- [ ] **Step 3: Lint and build**

```bash
markdownlint README.md web/guide/overview.md
python3 web/build.py --output web/dist
rg -n "SpatialTag|Spatial Media" web/dist/docs/index.html README.md
```

Expected: markdownlint clean; docs index shows SpatialTag; README H1 is SpatialTag.

- [ ] **Step 4: Commit**

```bash
git add README.md web/guide/overview.md spatial/README.md
git commit -m "$(cat <<'EOF'
docs: rebrand README and overview as SpatialTag

Lead public docs with the product name while keeping spatial-media as
the CLI and repository identifier.
EOF
)"
```

---

### Task 7: Final verification pass

**Files:**
- None required unless fixes surface
- Test: full site build + string audit

- [ ] **Step 1: Brand string audit**

```bash
python3 web/build.py --output web/dist
rg -n "Spatial Media" web/index.html web/build.py web/dist/index.html web/dist/docs README.md web/guide/overview.md || true
rg -n "SpatialTag" web/dist/index.html web/dist/docs/index.html README.md | head
```

Expected: no remaining **public chrome** “Spatial Media” in site/README/overview. Acceptable leftovers: design-spec history, commit messages, GUI/docker titles if deferred (see note).

- [ ] **Step 2: Smoke local preview**

```bash
cd web && pnpm build && pnpm preview
```

Manually check: first viewport brand test, favicon, docs nav, hero motion, CTAs.

- [ ] **Step 3: Optional follow-up (only if time; separate commit)**

Update user-visible window titles only (not CLI name):

- `spatial/gui.py` window title → `SpatialTag`
- `docker/templates/index.html` `<title>` / `<h1>` → `SpatialTag`

```bash
git add spatial/gui.py docker/templates/index.html
git commit -m "$(cat <<'EOF'
feat: align GUI and Docker UI titles with SpatialTag

Keep spatial-media as the CLI while matching desktop and Docker chrome
to the public product name.
EOF
)"
```

- [ ] **Step 4: Done checklist against spec**

- [ ] Brand is hero-level on homepage
- [ ] Tokens/fonts/favicon match spec
- [ ] Docs chrome says SpatialTag
- [ ] README leads with SpatialTag + CLI note
- [ ] `spatial-media` CLI still works / documented
- [ ] RFCs not rewritten

---

## Spec coverage (self-review)

| Spec item | Task |
|-----------|------|
| Name SpatialTag + subtitle/tagline/positioning | 4, 6 |
| Color tokens | 1, 5 |
| Fraunces / Source Sans 3 / IBM Plex Mono | 1 |
| Favicon mark | 2 |
| Hero structure + illustration + motion | 4 |
| Three paths + demo retained | 5 |
| Docs chrome | 3 |
| README | 6 |
| No repo/CLI/package rename | All tasks |
| Success criteria audit | 7 |

## Placeholder scan

No TBD/TODO steps; commands and target markup included.

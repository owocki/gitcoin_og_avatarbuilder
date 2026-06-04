# Gitcoin Avatar Builder — Standalone

A clean, dependency-free rebuild of Gitcoin's avatar builders. No login,
no backend, no Django — just static files reusing the original SVG art.

A header toggle switches between two builders:

- **Classic** — the OG layered builder. Each option is a separate SVG (Head, Eyes,
  Nose, Clothing, Accessories…) stacked as CSS layers; color is a filename swap.
- **Extended** — a port of Gitcoin's avatar3d / "Custom Avatar" system. Each *style*
  (Unisex, Female, Bufficorn, Comic, Joker, Orc, and ~95 more) is a single SVG whose
  top-level `<g id="category_part">` groups are toggled on/off, then skin / hair /
  background are recolored at render time via hex-delta "tone maps". Originally this
  ran server-side in Python (`app/avatar/views_3d.py`); here it's reproduced entirely
  in the browser (`extended.js`).

Source: [github.com/owocki/gitcoin_og_avatarbuilder](https://github.com/owocki/gitcoin_og_avatarbuilder)

## Run it locally

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

A local server is recommended (the PNG download needs same-origin asset access).
Opening `index.html` directly via `file://` mostly works, but the **Download PNG**
button may be blocked by the browser.

## Deploy to Vercel

This is a 100% static site — no build step. Vercel serves the files as-is.

**Option A — CLI**

```bash
npm i -g vercel   # if you don't have it
vercel            # preview deploy
vercel --prod     # production deploy
```

Accept the defaults when prompted (Framework Preset: **Other**, no build command,
output directory: project root).

**Option B — Git import**

1. Push this folder to a GitHub/GitLab/Bitbucket repo.
2. In the Vercel dashboard, **Add New → Project** and import the repo.
3. Framework Preset: **Other**. Leave Build Command empty and Output Directory blank.
4. **Deploy.**

Deployment behavior is configured in [`vercel.json`](vercel.json):

- `cleanUrls` — serves `index.html` at `/`.
- Long-lived immutable caching for everything under `/assets/`.
- `manifest.js` is revalidated on every request so catalog changes go live immediately.

`build_manifest.py` is excluded from deploys via [`.vercelignore`](.vercelignore)
(it's a dev-time tool, not needed at runtime).

## What's here

| File | Purpose |
|------|---------|
| `index.html` | UI + layout for both builders, plus the Classic builder's logic and the mode switch. |
| `manifest.js` | **Classic** catalog — every option, the layer it occupies, and its color palette. |
| `build_manifest.py` | Regenerates `manifest.js` by scanning `assets/avatar/`. Run after adding/removing classic art. |
| `assets/avatar/` | Classic Gitcoin SVG assets (from `app/assets/v2/images/avatar/`). |
| `extended.js` | **Extended** engine — fetches a style SVG, composes the selected groups, and recolors via tone maps. |
| `manifest3d.js` | **Extended** catalog — per style: its SVG, viewBox, part categories, tone palettes, and preview crops. |
| `build_manifest_3d.py` | Regenerates `manifest3d.js` by scanning `assets/avatar3d/`. Reads theme metadata from `theme_attrs.json`. |
| `theme_attrs.json` | Per-style metadata (tones, tone maps, preview viewboxes) extracted verbatim from `views_3d.py`. |
| `assets/avatar3d/` | Extended style SVGs (from `app/assets/v2/images/avatar3d/`). |
| `vercel.json` | Vercel static-hosting config (clean URLs + caching). |

The avatar can be deep-linked: `#classic` (default) or `#extended`.

## How it works

### Classic

The avatar is composed of stacked, absolutely-positioned layers — each a full-size
`background-image` (`contain` + `center`) at a fixed z-index. Because every SVG shares
the same coordinate space, the layers register perfectly.

- **Layer order** (back → front): Wallpaper, HatLong, HairLong, EarringBack, Clothing,
  Ears, Head, Makeup, HairShort, Earring, Beard, HatShort, Mustache, Mouth, Nose, Eyes,
  Glasses, Masks, Extras.
- **Color** is baked into filenames (`Head/0-AE7242.svg`). Changing a color simply swaps
  the file for the same shape with a different suffix:
  - Skin tone → Head, Ears
  - Hair color → Hair (front/back), Beard, Mustache
  - Clothing color → Clothing
  - Background → the preview's background color (not an asset)
- **Hair** splits into a back part (`HairLong`, behind clothing) and a front part (`HairShort`).
- **Accessories** map to layers by filename prefix and can be combined (one per layer).

### Extended

Each style is **one** SVG. Its top-level children carry ids like `head_x5F_1`,
`eyes_x5F_2`, `background_x5F_3`; the **category** is the prefix before the first `_`
(`head`, `eyes`, `background`). `extended.js` then:

1. **Fetches & parses** the style SVG once (cached), keeping each top-level group plus
   the shared `<style>` / `<defs>` / gradient nodes.
2. **Composes** a new SVG containing one chosen group per category (re-clicking a
   selection reverts that category to its first group), wrapped in the source viewBox.
   Per-part thumbnails reuse the same compose with a zoomed-in `previewViewbox` crop.
3. **Recolors** by string-replacing hex colors using **tone maps**: for a chosen tone,
   each base color is shifted by the same RGB delta (`delta = base_color − style_base`,
   then `+ chosen_tone`, clamped). This is a 1:1 port of `views_3d.py:get_avatar_tone_map`.

Styles with multi-option categories get part tabs; single-image styles render as fixed
presets (still recolorable where the style defines tones).

## Regenerating the catalogs

```bash
python3 build_manifest.py       # classic  -> manifest.js   (scans assets/avatar/)
python3 build_manifest_3d.py    # extended -> manifest3d.js (scans assets/avatar3d/)
```

Each scans its asset folder, verifies referenced files exist, and rewrites the manifest;
options/styles whose art is missing are skipped automatically.

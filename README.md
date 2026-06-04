# OG Gitcoin Avatar Builder — Standalone

A clean, dependency-free rebuild of the classic Gitcoin avatar builder. No login,
no backend, no Django — just static files reusing the original SVG art.

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
| `index.html` | The entire app — UI, layout, and logic in one file. |
| `manifest.js` | Auto-generated catalog of every option, the layer it occupies, and its color palette. |
| `build_manifest.py` | Regenerates `manifest.js` by scanning `assets/avatar/`. Run after adding/removing art. |
| `assets/avatar/` | The original Gitcoin SVG assets (copied from `app/assets/v2/images/avatar/`). |
| `vercel.json` | Vercel static-hosting config (clean URLs + caching). |

## How it works

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

## Regenerating the catalog

```bash
python3 build_manifest.py
```

This scans the asset folders, verifies each referenced file exists, and rewrites
`manifest.js`. Options whose art is missing are skipped automatically.

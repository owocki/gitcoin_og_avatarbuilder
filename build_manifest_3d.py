#!/usr/bin/env python3
"""
Generate manifest3d.js for the "Extended" Gitcoin Avatar Builder.

The extended builder is a port of Gitcoin's avatar3d / Custom Avatar system
(app/avatar/views_3d.py). Unlike the classic builder (one SVG file per option),
each *theme* here is a single SVG whose top-level <g id="category_part"> groups
are toggled on/off. Groups are bucketed into categories by the id prefix before
the first "_", and skin/hair/background are recolored at render time via
hex-delta "tone maps".

This script:
  1. reads theme metadata from theme_attrs.json (extracted verbatim from
     views_3d.py: preview_viewbox, skin/hair/background tones, tone_maps, path),
  2. scans each theme's SVG to enumerate the selectable group ids (grouped into
     ordered categories, mirroring avatar3dids_helper), and
  3. emits manifest3d.js (window.AVATAR_MANIFEST_3D).

Re-run after adding/removing avatar3d SVGs:  python3 build_manifest_3d.py
"""
import json
import os
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS_REL = os.path.join("assets", "avatar3d")
THEME_ATTRS = os.path.join(HERE, "theme_attrs.json")

# Themes worth surfacing first in the picker (rich part/tone customization).
# Everything else is appended after, in source order, as a one-click preset.
LEAD_THEMES = [
    'unisex', 'female', 'bufficorn', 'comic', 'flat', 'shiny', 'people',
    'joker', 'orc', 'barbarian', 'wookie', 'wolverine', 'cartoon_jedi',
    'square_bot', 'metacartel', 'jedi', 'protoss', 'terran', 'starbot',
    'bot', 'bender', 'curly', 'visible', 'walle', 'terminator',
]

# Human-friendly labels for keys that don't pretty-print cleanly.
LABEL_OVERRIDES = {
    'unisex': 'Unisex',
    'bot': 'Bot',
    'cartoon_jedi': 'Cartoon Jedi',
    'square_bot': 'Square Bot',
    'orc_gitcoin': 'Orc (Gitcoin)',
    'PixelBot': 'Pixel Bot',
    'iamthembot': 'I Am Them Bot',
    'qpix': 'Q Pix',
    'megaman2': 'Mega Man 2',
}


def pretty(key):
    if key in LABEL_OVERRIDES:
        return LABEL_OVERRIDES[key]
    cleaned = key.replace('greenpill_', 'GreenPill ').replace('_', ' ').replace('-', ' ')
    return ' '.join(w if (w.isupper() or any(c.isdigit() for c in w)) else w.capitalize()
                     for w in cleaned.split())


def parse_svg(path):
    """Return (viewBox, [ {key, ids:[...]} ]) for a theme SVG.

    Mirrors avatar3dids_helper: top-level child ids, excluding empty and 'base',
    grouped into ordered categories by the prefix before the first '_'.
    """
    tree = ET.parse(path)
    root = tree.getroot()
    view_box = root.attrib.get('viewBox', '')
    categories = []  # ordered list of {key, ids}
    index = {}       # category key -> entry
    for child in root:
        cid = child.attrib.get('id')
        if not cid or cid == 'base':
            continue
        cat = cid.split('_')[0]
        if not cat:
            continue
        if cat not in index:
            entry = {'key': cat, 'label': cat.capitalize(), 'ids': []}
            index[cat] = entry
            categories.append(entry)
        index[cat]['ids'].append(cid)
    return view_box, categories


def main():
    attrs = json.load(open(THEME_ATTRS))

    themes = {}
    referenced = []
    skipped = []
    for key, a in attrs.items():
        src = a.get('path', '')
        rel = src.replace('assets/v2/images/avatar3d/', ASSETS_REL + '/')
        abs_path = os.path.join(HERE, rel)
        if not os.path.isfile(abs_path):
            skipped.append(key)
            continue
        try:
            view_box, categories = parse_svg(abs_path)
        except ET.ParseError as e:
            skipped.append(f"{key} (parse error: {e})")
            continue

        referenced.append(rel)
        themes[key] = {
            'label': pretty(key),
            'path': rel,
            'viewBox': view_box,
            'categories': categories,
            'skinTones': a.get('skin_tones', []),
            'hairTones': a.get('hair_tones', []),
            'backgroundTones': a.get('background_tones', []),
            'toneMaps': a.get('tone_maps', []),
            'previewViewbox': a.get('preview_viewbox', {}),
        }

    def is_rich(k):
        t = themes[k]
        pickable = any(len(c['ids']) > 1 for c in t['categories'])
        toned = bool(t['skinTones'] or t['hairTones'] or t['backgroundTones'])
        return pickable or toned

    present = list(themes.keys())
    lead = [k for k in LEAD_THEMES if k in themes]
    rest_rich = [k for k in present if k not in lead and is_rich(k)]
    rest_static = [k for k in present if k not in lead and not is_rich(k)]
    theme_order = lead + rest_rich + rest_static

    manifest = {
        'assetBase': ASSETS_REL + '/',
        'themeOrder': theme_order,
        'leadCount': len(lead) + len(rest_rich),  # split point: customizable vs presets
        'themes': themes,
    }

    out_path = os.path.join(HERE, "manifest3d.js")
    with open(out_path, "w") as f:
        f.write("// AUTO-GENERATED by build_manifest_3d.py - do not edit by hand.\n")
        f.write("window.AVATAR_MANIFEST_3D = ")
        json.dump(manifest, f, indent=1)
        f.write(";\n")

    # Report + emit the set of referenced files (for pruning unused art).
    with open(os.path.join(HERE, ".manifest3d_referenced.txt"), "w") as f:
        f.write("\n".join(sorted(set(referenced))) + "\n")

    print(f"Wrote {out_path}")
    print(f"  {len(themes)} themes ({len(lead) + len(rest_rich)} customizable, "
          f"{len(rest_static)} presets)")
    if skipped:
        print(f"  skipped {len(skipped)} themes with no SVG on disk: "
              f"{', '.join(skipped[:8])}{' ...' if len(skipped) > 8 else ''}")


if __name__ == "__main__":
    main()

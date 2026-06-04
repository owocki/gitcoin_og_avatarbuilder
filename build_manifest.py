#!/usr/bin/env python3
"""
Generate manifest.js for the standalone Gitcoin Avatar Builder.

Scans assets/avatar/ and emits a JS file (window.AVATAR_MANIFEST) describing every
selectable option, the layer (z-index) each piece occupies, and which color palette
(if any) drives the SVG file that gets swapped in.

Re-run this if you add/remove SVG assets:  python3 build_manifest.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets", "avatar")

# --- palettes (from app/avatar/utils.py:get_avatar_context) -----------------
SKIN_TONES = ['FFFFF6', 'FEF7EB', 'F8D5C2', 'EEE3C1', 'D8BF82',
              'D2946B', 'AE7242', '88563B', '715031', '593D26']
HAIR_COLORS = ['000000', '4E3521', '8C3B28', 'B28E28', 'F4EA6E',
               'F0E6FF', '4D22D2', '8E2ABE', '3596EC', '0ECF7C']
CLOTHING_COLORS = ['CCCCCC', '684A23', 'FFCC3B', '4242F4', '43B9F9', 'F48914']
BACKGROUNDS = ['25E899', '9AB730', '00A55E', '3FCDFF', '3E00FF', '8E2ABE',
               'D0021B', 'F9006C', 'FFCE08', 'F8E71C', '15003E', 'FFFFFF']

DEFAULTS = {
    'SkinTone': 'AE7242',
    'HairColor': '000000',
    'ClothingColor': 'CCCCCC',
    'Background': '25E899',
}

# z-index order, back -> front (from app/assets/v2/js/avatar_builder.js)
LAYER_ORDER = [
    'Wallpaper',
    'HatLong', 'HairLong', 'EarringBack', 'Clothing',
    'Ears', 'Head', 'Makeup', 'HairShort', 'Earring', 'Beard', 'HatShort',
    'Mustache', 'Mouth', 'Nose', 'Eyes', 'Glasses', 'Masks', 'Extras',
]


def exists(rel):
    return os.path.isfile(os.path.join(ASSETS, rel))


def colored_path(folder, base, palette):
    """Path template with {c} placeholder + concrete default-color thumb."""
    color = DEFAULTS[palette]
    tmpl = f"{folder}/{base}-{{c}}.svg"
    thumb = f"{folder}/{base}-{color}.svg"
    return tmpl, thumb


def plain_path(folder, base):
    p = f"{folder}/{base}.svg"
    return p, p


# --- option builders --------------------------------------------------------
def colored_options(folder, bases, layer, palette):
    out = []
    for b in bases:
        tmpl, thumb = colored_path(folder, b, palette)
        if not exists(thumb):
            continue
        out.append({
            'id': str(b),
            'thumb': thumb,
            'layers': [{'layer': layer, 'path': tmpl, 'palette': palette}],
        })
    return out


def plain_options(folder, bases, layer):
    out = []
    for b in bases:
        p, thumb = plain_path(folder, b)
        if not exists(thumb):
            continue
        out.append({
            'id': str(b),
            'thumb': thumb,
            'layers': [{'layer': layer, 'path': p, 'palette': None}],
        })
    return out


def hair_options(pairs):
    """Each pair is [longPart, shortPart]; 'None' skips that slot."""
    slots = [('HairLong', 0), ('HairShort', 1)]
    out = []
    for pair in pairs:
        layers = []
        thumb = None
        for layer, idx in slots:
            part = pair[idx]
            if part == 'None':
                continue
            tmpl = f"HairStyle/{part}-{{c}}.svg"
            t = f"HairStyle/{part}-{DEFAULTS['HairColor']}.svg"
            if not exists(t):
                layers = []
                break
            layers.append({'layer': layer, 'path': tmpl, 'palette': 'HairColor'})
            thumb = t  # prefer front (later slot) as the swatch
        if not layers:
            continue
        out.append({'id': '+'.join(pair), 'thumb': thumb, 'layers': layers})
    return out


def facialhair_options(bases):
    out = []
    for b in bases:                       # e.g. 'Beard-0', 'Mustache-2'
        layer = b.split('-')[0]           # Beard | Mustache
        tmpl = f"FacialHair/{b}-{{c}}.svg"
        thumb = f"FacialHair/{b}-{DEFAULTS['HairColor']}.svg"
        if not exists(thumb):
            continue
        out.append({
            'id': b, 'thumb': thumb,
            'layers': [{'layer': layer, 'path': tmpl, 'palette': 'HairColor'}],
        })
    return out


def accessory_options(groups):
    """Each group is a list of one or more values like 'Glasses-0','EarringBack-2'."""
    out = []
    seen = set()
    for group in groups:
        key = '+'.join(group)
        if key in seen:
            continue
        layers = []
        thumb = None
        ok = True
        for val in group:
            layer = val.split('-')[0]     # Glasses | HatShort | Masks | Earring | ...
            path = f"Accessories/{val}.svg"
            if not exists(path):
                ok = False
                break
            layers.append({'layer': layer, 'path': path, 'palette': None})
            thumb = path
        if not ok or not layers:
            continue
        seen.add(key)
        out.append({'id': key, 'thumb': thumb, 'layers': layers})
    return out


# --- raw option lists (from utils.py) ---------------------------------------
HAIR_PAIRS = [
    ['None', '0'], ['None', '1'], ['None', '2'], ['None', '3'], ['None', '4'], ['5', 'None'],
    ['6-back', '6-front'], ['7-back', '7-front'], ['8-back', '8-front'], ['9-back', '9-front'],
    ['None', '10'], ['damos_hair-back', 'damos_hair-front'],
    ['long_swoosh-back', 'long_swoosh-front'], ['None', 'mohawk'], ['None', 'mohawk_inverted'],
    ['None', 'spikey'], ['None', 'mickey_hair'], ['None', 'modernhair_1'], ['None', 'modernhair_2'],
    ['modernhair_3-back', 'modernhair_3-front'], ['None', 'womenhair'], ['None', 'womanhair'],
    ['None', 'womanhair1'], ['None', 'womanhair2'], ['None', 'womanhair3'], ['None', 'womanhair4'],
    ['None', 'womanhair5'], ['None', 'man-hair'], ['None', 'girl_hairstyle1'],
    ['None', 'girl_hairstyle2'], ['None', 'girl_hairstyle3'], ['None', 'men_hairstyle1'],
    ['None', 'men_hairstyle2'],
]

ACCESSORY_GROUPS = [
    ['Glasses-0'], ['Glasses-1'], ['Glasses-2'], ['Glasses-3'], ['Glasses-4'],
    ['HatShort-backwardscap'], ['HatShort-redbow'], ['HatShort-yellowbow'], ['HatShort-ballcap'],
    ['HatShort-cowboy'], ['HatShort-superwoman-tiara'], ['HatShort-headdress'],
    ['HatShort-headphones'], ['HatShort-shortbeanie'], ['HatShort-tallbeanie'],
    ['HatShort-bunnyears'], ['HatShort-menorah'], ['HatShort-pilgrim'], ['HatShort-santahat'],
    ['HatShort-elfhat'], ['Earring-0'], ['Earring-1'], ['EarringBack-2', 'Earring-2'],
    ['Earring-3'], ['Earring-4'], ['Earring-5'], ['Masks-jack-o-lantern'], ['Masks-guy-fawkes'],
    ['Masks-bunny'], ['Masks-blackpanther'], ['Masks-jack-o-lantern-lighted'],
    ['Masks-wolverine_inspired'], ['Masks-captain_inspired'], ['Masks-alien'], ['Extras-Parrot'],
    ['Extras-wonderwoman_inspired'], ['Extras-santa_inspired'], ['Extras-reindeer'],
    ['Masks-gitcoinbot'], ['Extras-tattoo'], ['Masks-batman_inspired'], ['Masks-flash_inspired'],
    ['Masks-deadpool_inspired'], ['Masks-darth_inspired'], ['Masks-spiderman_inspired'],
    ['Glasses-5'], ['Glasses-geordi-visor'], ['Masks-funny_face'], ['Masks-viking'],
    ['Masks-construction_helmet'], ['Glasses-6'], ['HatShort-green'], ['Earring-6'],
    ['Extras-necklace'], ['Masks-carnival'], ['Masks-gas'], ['Masks-surgical'], ['Extras-monkey'],
    ['Masks-power'], ['Glasses-7'], ['Glasses-8'], ['HatShort-angel'], ['HatShort-devil'],
    ['Extras-necklace1'], ['Extras-necklace2'], ['Extras-necklace3'], ['Glasses-9'],
    ['Masks-clown'], ['HatShort-sleepy'], ['Earring-tribal'], ['Glasses-google'],
    ['Masks-marshmellow'], ['Masks-power1'], ['HatShort-elf'], ['Extras-necklaceb'],
    ['Masks-football'], ['HatShort-chefHat'], ['HatShort-captain'], ['HatShort-beanie'],
    ['Masks-egypt'], ['HatShort-nefertiti'], ['Masks-frankenstein'], ['Masks-diving'],
    ['HatShort-1'], ['HatShort-artist'], ['HatShort-pirate'], ['HatShort-grad'],
    ['HatShort-antlers'], ['Extras-sword'], ['Masks-pirate'], ['Extras-bird'], ['Extras-fire'],
    ['Masks-hockey'], ['Masks-snorkel'], ['Glasses-monocle'], ['HatShort-police'],
    ['HatShort-mexican'], ['HatShort-fez'],
]

WALLPAPERS = ['portal', 'space', 'bokeh', 'bokeh2', 'bokeh3', 'bokeh4', 'bokeh5', 'fire', 'trees',
              'trees2', 'trees3', 'flowers', 'city', 'city2', 'mountains', 'code', 'code2', 'code3',
              'bokeh6', 'abstract', 'anchors', 'circuit', 'jigsaw', 'lines', 'gears', 'clouds',
              'signal', 'polka_dots', 'polka_dots_black', 'squares', 'shapes', 'sunburst',
              'sunburst_pastel', 'rainbow']

MAKEUP = ['ziggy-stardust', 'bolt', 'star2', 'kiss', 'blush', 'eyeliner-green', 'eyeliner-teal',
          'eyeliner-pink', 'eyeliner-red', 'eyeliner-blue', 'star']


def dedupe(seq):
    out, seen = [], set()
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def main():
    categories = [
        {'key': 'Head', 'label': 'Head', 'optional': False, 'palette': 'SkinTone',
         'options': colored_options('Head', ['0', '1', '2', '3', '4'], 'Head', 'SkinTone')},
        {'key': 'Eyes', 'label': 'Eyes', 'optional': False, 'palette': None,
         'options': plain_options('Eyes', ['0', '1', '2', '3', '4', '5', '6'], 'Eyes')},
        {'key': 'Nose', 'label': 'Nose', 'optional': False, 'palette': None,
         'options': plain_options('Nose', ['0', '1', '2', '3', '4'], 'Nose')},
        {'key': 'Mouth', 'label': 'Mouth', 'optional': False, 'palette': None,
         'options': plain_options('Mouth', ['0', '1', '2', '3', '4', '5'], 'Mouth')},
        {'key': 'Ears', 'label': 'Ears', 'optional': False, 'palette': 'SkinTone',
         'options': colored_options('Ears', ['0', '1', '2', '3', 'Spock'], 'Ears', 'SkinTone')},
        {'key': 'Clothing', 'label': 'Clothing', 'optional': False, 'palette': 'ClothingColor',
         'options': colored_options('Clothing', [
             'cardigan', 'hoodie', 'knitsweater', 'plaid', 'shirt', 'shirtsweater', 'spacecadet',
             'suit', 'ethlogo', 'cloak', 'robe', 'pjs', 'elf_inspired', 'business_suit',
             'suspender', 'gitcoinpro', 'star_uniform', 'jersey', 'charlie', 'doctor', 'chinese',
             'blouse', 'polkadotblouse', 'coat', 'crochettop', 'space_suit', 'armour', 'pilot',
             'baseball', 'football', 'lifevest', 'firefighter', 'leatherjacket', 'martialarts',
             'raincoat', 'recycle', 'chef', 'sailor', 'turtleneck'], 'Clothing', 'ClothingColor')},
        {'key': 'HairStyle', 'label': 'Hair', 'optional': True, 'palette': 'HairColor',
         'options': hair_options(HAIR_PAIRS)},
        {'key': 'FacialHair', 'label': 'Facial Hair', 'optional': True, 'palette': 'HairColor',
         'options': facialhair_options([
             'Mustache-0', 'Mustache-1', 'Mustache-2', 'Mustache-3',
             'Beard-0', 'Beard-1', 'Beard-2', 'Beard-3'])},
        {'key': 'Makeup', 'label': 'Makeup', 'optional': True, 'palette': None,
         'options': plain_options('Makeup', MAKEUP, 'Makeup')},
        {'key': 'Accessories', 'label': 'Accessories', 'optional': True, 'palette': None,
         'multi': True, 'options': accessory_options(ACCESSORY_GROUPS)},
        {'key': 'Wallpaper', 'label': 'Wallpaper', 'optional': True, 'palette': None,
         'options': plain_options('Wallpaper', dedupe(WALLPAPERS), 'Wallpaper')},
    ]

    manifest = {
        'layerOrder': LAYER_ORDER,
        'palettes': {
            'SkinTone': SKIN_TONES,
            'HairColor': HAIR_COLORS,
            'ClothingColor': CLOTHING_COLORS,
            'Background': BACKGROUNDS,
        },
        'defaults': DEFAULTS,
        'categories': categories,
    }

    out_path = os.path.join(HERE, "manifest.js")
    with open(out_path, "w") as f:
        f.write("// AUTO-GENERATED by build_manifest.py — do not edit by hand.\n")
        f.write("window.AVATAR_MANIFEST = ")
        json.dump(manifest, f, indent=2)
        f.write(";\n")

    total = sum(len(c['options']) for c in categories)
    print(f"Wrote {out_path}")
    for c in categories:
        print(f"  {c['label']:<13} {len(c['options'])} options")
    print(f"  TOTAL {total} options across {len(categories)} categories")


if __name__ == "__main__":
    main()

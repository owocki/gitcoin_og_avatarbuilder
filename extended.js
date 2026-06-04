// Extended ("3D" / Custom) Gitcoin Avatar Builder.
//
// A dependency-free, client-side port of app/avatar/views_3d.py. Each *theme* is a
// single SVG whose top-level <g id="category_part"> groups are toggled on/off
// (grouped into categories by the id prefix before the first "_"), then skin / hair /
// background are recolored via hex-delta "tone maps". The original did this server-side
// in Python; here we do the identical compose-and-recolor in the browser.
//
// Rendering uses isolated `data:` SVG <img> elements (exactly like the original markup),
// which sidesteps gradient-id collisions between the many SVGs shown at once.

(function () {
  const M = window.AVATAR_MANIFEST_3D;
  const ASSET = M.assetBase;

  // Categories that are structural-only: always composited, never given a picker tab.
  const NON_PICKABLE = new Set(['frame', 'shadow', 'base']);

  // ---- color helpers (faithful ports of avatar/helpers.py) -------------------
  function hexToRgb(h) {
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  function rgbToHex(rgb) {
    return rgb.map(e => e.toString(16).padStart(2, '0')).join('');
  }
  function addRgb(a, b, clamp) {
    const out = [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
    if (clamp) for (let i = 0; i < 3; i++) out[i] = Math.max(0, Math.min(255, out[i]));
    return out;
  }
  function subRgb(a, b, clamp) {
    return addRgb(a, [-b[0], -b[1], -b[2]], clamp);
  }

  // Faithful port of views_3d.py:get_avatar_tone_map — returns {fromHex: toHex}.
  function getToneMap(tone, baseTone, theme) {
    let tones, base3d;
    // default branch (== 'skin')
    tones = ['D68876', 'BC8269', 'EEE3C1', 'FFCAA6', 'FFDBC2', 'D7723B', 'F4B990', 'CCB293', 'EDCEAE', 'F3DBC4'];
    base3d = 'F4B990';
    if (theme === 'female') base3d = 'FFCAA6';
    if (theme === 'comic') base3d = 'CCB293';

    if (tone === 'blonde_hair') { tones = ['F495A8', 'C6526D', 'F4C495']; base3d = 'CEA578'; }
    else if (tone === 'brown_hair') { tones = ['775246', '563532', 'A3766A']; base3d = '775246'; }
    else if (tone === 'brown_hair2') { tones = ['683B38', 'A56860', '7F4C42']; base3d = '683B38'; }
    else if (tone === 'dark_hair') { tones = ['4C3D44', '422D39', '6D5E66', '5E4F57', '9B8886', '896F6B', '84767E', '422C37']; base3d = '6D5E66'; }
    else if (tone === 'grey_hair') { tones = ['7C6761', '5E433D', 'AA8B87']; base3d = '7C6761'; }
    else if (tone === 'comic_hair') { tones = ['8C6239']; base3d = '8C6239'; }
    else if (tone === 'comic_background') { tones = ['9B9B9B']; base3d = '9B9B9B'; }
    else if (tone === 'flat_background') { tones = ['A6D9EA']; base3d = 'A6D9EA'; }
    else if (tone === 'flat_skin') { tones = ['EDCEAE', 'F3DBC4', 'E4B692', 'F1C9A5']; base3d = 'EDCEAE'; }
    else if (tone === 'metacartel_skin') { tones = ['ED495F']; }
    else if (tone === 'mage_skin') { tones = ['FFEDD9']; base3d = 'FFEDD9'; }
    else if (tone === 'barb_skin') { tones = ['F7D3C0']; base3d = 'F7D3C0'; }
    else if (tone === 'orc_skin') { tones = ['FFFF99']; base3d = 'FFFF99'; }
    else if (tone === 'terran_skin') { tones = ['FFD9B3']; base3d = 'FFD9B3'; }
    else if (tone === 'starbot_skin') { tones = ['FFFFFF']; base3d = 'FFFFFF'; }
    else if (tone === 'wookie_skin') { tones = ['AE7343']; base3d = 'AE7343'; }
    else if (tone === 'wolverine_skin') { tones = ['ECE3C1']; base3d = 'ECE3C1'; }
    else if (tone === 'orc_hair') { tones = ['010101']; base3d = '010101'; }
    else if (tone === 'squarebot_background') { tones = ['009345', '29B474']; base3d = '29B474'; }
    else if (tone === 'squarebot_skin') { tones = ['29B473']; base3d = '29B473'; }
    else if (tone === 'cj_hair') { tones = ['CCA352']; base3d = 'CCA352'; }
    else if (tone === 'cj_skin') { tones = ['D99678']; base3d = 'D99678'; }
    else if (tone === 'people_skin') { tones = ['FFE1B2', 'FFD7A3']; base3d = 'FFE1B2'; }
    else if (tone === 'people_hair') { tones = ['FFD248', '414042', 'A18369', 'E7ECED', '8C6239', '9B8579']; base3d = 'FFD248'; }
    else if (tone === 'shiny_skin') { tones = ['FFD3AE', '333333', 'E8B974', 'EDCEAE']; base3d = 'FFD3AE'; }
    else if (tone === 'shiny_hair') { tones = ['D68D51', 'F7774B', 'E8B974', 'F7B239', 'D3923C', '666666']; base3d = 'D68D51'; }
    else if (tone === 'flat_hair') {
      tones = ['682234', '581A2B', '10303F', '303030', '265A68', '583A2F', 'D1874A', 'E1A98C', 'D2987B', '3C2A20',
        'C64832', 'B2332D', 'A0756F', '8C6762', '471B18', '5A3017', 'EC9A1C', '545465', '494857', '231F20', '0F303F'];
      base3d = '8C6239';
    }

    const out = {};
    for (const key of tones) {
      const delta = subRgb(hexToRgb(key), hexToRgb(base3d), false);
      out[key] = rgbToHex(addRgb(delta, hexToRgb(baseTone), true));
    }
    return out;
  }

  // ---- state -----------------------------------------------------------------
  const state = {
    themeKey: M.themeOrder[0],
    selected: {},        // category key -> chosen id
    skinTone: '', hairTone: '', backgroundTone: '',
    activeCat: null,
  };
  const svgCache = {};   // themeKey -> { roots:[{id,cat,xml,el}], byCat:{}, doc }

  function theme() { return M.themes[state.themeKey]; }
  function pickableCats() {
    return theme().categories.filter(c => c.ids.length > 1 && !NON_PICKABLE.has(c.key));
  }

  // ---- SVG fetch + parse -----------------------------------------------------
  async function loadTheme(key) {
    if (svgCache[key]) return svgCache[key];
    const txt = await fetch(M.themes[key].path).then(r => r.text());
    const doc = new DOMParser().parseFromString(txt, 'image/svg+xml');
    const root = doc.documentElement;
    const ser = new XMLSerializer();
    const roots = [];
    // Always-included shared defs: <style>, <defs>, any element with "gradient" in its id.
    const shared = [];
    for (const el of Array.from(root.children)) {
      const tag = el.tagName.toLowerCase();
      const id = el.getAttribute('id') || '';
      if (tag === 'style' || tag === 'defs' || id.toLowerCase().includes('gradient')) {
        shared.push(ser.serializeToString(el));
      }
      if (id) {
        roots.push({ id, cat: id.split('_')[0], xml: ser.serializeToString(el) });
      }
    }
    const byId = {};
    roots.forEach(r => { byId[r.id] = r; });
    return (svgCache[key] = { roots, byId, shared });
  }

  // Compose an SVG string from a set of accepted ids (+ shared defs).
  function compose(cache, acceptIds, viewBox, sizeAttr) {
    const accept = new Set(acceptIds);
    const parts = cache.shared.slice();
    for (const r of cache.roots) {
      if (accept.has(r.id)) parts.push(r.xml);
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" ` +
      `viewBox="${viewBox}" ${sizeAttr} preserveAspectRatio="xMidYMid meet">${parts.join('')}</svg>`;
  }

  // themeKey/tones default to the live selection; pass them explicitly to render
  // a different theme (used for the style-dropdown thumbnails).
  function recolor(svg, t, themeKey, tones) {
    themeKey = themeKey || state.themeKey;
    tones = tones || { skin: state.skinTone, hair: state.hairTone, background: state.backgroundTone };
    for (const type of t.toneMaps) {
      let base = tones.skin;
      if (type.includes('hair')) base = tones.hair;
      if (type.includes('background')) base = tones.background;
      if (!base) continue;
      const map = getToneMap(type, base, themeKey);
      for (const [from, to] of Object.entries(map)) svg = svg.split(from).join(to);
    }
    return svg;
  }

  function dataUri(svg) {
    return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
  }

  // ---- style-dropdown thumbnails ---------------------------------------------
  // Each theme is its own (large) SVG, so thumbnails are rendered lazily — only
  // when their dropdown row scrolls into view — and cached. A thumbnail is the
  // theme's default avatar (first id of every category) at its default tones.
  const thumbCache = {};
  async function ensureThumb(key, img) {
    if (!img) return;
    if (thumbCache[key]) { img.src = thumbCache[key]; return; }
    try {
      await loadTheme(key);
      const t = M.themes[key];
      const ids = t.categories.map(c => c.ids[0]);
      const tones = {
        skin: (t.skinTones || [])[0] || '',
        hair: (t.hairTones || [])[0] || '',
        background: (t.backgroundTones || [])[0] || '',
      };
      const svg = recolor(
        compose(svgCache[key], ids, t.viewBox || '0 0 350 350', 'width="100%" height="100%"'),
        t, key, tones);
      thumbCache[key] = dataUri(svg);
      img.src = thumbCache[key];
    } catch (e) { /* leave the placeholder background on failure */ }
  }

  // The full avatar = one id from every category (selected, else first), recolored.
  function fullAvatarSvg(sizeAttr) {
    const cache = svgCache[state.themeKey];
    const t = theme();
    const ids = t.categories.map(c => state.selected[c.key] || c.ids[0]);
    return recolor(compose(cache, ids, t.viewBox || '0 0 350 350', sizeAttr || 'width="100%" height="100%"'), t);
  }

  // ---- rendering -------------------------------------------------------------
  function renderPreview() {
    const img = document.getElementById('ext-preview-img');
    img.src = dataUri(fullAvatarSvg());
  }

  let thumbObserver = null;
  function buildThemeMenu() {
    const menu = document.getElementById('ext-theme-menu');
    if (menu.dataset.built) return; // build once
    menu.dataset.built = '1';
    const byLabel = (a, b) => M.themes[a].label.localeCompare(M.themes[b].label);
    const customizable = M.themeOrder.slice(0, M.leadCount).sort(byLabel);
    const presets = M.themeOrder.slice(M.leadCount).sort(byLabel);
    // Render each thumbnail only as its row nears the viewport (root = the menu).
    thumbObserver = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        ensureThumb(e.target.dataset.key, e.target);
        thumbObserver.unobserve(e.target);
      }
    }, { root: menu, rootMargin: '150px' });
    const addGroup = (label, keys) => {
      const h = document.createElement('div');
      h.className = 'ext-optgroup'; h.textContent = label;
      menu.appendChild(h);
      for (const k of keys) {
        const opt = document.createElement('button');
        opt.type = 'button'; opt.className = 'ext-option'; opt.dataset.key = k;
        opt.setAttribute('role', 'option');
        const img = document.createElement('img');
        img.className = 'ext-thumb'; img.dataset.key = k; img.alt = '';
        const span = document.createElement('span');
        span.className = 'ext-option-label'; span.textContent = M.themes[k].label;
        opt.appendChild(img); opt.appendChild(span);
        opt.onclick = () => { closeMenu(); switchTheme(k); };
        menu.appendChild(opt);
        thumbObserver.observe(img);
      }
    };
    addGroup('Customizable', customizable);
    addGroup('Presets', presets);
  }

  // Reflect the current selection in the trigger + highlight the chosen option.
  function syncTrigger() {
    document.getElementById('ext-theme-current-label').textContent = M.themes[state.themeKey].label;
    ensureThumb(state.themeKey, document.getElementById('ext-theme-current-thumb'));
    document.querySelectorAll('#ext-theme-menu .ext-option').forEach(o =>
      o.classList.toggle('sel', o.dataset.key === state.themeKey));
  }

  function openMenu() {
    document.getElementById('ext-theme').classList.add('open');
    const sel = document.querySelector('#ext-theme-menu .ext-option.sel');
    if (sel) sel.scrollIntoView({ block: 'nearest' });
  }
  function closeMenu() { document.getElementById('ext-theme').classList.remove('open'); }

  function renderTones() {
    const t = theme();
    const rows = [
      ['skinTone', 'Skin', t.skinTones],
      ['hairTone', 'Hair', t.hairTones],
      ['backgroundTone', 'Background', t.backgroundTones],
    ];
    const wrap = document.getElementById('ext-tones');
    wrap.innerHTML = '';
    let any = false;
    for (const [key, label, list] of rows) {
      if (!list || !list.length) continue;
      any = true;
      const row = document.createElement('div'); row.className = 'colorrow';
      const name = document.createElement('div'); name.className = 'name'; name.textContent = label;
      const sws = document.createElement('div'); sws.className = 'swatches';
      for (const c of list) {
        const s = document.createElement('div');
        s.className = 'sw' + (state[key] === c ? ' sel' : '');
        s.style.background = '#' + c; s.title = '#' + c;
        s.onclick = () => { state[key] = c; renderTones(); renderPreview(); renderGrid(); };
        sws.appendChild(s);
      }
      row.appendChild(name); row.appendChild(sws); wrap.appendChild(row);
    }
    wrap.style.display = any ? '' : 'none';
  }

  function renderTabs() {
    const cats = pickableCats();
    const el = document.getElementById('ext-tabs');
    const hint = document.getElementById('ext-hint');
    el.innerHTML = '';
    if (!cats.length) {
      const t = theme();
      const toned = t.skinTones.length || t.hairTones.length || t.backgroundTones.length;
      el.innerHTML = '<span class="hint" style="margin:0">This avatar is a fixed preset' +
        (toned ? ' — adjust its tones on the left.' : '.') + '</span>';
      hint.style.display = 'none';
      return;
    }
    hint.style.display = '';
    if (!state.activeCat || !cats.find(c => c.key === state.activeCat)) state.activeCat = cats[0].key;
    for (const c of cats) {
      const tab = document.createElement('div');
      tab.className = 'tab' + (c.key === state.activeCat ? ' active' : '');
      tab.textContent = c.label;
      tab.onclick = () => { state.activeCat = c.key; renderTabs(); renderGrid(); };
      el.appendChild(tab);
    }
  }

  function renderGrid() {
    const grid = document.getElementById('ext-grid');
    grid.innerHTML = '';
    const cats = pickableCats();
    if (!cats.length) return;
    const cat = cats.find(c => c.key === state.activeCat) || cats[0];
    const cache = svgCache[state.themeKey];
    const t = theme();
    const vb = t.previewViewbox[cat.key] || '0 0 600 600';
    const selectedId = state.selected[cat.key] || cat.ids[0];
    for (const id of cat.ids) {
      const tile = document.createElement('div');
      tile.className = 'opt' + (id === selectedId ? ' sel' : '');
      const svg = recolor(compose(cache, [id], vb, 'width="100%" height="100%"'), t);
      const img = document.createElement('img');
      img.src = dataUri(svg);
      img.style.cssText = 'width:100%;height:100%;object-fit:contain;pointer-events:none';
      tile.appendChild(img);
      tile.onclick = () => {
        // toggle: re-clicking the active option falls back to the category default (ids[0])
        state.selected[cat.key] = (state.selected[cat.key] === id) ? null : id;
        renderGrid(); renderPreview();
      };
      grid.appendChild(tile);
    }
  }

  // ---- theme switching -------------------------------------------------------
  async function switchTheme(key) {
    state.themeKey = key;
    state.selected = {};
    state.activeCat = null;
    const t = theme();
    state.skinTone = (t.skinTones || [])[0] || '';
    state.hairTone = (t.hairTones || [])[0] || '';
    state.backgroundTone = (t.backgroundTones || [])[0] || '';
    syncTrigger();
    document.getElementById('ext-preview-img').src = '';
    await loadTheme(key);
    renderTones(); renderTabs(); renderGrid(); renderPreview();
  }

  // ---- randomize -------------------------------------------------------------
  function rand(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

  // Randomize parts & tones within the CURRENT style.
  function randomizeThis() {
    const t = theme();
    for (const c of pickableCats()) state.selected[c.key] = rand(c.ids);
    if (t.skinTones && t.skinTones.length) state.skinTone = rand(t.skinTones);
    if (t.hairTones && t.hairTones.length) state.hairTone = rand(t.hairTones);
    if (t.backgroundTones && t.backgroundTones.length) state.backgroundTone = rand(t.backgroundTones);
    renderTones(); renderTabs(); renderGrid(); renderPreview();
  }

  // Roll a brand-new random style, then randomize its parts & tones.
  async function randomizeAll() {
    const key = rand(M.themeOrder);
    if (key !== state.themeKey) await switchTheme(key);
    randomizeThis();
  }

  // ---- download PNG ----------------------------------------------------------
  function download() {
    const t = theme();
    const [, , vw, vh] = (t.viewBox || '0 0 350 350').split(/\s+/).map(Number);
    const MAX = 1024;
    const ar = (vw && vh) ? vw / vh : 1;
    let w = MAX, h = MAX;
    if (ar > 1) h = Math.round(MAX / ar); else w = Math.round(MAX * ar);
    const svg = fullAvatarSvg(`width="${w}" height="${h}"`);
    const img = new Image();
    img.onload = () => {
      const cv = document.createElement('canvas');
      cv.width = w; cv.height = h;
      cv.getContext('2d').drawImage(img, 0, 0, w, h);
      cv.toBlob(blob => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'gitcoin-avatar-' + state.themeKey + '.png';
        a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000);
      }, 'image/png');
    };
    img.onerror = () => alert(
      "Couldn't render the PNG. Run a local server instead:\n\n" +
      "  python3 -m http.server 8000\n\nthen visit http://localhost:8000");
    img.src = dataUri(svg);
  }

  // ---- boot ------------------------------------------------------------------
  let booted = false;
  async function boot() {
    if (booted) return;
    booted = true;
    buildThemeMenu();
    const trigger = document.getElementById('ext-theme-trigger');
    trigger.onclick = (e) => {
      e.stopPropagation();
      document.getElementById('ext-theme').classList.contains('open') ? closeMenu() : openMenu();
    };
    document.addEventListener('click', (e) => {
      if (!document.getElementById('ext-theme').contains(e.target)) closeMenu();
    });
    document.getElementById('ext-random-all').onclick = randomizeAll;
    document.getElementById('ext-random-this').onclick = randomizeThis;
    document.getElementById('ext-download').onclick = download;
    await switchTheme(state.themeKey);
  }

  window.ExtendedBuilder = { boot };
})();

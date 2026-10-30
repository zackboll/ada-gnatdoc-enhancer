/* Shared opt-in search. No HTML interpolation, remote services, or URL authority. */
window.gnatdocDocumentationSearch = (router) => {
  'use strict';
  const {approved, canonicalUrl, activate} = router;
  const input = document.getElementById('package-search');
  const status = document.getElementById('package-results');
  const list = document.getElementById('documentation-search-results');
  const authority = document.getElementById('documentation-search-authority');
  const clear = document.getElementById('package-clear');
  let records = null, failed = false;
  const limit = 50;
  const authorized = new Map();
  function render() {
    list.replaceChildren();
    const query = input.value.trim().toLowerCase();
    document.body.classList.toggle('documentation-search-active', Boolean(query && records && !failed));
    list.hidden = true;
    if (failed) { status.textContent = 'Documentation search unavailable. Browse the native navigation links below.'; return; }
    if (!records) { status.textContent = 'Loading documentation search…'; return; }
    if (!query) { status.textContent = 'Search public API names, signatures, and developer guides.'; return; }
    if (query.length > 256 || /[\x00-\x1f\x7f]/.test(query)) {
      status.textContent = 'Enter a search of at most 256 characters without control characters.'; return;
    }
    const words = query.split(/\s+/);
    const matches = records.filter(r => words.every(w => r.search.includes(w)));
    function score(r) {
      const name = r.name.toLowerCase(), short = name.slice(name.lastIndexOf('.') + 1);
      return name === query || short === query ? 0 : name.includes(query) ? 1 : 2;
    }
    // Stable tie order is the deterministic index order, not browser locale.
    matches.sort((a,b) => score(a) - score(b));
    status.textContent = matches.length ? `${matches.length} results${matches.length > limit ? `; showing first ${limit}. Refine your search.` : '.'}` : 'No matching documentation.';
    for (const r of matches.slice(0, limit)) {
      const item = document.createElement('li'), kind = document.createElement('span');
      kind.className = 'search-kind'; kind.textContent = r.kind;
      const link = document.createElement('a');
      link.textContent = r.label;
      const target = authorized.get(r.href);
      // Canonical outer-shell URLs also work with reload, fresh tabs and
      // modified clicks. Only already-authorized symbols get symbol routing.
      const href = target.state ? canonicalUrl(target.state).href : target.url.href;
      link.href = href;
      link.addEventListener('click', ev => {
        if (link.getAttribute('href') !== href) { ev.preventDefault(); return; }
        if (target.state && ev.button === 0 && !ev.ctrlKey && !ev.metaKey && !ev.shiftKey && !ev.altKey) {
          ev.preventDefault(); activate(target.state);
        }
      });
      const description = document.createElement('small');
      description.textContent = r.text.length > 350 ? r.text.slice(0,350) + '…' : r.text;
      item.append(kind, link, description); list.append(item);
    }
    list.hidden = !matches.length;
  }
  input.addEventListener('input', render);
  clear.addEventListener('click', () => { input.value = ''; render(); input.focus(); });
  input.addEventListener('keydown', ev => {
    if (ev.key === 'Escape') { input.value = ''; render(); }
    if (ev.key === 'ArrowDown' || ev.key === 'Enter') {
      const first = list.querySelector('a');
      if (first) { ev.preventDefault(); first.focus(); }
    }
  });
  list.addEventListener('keydown', ev => {
    const links = Array.from(list.querySelectorAll('a')), index = links.indexOf(document.activeElement);
    if (ev.key === 'Escape') { ev.preventDefault(); input.focus(); return; }
    if (index < 0 || !['ArrowDown','ArrowUp','Home','End'].includes(ev.key)) return;
    ev.preventDefault();
    const next = ev.key === 'Home' ? 0 : ev.key === 'End' ? links.length-1 :
      Math.max(0, Math.min(links.length-1, index + (ev.key === 'ArrowDown' ? 1 : -1)));
    links[next].focus();
  });
  (async () => {
    try {
      if (!authority || authority.dataset.schema !== '1' || !/^[a-f0-9]{64}$/.test(authority.dataset.sha256 || '')) throw Error('authority');
      for (const link of authority.querySelectorAll('a')) {
        const raw = link.getAttribute('href') || '', kind = link.dataset.searchKind, name = link.dataset.searchName;
        if (authorized.has(raw) || !name) throw Error('duplicate authority');
        const url = new URL(raw, location.href);
        if (url.origin !== location.origin) throw Error('origin');
        if (kind === 'guide') {
          if (!/^\.\.\/guides\/[a-z][a-z0-9-]*\.html$/.test(raw) || link.hasAttribute('target')) throw Error('guide');
          authorized.set(raw, {url, name, kind});
        } else {
          const state = approved.get(url.href);
          if (!['package','symbol','operation'].includes(kind) || !state ||
              !/^[a-f0-9]{64}\.html(?:#[a-f0-9]{64})?$/.test(raw) ||
              (kind === 'package' ? state.declaration || name !== state.item.name :
                !state.declaration || !name.startsWith(state.item.name + '.'))) throw Error('destination');
          authorized.set(raw, {state, name, kind});
        }
      }
      const response = await fetch('gnatdoc-search-index.json', {credentials:'same-origin', mode:'same-origin', redirect:'error'});
      if (!response.ok) throw Error('index');
      const buffer = await response.arrayBuffer();
      if (buffer.byteLength > 8*1024*1024) throw Error('size');
      const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', buffer)), b => b.toString(16).padStart(2,'0')).join('');
      if (hash !== authority.dataset.sha256) throw Error('digest');
      const data = JSON.parse(new TextDecoder('utf-8', {fatal:true}).decode(buffer));
      if (Object.keys(data).sort().join() !== 'records,schema_version' || data.schema_version !== 1 ||
          !Array.isArray(data.records) || data.records.length > 20000 ||
          data.records.length !== authorized.size || String(data.records.length) !== authority.dataset.count) throw Error('schema');
      const seen = new Set();
      records = data.records.map(r => {
        if (!r || Object.keys(r).sort().join() !== 'href,kind,label,name,text' ||
            !Object.values(r).every(v => typeof v === 'string') || r.text.length > 64000 ||
            seen.has(r.href)) throw Error('record');
        const target = authorized.get(r.href);
        if (!target || target.name !== r.name || target.kind !== r.kind) throw Error('unauthorized record');
        seen.add(r.href);
        return {...r, search:(r.name + ' ' + r.text).toLowerCase()};
      });
    } catch (_) { records = null; failed = true; }
    render();
  })();
  return render;
};
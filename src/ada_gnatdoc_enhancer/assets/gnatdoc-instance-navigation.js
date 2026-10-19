/* Explicitly opted-in explanatory summaries remain separate from native symbols. */
(() => {
  'use strict';
  const controls = document.getElementById('package-navigation');
  const sidebar = document.querySelector('.side-navigation');
  const frame = document.querySelector('iframe[name="document-content"]');
  const heading = document.getElementById('compilation-units');
  if (!controls || !sidebar || !frame || !heading || controls.dataset.ready) return;
  const nativeList = heading.nextElementSibling;
  if (!nativeList || nativeList.tagName !== 'UL') return;
  const navLinks = Array.from(nativeList.querySelectorAll('a'));
  const byName = new Map(), byPath = new Map();
  for (const link of navLinks) {
    const target = link.getAttribute('href');
    if (!/^[a-f0-9]{64}\.html$/.test(target || '') || link.target !== frame.name) return;
    const url = new URL(target, location.href);
    if (url.origin !== location.origin || byName.has(link.textContent.toLowerCase()) || byPath.has(url.pathname)) return;
    const item = {link, url, name:link.textContent};
    byName.set(item.name.toLowerCase(), item);
    byPath.set(url.pathname, item);
  }
  if (byName.size !== navLinks.length || !navLinks.length) return;
  const search = document.getElementById('package-search');
  const results = document.getElementById('package-results');
  let current = null;
  const allLinks = Array.from(sidebar.querySelectorAll('a[target="document-content"]'));
  const filtered = allLinks.filter(link => link.closest('li') || link.closest('.operation-group'));
  // Only generated native links confer authority. Neither query state nor an
  // iframe URL can manufacture a destination, even with a plausible hash.
  const approved = new Map(), linkStates = new Map();
  for (const link of allLinks) {
    const href = link.getAttribute('href');
    if (!/^[a-f0-9]{64}\.html(?:#[a-f0-9]{64})?$/.test(href || '')) continue;
    const url = new URL(href, location.href), item = byPath.get(url.pathname);
    if (!item || url.origin !== location.origin) continue;
    const state = {item, url, declaration:url.hash.slice(1), link};
    if (!approved.has(url.href)) approved.set(url.href, state);
    linkStates.set(link, state);
  }
  const metadata = document.getElementById('type-navigation');
  const fallback = metadata && byName.get((metadata.dataset.defaultPackage || '').toLowerCase());
  if (!fallback) return;
  const symbols = new Map();
  for (const link of metadata.querySelectorAll('a')) {
    const name = link.dataset.symbol || '', href = link.getAttribute('href') || '';
    if (!/^[A-Za-z](?:[A-Za-z0-9]|_[A-Za-z0-9])*(?:\.[A-Za-z](?:[A-Za-z0-9]|_[A-Za-z0-9])*)+$/.test(name) ||
        !/^[a-f0-9]{64}\.html#[a-f0-9]{64}$/.test(href)) return;
    const item = byName.get(name.slice(0,name.lastIndexOf('.')).toLowerCase());
    const url = new URL(href,location.href), key = name.toLowerCase();
    if (!item || item.url.pathname!==url.pathname || url.origin!==location.origin || symbols.has(key)) return;
    const previous = approved.get(url.href);
    if (previous && previous.symbol) return;
    const state = {item, url, declaration:url.hash.slice(1), link:previous?.link || item.link, symbol:name};
    symbols.set(key,state);approved.set(url.href,state);
    // Tagged sidebar links and hidden metadata must share one logical state.
    for (const [nativeLink, target] of linkStates)
      if (target.url.href===url.href) linkStates.set(nativeLink,state);
  }
  if (!symbols.size) return;
  const explanations = document.getElementById('instance-reference-navigation');
  if (!explanations) return;
  const summaries = new Map();
  for (const link of explanations.querySelectorAll('a')) {
    const name = link.dataset.instance || '', href = link.getAttribute('href') || '';
    const owner = name.slice(0,name.lastIndexOf('.')), item = byName.get(owner);
    if (!item || !/^[a-z][a-z0-9_.]*\.(?:vector|matrix)$/.test(name) ||
        !/^[a-f0-9]{64}\.html#instance-members-summary$/.test(href)) return;
    const url = new URL(href,location.href);
    if (url.pathname!==item.url.pathname || summaries.has(item.name) || approved.has(url.href)) return;
    const state = {item,url,link:item.link,declaration:'',summary:'instance-members-summary'};
    summaries.set(item.name,state);approved.set(url.href,state);
  }
  if (!summaries.size) return;
  const defaultState = approved.get(fallback.url.href);
  let pending = null;
  const superseded = new Set();
  const observedDocuments = new WeakSet();
  function select(state) {
    for (const l of allLinks) l.removeAttribute('aria-current');
    state.item.link.setAttribute('aria-current','page');
    if (state.declaration && state.link!==state.item.link) state.link.setAttribute('aria-current','location');
    current=state;
  }
  function canonicalUrl(state) {
    const u = new URL(location.href);
    u.searchParams.set('package',state.item.name);
    u.searchParams.delete('declaration');
    u.searchParams.delete('symbol');
    u.hash='';
    if (state.summary) u.hash=state.summary;
    if (state.symbol) u.searchParams.set('symbol',state.symbol);
    else if (state.declaration) u.searchParams.set('declaration',state.declaration);
    return u;
  }
  function targetFromUrl() {
    const query = new URL(location.href).searchParams;
    const packages = query.getAll('package'), declarations = query.getAll('declaration');
    const names = query.getAll('symbol');
    // Ada identities need no escapes. Reject encoded aliases, duplicate keys,
    // unknown parameters and symbol/declaration mixtures rather than decoding
    // them into a second interpretation of the public contract.
    if (/[%+\\]/.test(location.search) ||
        Array.from(query.keys()).some(k => !['package','symbol','declaration'].includes(k)) ||
        packages.length>1 || declarations.length>1 || names.length>1 ||
        (names.length && declarations.length)) return defaultState;
    if (names.length) {
      const state = symbols.get(names[0].toLowerCase());
      return state && (!packages.length || packages[0].toLowerCase()===state.item.name.toLowerCase()) ? state : defaultState;
    }
    const item = packages.length===1 && byName.get(packages[0].toLowerCase());
    if (!item) return defaultState;
    const packageState = approved.get(item.url.href);
    if (!declarations.length && location.hash==='#instance-members-summary')
      return summaries.get(item.name) || packageState;
    if (!declarations.length) return packageState;
    if (declarations.length!==1 || !/^[a-f0-9]{64}$/.test(declarations[0])) return packageState;
    return approved.get(item.url.href+'#'+declarations[0]) || packageState;
  }
  function frameUrl() {
    try { return frame.contentWindow.location.href; }
    catch (_) { return null; }
  }
  function reveal(state) {
    const fragment=state.declaration || state.summary;
    if (!fragment) return;
    requestAnimationFrame(() => {
      if (current!==state || pending || frameUrl()!==state.url.href) return;
      try {
        if (frame.contentDocument.readyState==='complete')
          frame.contentDocument.getElementById(fragment)?.scrollIntoView({block:'start'});
      } catch (_) { /* A foreign frame cannot acquire symbol authority. */ }
    });
  }
  function navigate(state, retry=false) {
    if (!retry && pending && pending.url.href===state.url.href) return;
    if (pending && pending.url.href!==state.url.href) superseded.add(pending.url.href);
    superseded.delete(state.url.href);
    pending=state;
    if (frameUrl()===state.url.href) { pending=null; reveal(state); return; }
    // The outer entry owns history. assign()/src would add joint iframe entries.
    frame.contentWindow.location.replace(state.url.href);
  }
  function activate(state) {
    if (!current || current.url.href!==state.url.href) {
      history.pushState({package:state.item.name, declaration:state.declaration, symbol:state.symbol},'',canonicalUrl(state));
    }
    select(state);navigate(state);
  }
  function restore() {
    const state=targetFromUrl();
    const canonical=canonicalUrl(state);
    if (canonical.href!==location.href) history.replaceState(null,'',canonical);
    select(state);navigate(state);
  }
  function click(ev, inner=false) {
    const link=ev.target.closest('a');
    if (!link || link.hasAttribute('download') || (inner ? link.target && link.target!=='_self' && link.target!==frame.name : link.target!==frame.name) ||
        ev.button!==0 || ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.altKey) return;
    let state;
    if (inner) {
      // Native document navigation is enhanced only for the exact same allowlist.
      const raw=link.getAttribute('href') || '';
      if (/^(?:[a-f0-9]{64}\.html(?:#(?:[a-f0-9]{64}|instance-members-summary))?|#[a-f0-9]{64})$/.test(raw))
        state=approved.get(new URL(raw,frameUrl()).href);
      if (!state) return; // Ordinary external/untracked native links stay native.
    } else {
      state=linkStates.get(link);
      // Do not follow a mutated or injected sidebar destination.
      if (!state || link.getAttribute('href')!==state.url.href.slice(state.url.href.lastIndexOf('/')+1)) {
        ev.preventDefault();return;
      }
    }
    ev.preventDefault();activate(state);
  }
  frame.addEventListener('load', () => {
    // Loads are acknowledgements, never history writers. An older completion
    // cannot replace a newer selection or restored state.
    const loaded=frameUrl();
    if (pending && loaded!==pending.url.href) { navigate(pending,true); return; }
    if (!pending && superseded.has(loaded) && loaded!==current.url.href) {
      superseded.delete(loaded);navigate(current);return;
    }
    pending=null;
    try {
      const doc=frame.contentDocument;
      if (approved.has(frameUrl()) && doc && !observedDocuments.has(doc)) {
        doc.addEventListener('click',ev => click(ev,true));observedDocuments.add(doc);
        frame.contentWindow.addEventListener('hashchange',() => {
          if (pending && frameUrl()===pending.url.href) pending=null;
          if (frameUrl()===current.url.href) reveal(current);
        });
      }
    } catch (_) { /* Cross-origin navigation is never tracked. */ }
    if (loaded===current.url.href) reveal(current);
  });
  sidebar.addEventListener('click',ev => click(ev));
  function filter() {
    const q=search.value.toLowerCase();let shown=0;
    for (const link of filtered) {
      const match=link.textContent.toLowerCase().includes(q);
      link.parentElement.hidden=!match;
      if(match) shown++;
    }
    results.textContent=shown ? `${shown} results` : 'No matching documentation.';
  }
  search.addEventListener('input',filter);
  document.getElementById('package-clear').addEventListener('click',() => {
    search.value='';filter();search.focus();
  });
  window.addEventListener('popstate',restore);
  window.addEventListener('pageshow',restore);
  const initial=targetFromUrl(), canonical=canonicalUrl(initial);
  if (canonical.href!==location.href)
    history.replaceState({package:initial.item.name, declaration:initial.declaration},'',canonical);
  controls.dataset.ready='true';filter();restore();controls.hidden=false;
})();

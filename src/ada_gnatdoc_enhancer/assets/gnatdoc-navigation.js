/* Offline and optional: native anchor list works when JavaScript is disabled. */
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
  const first = byName.values().next().value;
  let current = null;
  const allLinks = Array.from(sidebar.querySelectorAll('a[target="document-content"]'));
  const filtered = allLinks.filter(link => link.closest('li') || link.closest('.operation-group'));
  function select(item) {
    if (!item) return;
    for (const l of allLinks) l.removeAttribute('aria-current');
    item.link.setAttribute('aria-current','page'); current=item;
  }
  function updateHistory(item, method) {
    const u = new URL(location.href);
    if (u.searchParams.getAll('package').length===1 && u.searchParams.get('package')===item.name) return;
    u.searchParams.set('package',item.name);
    history[method]({package:item.name},'',u);
  }
  function targetFromUrl() {
    const all = new URL(location.href).searchParams.getAll('package');
    return all.length===1 ? byName.get(all[0].toLowerCase()) || first : first;
  }
  function restore() {
    const item=targetFromUrl();select(item);updateHistory(item,'replaceState');
    try { if (frame.contentWindow.location.pathname!==item.url.pathname)
      frame.contentWindow.location.replace(item.url.href); }
    catch (_) { frame.src=item.url.href; }
  }
  frame.addEventListener('load', () => {
    try {
      const u=new URL(frame.contentWindow.location.href);
      const item=u.origin===location.origin && byPath.get(u.pathname);
      if (item && item!==current) {select(item);updateHistory(item,'pushState');}
    } catch (_) { /* Cross-origin navigation is never tracked. */ }
  });
  sidebar.addEventListener('click',ev => {
    const l=ev.target.closest('a');
    if (!l || l.target!==frame.name || ev.button!==0 || ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.altKey) return;
    const u=new URL(l.href), item=u.origin===location.origin && byPath.get(u.pathname);
    if (!item) return;
    ev.preventDefault();select(item);updateHistory(item,'pushState');
    frame.contentWindow.location.replace(u.href);
  });
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
  controls.dataset.ready='true';filter();restore();controls.hidden=false;
})();

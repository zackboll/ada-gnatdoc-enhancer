/* Qualified native GNATdoc 26 shell. No generated filename is constructed. */
(() => {
  "use strict";
  const controls = document.getElementById("package-navigation");
  const heading = document.getElementById("compilation-units");
  const frame = document.querySelector('iframe[name="document-content"]');
  if (!controls || !heading || !frame || controls.dataset.ready) return;
  const list = heading.nextElementSibling;
  if (!list || list.tagName !== "UL") return;
  const links = Array.from(list.querySelectorAll("a"));
  const byName = new Map(), byPath = new Map();
  for (const link of links) {
    const name = link.textContent;
    const url = new URL(link.getAttribute("href"), location.href);
    if (link.target !== frame.name || url.origin !== location.origin ||
        url.search || url.hash || !/^[a-f0-9]{64}\.html$/.test(link.getAttribute("href")) ||
        byName.has(name.toLowerCase()) || byPath.has(url.pathname)) return;
    const item = {name, url, link};
    byName.set(name.toLowerCase(), item);
    byPath.set(url.pathname, item);
  }
  const fallback = byName.get("opencv.core");
  if (links.length !== 195 || !fallback) return;
  const symbols = new Map(), destinations = new Map();
  for (const link of document.querySelectorAll('#type-navigation a')) {
    const name = link.dataset.symbol;
    const owner = name.slice(0, name.lastIndexOf('.'));
    const item = byName.get(owner.toLowerCase());
    const url = new URL(link.getAttribute('href'), location.href);
    const key = url.pathname + url.hash;
    if (!item || !/^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+$/.test(name) ||
        url.origin !== location.origin || url.pathname !== item.url.pathname ||
        url.search || !url.hash || symbols.has(name.toLowerCase()) ||
        destinations.has(key)) return;
    const symbol = {name, item, url};
    symbols.set(name.toLowerCase(), symbol);
    destinations.set(key, symbol);
  }
  if (!symbols.size) return;
  controls.dataset.ready = "true";
  const search = document.getElementById("package-search");
  const status = document.getElementById("package-results");
  function mark(item) {
    for (const link of links) link.removeAttribute("aria-current");
    item.link.setAttribute("aria-current", "page");
  }
  function outer(item, method, symbol = null) {
    const url = new URL(location.href);
    if (url.searchParams.getAll("package").length === 1 &&
        url.searchParams.get("package") === item.name &&
        url.searchParams.getAll("symbol").length === (symbol ? 1 : 0) &&
        (!symbol || url.searchParams.get("symbol") === symbol.name)) return;
    url.searchParams.set("package", item.name);
    url.searchParams.delete("symbol");
    if (symbol) url.searchParams.set("symbol", symbol.name);
    history[method]({package: item.name, symbol: symbol?.name}, "", url);
  }
  function requested() {
    const params = new URL(location.href).searchParams;
    const values = params.getAll("package");
    const names = params.getAll("symbol");
    if (names.length) {
      const symbol = names.length === 1 && symbols.get(names[0].toLowerCase());
      if (symbol && values.length <= 1 &&
          (!values.length || values[0].toLowerCase() === symbol.item.name.toLowerCase()))
        return {item: symbol.item, symbol};
      return {item: fallback};
    }
    return {item: values.length === 1 ? byName.get(values[0].toLowerCase()) || fallback : fallback};
  }
  function revealSymbol() {
    // A restored frame can already have the right fragment but the wrong
    // scroll offset. Run after the traversal's native scroll restoration,
    // and recheck the destination in case another navigation has started.
    requestAnimationFrame(() => {
      const {symbol} = requested();
      if (!symbol) return;
      try {
        if (frame.contentWindow.location.href !== symbol.url.href ||
            frame.contentDocument.readyState !== "complete") return;
        frame.contentDocument.getElementById(symbol.url.hash.slice(1))
          ?.scrollIntoView({block: "start"});
      } catch (_) { /* Unsupported foreign navigation is never selected. */ }
    });
  }
  function restore() {
    const {item, symbol} = requested();
    mark(item);
    outer(item, "replaceState", symbol);
    // Outer package/symbol history is authoritative; never add frame entries.
    const url = (symbol || item).url;
    if (frame.contentWindow.location.href !== url.href)
      frame.contentWindow.location.replace(url.href);
    else revealSymbol();
  }
  function navigate(url) {
    const item = url.origin === location.origin && byPath.get(url.pathname);
    if (!item || url.search) return false;
    const symbol = destinations.get(url.pathname + url.hash);
    mark(item);
    outer(item, "pushState", symbol);
    frame.contentWindow.location.replace(url.href);
    return true;
  }
  function click(event) {
    const link = event.target.closest("a");
    if (!link || event.button !== 0 || event.ctrlKey || event.metaKey ||
        event.shiftKey || event.altKey || link.hasAttribute('download')) return;
    if (link.ownerDocument === document ? link.target !== frame.name :
        link.target && link.target !== frame.name && link.target !== '_self') return;
    if (navigate(new URL(link.href))) event.preventDefault();
  }
  frame.addEventListener("load", () => {
    try {
      const url = new URL(frame.contentWindow.location.href);
      const item = url.origin === location.origin && byPath.get(url.pathname);
      if (!item) return;
      const symbol = destinations.get(url.pathname + url.hash);
      mark(item);
      outer(item, "pushState", symbol);
      frame.contentDocument.addEventListener('click', click);
      revealSymbol();
    } catch (_) { /* Unsupported foreign navigation is never selected. */ }
  });
  document.querySelector(".side-navigation").addEventListener("click", click);
  function filter() {
    const query = search.value.toLowerCase();
    let count = 0;
    for (const link of links) {
      const matches = link.textContent.toLowerCase().includes(query);
      link.parentElement.hidden = !matches;
      if (matches) count++;
    }
    status.textContent = count ? `${count} packages` : "No matching packages.";
  }
  search.addEventListener("input", filter);
  document.getElementById("package-clear").addEventListener("click", () => {
    search.value = "";
    filter();
    search.focus();
  });
  window.addEventListener("popstate", restore);
  window.addEventListener("pageshow", restore);
  filter();
  restore();
  controls.hidden = false;
})();